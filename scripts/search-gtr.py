#!/usr/bin/env python3
"""
Secure RAG - GTR Semantic Search

Search encrypted vectors using GTR embeddings (768-dim).
"""

import json
import urllib.request
import sys
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "secure_documents"


def encrypt_vector(vector):
    """Encrypt vector via Vault."""
    data = json.dumps({"vector": [float(v) for v in vector]}).encode()
    req = urllib.request.Request(
        f"{VAULT_ADDR}/v1/vector/encrypt/vector",
        data=data,
        headers={"X-Vault-Token": VAULT_TOKEN, "Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req).read())["data"]["ciphertext"]


def search_qdrant(vector, limit=5):
    """Search Qdrant with encrypted vector."""
    data = json.dumps({
        "vector": [float(v) for v in vector],
        "limit": limit,
        "with_payload": True
    }).encode()
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req).read())["result"]


def main():
    if len(sys.argv) < 2:
        print("""
Usage: python3 search-gtr.py "your query"

Examples:
  python3 scripts/search-gtr.py "What is a vector database?"
  python3 scripts/search-gtr.py "How do I secure secrets?"
  python3 scripts/search-gtr.py "Kubernetes deployment"
""")
        return

    query = " ".join(sys.argv[1:])

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   🔍 Secure RAG Search (GTR 768-dim)                                 ║
╚══════════════════════════════════════════════════════════════════════╝

   Query: "{query}"
""")

    # Load model
    print("📦 Loading GTR model...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('sentence-transformers/gtr-t5-base')

    # Embed query
    print("📝 Embedding query...")
    query_embedding = model.encode(query)

    # Encrypt query
    print("🔐 Encrypting query vector...")
    encrypted_query = encrypt_vector(query_embedding)

    # Search
    print("🔎 Searching encrypted vectors...")
    results = search_qdrant(encrypted_query)

    print()
    print("=" * 70)
    print(f"  📊 Results ({len(results)} found)")
    print("=" * 70)

    for i, result in enumerate(results, 1):
        score = result["score"]
        payload = result["payload"]
        title = payload.get("title", "Untitled")
        preview = payload.get("content_preview", "")[:150]

        # Relevance indicator
        if score > 0.5:
            relevance = "🟢 Highly Relevant"
        elif score > 0.3:
            relevance = "🟡 Relevant"
        elif score > 0.1:
            relevance = "🟠 Somewhat Relevant"
        else:
            relevance = "🔴 Low Relevance"

        print(f"""
  #{i} {title}
  ─────────────────────────────────────────────────────────────────
  Score: {score:.4f}  ({relevance})
  
  {preview}...
""")

    print("=" * 70)
    print("💡 Higher scores = more semantically similar")
    print()


if __name__ == "__main__":
    main()

