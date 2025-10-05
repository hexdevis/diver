# Code indexing functions

from config import CODE_DIR, get_embedder, get_collection
from utils import get_code_files, read_file, chunk_text
from typing import List


def _batch(iterable, size: int):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def index_codebase(batch_size: int = 32):
    """Index the codebase in batches. This batches embedding calls and collection.add
    calls which is much faster than adding one document at a time.

    Args:
        batch_size: number of chunks to encode per batch.
    """
    print("Indexing codebase...")
    files = get_code_files(CODE_DIR)
    embedder = get_embedder()
    collection = get_collection()

    chunks = []  # list of tuples (chunk_text, source, id)
    for fp in files:
        content = read_file(fp)
        for chunk in chunk_text(content):
            chunks.append((chunk, fp, f"{fp}-{hash(chunk)}"))

    total = 0
    for batch in _batch(chunks, batch_size):
        docs: List[str] = [c[0] for c in batch]
        metadatas = [{"source": c[1]} for c in batch]
        ids = [c[2] for c in batch]

        # encode in one call for better throughput
        embeddings = embedder.encode(docs, show_progress_bar=False)

        collection.add(documents=docs, embeddings=embeddings, metadatas=metadatas, ids=ids)
        total += len(docs)

    print(f"Indexed {total} chunks from {len(files)} files into vector DB.")
