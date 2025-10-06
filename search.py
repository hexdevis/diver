from config import TOP_K, get_embedder, get_collection, CODE_DIR
from utils import get_code_files, read_file
import re
import os

def _snippet_for_query(doc: str, query: str, window: int = 120, max_len: int = 400) -> str:
    """Return a short snippet from doc centered on the first occurrence of query (case-insensitive).
    If query is not found, return the first max_len characters.
    """
    if not doc:
        return ""
    q = query.lower()
    ldoc = doc.lower()
    idx = ldoc.find(q)
    if idx == -1:
        # fallback: trim to max_len
        s = doc.strip()
        return s if len(s) <= max_len else s[:max_len].rsplit("\n", 1)[0] + "..."

    start = max(0, idx - window)
    end = min(len(doc), idx + len(query) + window)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(doc) else ""
    return prefix + doc[start:end].strip() + suffix


def _parse_code_query(query: str):
    """Try to detect code-like queries and return (kind, name) or None.

    kind is one of: 'struct', 'class', 'def', 'function'
    name is the identifier following the keyword.
    """
    q = query.strip()
    # patterns like 'struct Node' or 'class Foo' or 'def bar'
    m = re.search(r"\b(struct|class)\s+(\w+)\b", q)
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"\bdef\s+(\w+)\s*\(", q)
    if m:
        return "def", m.group(1)
    # plain function name or identifier
    m = re.match(r"^(\w+)$", q)
    if m:
        return None
    return None


def _extract_block_c_style(text: str, start_idx: int) -> str:
    """Extract a brace-delimited block starting at or after start_idx (for C/C++/Java).
    This is a best-effort extractor that finds the first '{' after start_idx and returns
    until the matching '}' (handles simple nesting).
    """
    n = len(text)
    # find first '{' after start_idx
    i = text.find("{", start_idx)
    if i == -1:
        # no braces: return a few lines
        return '\n'.join(text[start_idx:start_idx+400].splitlines()[:40])
    depth = 0
    j = i
    while j < n:
        if text[j] == '{':
            depth += 1
        elif text[j] == '}':
            depth -= 1
            if depth == 0:
                return text[start_idx:j+1]
        j += 1
    # fallback: return from start_idx to some reasonable length
    return text[start_idx:start_idx+2000]


def _search_files_for_symbol(kind: str, name: str, ext: str = None):
    """Search source files for a symbol and return list of (path, snippet).

    ext may be like '.cpp' or 'cpp' or None.
    """
    # normalize extension filter
    exts = None
    if ext:
        if not ext.startswith('.'):
            ext = '.' + ext
        exts = [ext]

    # include common code extensions
    file_list = get_code_files(CODE_DIR, exts=(".py", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".java", ".js", ".ts", ".rs"))
    matches = []
    for fp in file_list:
        if exts and not fp.lower().endswith(tuple(exts)):
            continue
        content = read_file(fp)
        if not content:
            continue

        if kind in ("struct", "class"):
            # look for 'struct Name' or 'class Name'
            pat = re.compile(rf"\b{kind}\s+{re.escape(name)}\b")
            m = pat.search(content)
            if m:
                # find enclosing block
                start = max(0, m.start() - 80)
                block = _extract_block_c_style(content, start)
                matches.append((fp, block))
                continue

        if kind == "def":
            # python-style def
            pat = re.compile(rf"^\s*def\s+{re.escape(name)}\s*\(", re.M)
            m = pat.search(content)
            if m:
                # capture indented block following the def
                start_line = content.rfind('\n', 0, m.start()) + 1
                lines = content[start_line:].splitlines()
                block_lines = []
                indent = None
                for line in lines:
                    if not block_lines:
                        block_lines.append(line)
                        # determine indent of next lines
                        continue
                    # stop when we see a top-level line (no indent)
                    if re.match(r"^\S", line):
                        break
                    block_lines.append(line)
                block = "\n".join(block_lines)
                matches.append((fp, block))
                continue

    return matches


def search_code(query: str, ext: str = None):
    """Search the vector DB for relevant code snippets.

    If the query looks like a code symbol search (e.g. 'struct Node', 'class Foo', 'def bar')
    we attempt a fast filesystem scan to return the exact definition. Otherwise we fall back
    to embedding-based retrieval.

    Returns a list of tuples: (source_path, snippet_text, distance)
    """
    if not query:
        return []

    # allow queries like 'in .cpp struct Node' or 'in cpp struct Node'
    q = query.strip()
    # strip leading 'in' tokens
    if q.lower().startswith("in "):
        q = q.split(maxsplit=1)[1]

    parsed = _parse_code_query(q)
    if parsed:
        kind, name = parsed
        # try filesystem search first when a language ext is provided or when we can find the symbol
        fs_matches = _search_files_for_symbol(kind, name, ext=ext)
        if fs_matches:
            return [(p, s, None) for p, s in fs_matches]

    # fallback to embedding-based similarity search
    embedder = get_embedder()
    collection = get_collection()

    q_emb = embedder.encode([query])[0]

    results = collection.query(
        query_embeddings=[q_emb],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    docs_list = results.get("documents", [])
    metas_list = results.get("metadatas", [])
    dists_list = results.get("distances", [])

    if not docs_list:
        return []

    docs = docs_list[0]
    metas = metas_list[0] if metas_list else [{}] * len(docs)
    dists = dists_list[0] if dists_list else [None] * len(docs)

    out = []
    for m, d, dist in zip(metas, docs, dists):
        src = m.get("source") if isinstance(m, dict) else None
        snippet = _snippet_for_query(d, query)
        out.append((src, snippet, dist))

    # if extension filter is provided, only return results with matching source paths.
    if ext:
        if not ext.startswith('.'):
            ext = '.' + ext
        ext = ext.lower()
        out = [t for t in out if t[0] and t[0].lower().endswith(ext)]

    return out
