import chromadb
from sentence_transformers import SentenceTransformer
from typing import Optional

CODE_DIR = "./src"
MODEL_NAME = "BAAI/bge-m3"
OLLAMA_MODEL = "qwen3:8b"
TOP_K = 7 

# runtime and compiler configuration 
DEFAULTS = {
	"python": "python3",
	"node": "node",
	"ts_node": "ts-node",
	"npx": "npx",
	"tsc": "tsc",
	"gcc": "gcc",
	"gpp": "g++",
	"clang": "clang",
	"clangpp": "clang++",
	"rustc": "rustc",
	"build_dir": "build",
	"editor": "vim",
}

# lazily-initialized heavy resources to avoid long import-time delays.
_embedder: Optional[SentenceTransformer] = None
_chroma_client = None
_collection = None

def get_embedder() -> SentenceTransformer:
	"""Return a singleton SentenceTransformer instance. Loading is deferred until first use."""
	global _embedder
	if _embedder is None:
		print("Loading embedding model...")
		_embedder = SentenceTransformer(MODEL_NAME)
	return _embedder

def get_chroma_client():
	"""Return a singleton Chroma client."""
	global _chroma_client
	if _chroma_client is None:
		_chroma_client = chromadb.Client()
	return _chroma_client

def get_collection(name: str = "codebase"):
	"""Return or create the named collection in Chroma. Deferred until first use."""
	global _collection
	if _collection is None:
		client = get_chroma_client()
		_collection = client.get_or_create_collection(name)
	return _collection

