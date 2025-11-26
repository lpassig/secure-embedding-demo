#!/usr/bin/env python3
"""
Secure RAG - GTR Embedding Ingestion

Uses GTR embeddings (768-dim) which have a pre-trained vec2text inverter.
This allows proper demonstration of inversion attacks.
"""

import json
import urllib.request
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "secure_documents"

# Sample documents
DOCUMENTS = [
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "Introduction to Vector Databases",
        "content": "Vector databases are specialized database systems designed to store, index, and query high-dimensional vector embeddings. Unlike traditional databases that excel at exact matches, vector databases enable similarity search - finding items that are semantically similar to a query. This makes them essential for modern AI applications like semantic search, recommendation systems, and retrieval-augmented generation (RAG). Popular vector databases include Qdrant, Pinecone, Weaviate, and Milvus."
    },
    {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "title": "HashiCorp Vault Security Best Practices",
        "content": "HashiCorp Vault is a secrets management tool that provides a unified interface to any secret while providing tight access control and recording a detailed audit log. Key best practices include: Always use TLS in production. Enable audit logging to track all access. Use short-lived tokens and implement token renewal. Leverage Vault policies for fine-grained access control. Regularly rotate secrets and encryption keys."
    },
    {
        "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "title": "Building RAG Applications with n8n",
        "content": "n8n is a powerful workflow automation tool that can orchestrate complex RAG pipelines. A typical RAG workflow involves: Document ingestion - fetching and parsing documents from various sources. Chunking - splitting documents into smaller pieces. Embedding - converting text chunks into vector representations. Storage - saving vectors to a vector database. Retrieval - finding relevant chunks based on query similarity. Generation - using retrieved context to generate responses."
    },
    {
        "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
        "title": "Data Encryption at Rest and in Transit",
        "content": "Data encryption is fundamental to security. Encryption at rest protects stored data using algorithms like AES-256. Encryption in transit secures data moving between systems using TLS/SSL. For vector embeddings, additional considerations apply: vectors can leak information about the original data through similarity relationships. Distance-preserving encryption schemes allow similarity search on encrypted vectors while maintaining confidentiality."
    },
    {
        "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
        "title": "Kubernetes Deployment Patterns",
        "content": "Deploying applications on Kubernetes requires understanding several key patterns. The sidecar pattern adds helper containers to pods for logging, monitoring, or security. The ambassador pattern provides a proxy for external service access. For stateful applications like databases, use StatefulSets with persistent volumes. Implement health checks using liveness and readiness probes. Use Horizontal Pod Autoscaler for automatic scaling."
    }
]


def configure_vault(dimension=768):
    """Configure Vault for GTR embeddings."""
    data = json.dumps({
        "dimension": dimension,
        "scaling_factor": 10.0,
        "approximation_factor": 5.0
    }).encode()
    req = urllib.request.Request(
        f"{VAULT_ADDR}/v1/vector/config/rotate",
        data=data,
        headers={"X-Vault-Token": VAULT_TOKEN, "Content-Type": "application/json"}
    )
    urllib.request.urlopen(req)


def create_collection(dimension=768):
    """Create Qdrant collection."""
    # Delete if exists
    try:
        req = urllib.request.Request(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
            method="DELETE"
        )
        urllib.request.urlopen(req)
    except:
        pass
    
    # Create new
    data = json.dumps({
        "vectors": {"size": dimension, "distance": "Cosine"}
    }).encode()
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    urllib.request.urlopen(req)


def encrypt_vector(vector):
    """Encrypt vector via Vault."""
    data = json.dumps({"vector": [float(v) for v in vector]}).encode()
    req = urllib.request.Request(
        f"{VAULT_ADDR}/v1/vector/encrypt/vector",
        data=data,
        headers={"X-Vault-Token": VAULT_TOKEN, "Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req).read())["data"]["ciphertext"]


def store_in_qdrant(point_id, vector, payload):
    """Store vector in Qdrant."""
    vector = [float(v) for v in vector]
    data = json.dumps({
        "points": [{
            "id": point_id,
            "vector": vector,
            "payload": payload
        }]
    }).encode()
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points?wait=true",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    urllib.request.urlopen(req)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║   🔒 Secure RAG - GTR Embedding Ingestion (768-dim)                  ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    # Configure infrastructure
    print("📦 Configuring infrastructure for GTR embeddings (768-dim)...")
    configure_vault(768)
    print("   ✅ Vault configured")
    create_collection(768)
    print("   ✅ Qdrant collection 'secure_documents' created")
    print()

    # Load GTR model
    print("📦 Loading GTR embedding model...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('sentence-transformers/gtr-t5-base')
    print(f"   ✅ Model loaded (dimension: {model.get_sentence_embedding_dimension()})")
    print()

    # Process documents
    print("📝 Embedding and storing documents...")
    print()

    for i, doc in enumerate(DOCUMENTS, 1):
        print(f"   [{i}/{len(DOCUMENTS)}] {doc['title']}")
        
        # Generate embedding
        text = f"{doc['title']}\n\n{doc['content']}"
        embedding = model.encode(text)
        
        # Encrypt
        encrypted = encrypt_vector(embedding)
        
        # Store
        payload = {
            "document_id": doc["id"],
            "title": doc["title"],
            "source": "sample-docs",
            "content_preview": doc["content"][:300] + "..."
        }
        store_in_qdrant(doc["id"], encrypted, payload)
        
        print(f"       ✅ Embedded → Encrypted → Stored")

    # Verify
    print()
    print("🔍 Verifying...")
    req = urllib.request.Request(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/count")
    resp = urllib.request.urlopen(req)
    count = json.loads(resp.read())["result"]["count"]
    print(f"   Total points in Qdrant: {count}")

    print()
    print("✅ Done! Now you can:")
    print("   • Search: python3 scripts/search-gtr.py \"your query\"")
    print("   • Attack: python3 scripts/demo-real-vec2text.py")
    print()


if __name__ == "__main__":
    main()

