import os
import glob
import subprocess
from sentence_transformers import SentenceTransformer
import chromadb

# --- Configuration ---
CODE_DIR = "./src"         # path to your codebase
MODEL_NAME = "BAAI/bge-m3"          # local embedding model
OLLAMA_MODEL = "qwen3:8b"   # local Ollama model
TOP_K = 5                           # how many code snippets to retrieve

# --- Setup ---
print("Loading embedding model...")
embedder = SentenceTransformer(MODEL_NAME)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("codebase")

# --- Helper functions ---
def get_code_files(path, exts=(".py", ".js", ".cpp", ".java", ".ts")):
    files = []
    for ext in exts:
        files.extend(glob.glob(os.path.join(path, f"**/*{ext}"), recursive=True))
    return files

def read_file(fp):
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def chunk_text(text, size=512):
    lines = text.splitlines()
    for i in range(0, len(lines), size):
        yield "\n".join(lines[i:i+size])

# --- Step 1: Index codebase ---
def index_codebase():
    print("Indexing codebase...")
    files = get_code_files(CODE_DIR)
    for fp in files:
        content = read_file(fp)
        for chunk in chunk_text(content):
            emb = embedder.encode(chunk)
            collection.add(
                documents=[chunk],
                embeddings=[emb],
                metadatas=[{"source": fp}],
                ids=[f"{fp}-{hash(chunk)}"]
            )
    print(f"Indexed {len(files)} files into vector DB.")

# --- Step 2: Search relevant code ---
def search_code(query):
    q_emb = embedder.encode([query])
    results = collection.query(query_embeddings=q_emb, n_results=TOP_K)
    docs = results["documents"][0]
    meta = results["metadatas"][0]
    return [(m["source"], d) for m, d in zip(meta, docs)]

# --- Step 3: Ask model ---
def ask_model(query, context):
    prompt = f"""
You are a coding assistant with access to project context.

User question:
{query}

Relevant code context:
{context}

Answer concisely and clearly.
"""
    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL, prompt],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()

# --- Interactive loop ---
if __name__ == "__main__":
  try:
    if not collection.count():
        index_codebase()

    while True:
        q = input("\nAsk: ")
        if q.lower() in ["exit", "quit"]:
            print("Exiting...")
            break

        matches = search_code(q)
        context = "\n\n".join([f"File: {src}\n{chunk}" for src, chunk in matches])
        answer = ask_model(q, context)
        print("\nAnswer:\n", answer)

  except KeyboardInterrupt:
        print("\nExiting...")
