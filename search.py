# Search logic (search_code)

from config import TOP_K, get_embedder, get_collection


def search_code(query: str):
    """Search the vector DB for relevant code snippets.

    Returns a list of (source_path, document_text) tuples.
    """
    embedder = get_embedder()
    collection = get_collection()

    # SentenceTransformer.encode returns a vector (or list of vectors if given a list).
    q_emb = embedder.encode([query])[0]
    results = collection.query(query_embeddings=[q_emb], n_results=TOP_K)

    docs = results.get("documents", [])[0]
    meta = results.get("metadatas", [])[0]
    return [(m.get("source"), d) for m, d in zip(meta, docs)]
