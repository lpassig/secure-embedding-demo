#!/usr/bin/env python3
"""
Ingest demo data that works with vec2text inversion.

Stores the same documents in TWO collections:
- raw_documents: Unencrypted (VULNERABLE to vec2text)
- secure_documents: Encrypted (PROTECTED from vec2text)
"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import json
import urllib.request
import uuid

VAULT_ADDR = 'http://localhost:8200'
VAULT_TOKEN = 'root'
QDRANT_URL = 'http://localhost:6333'

# Demo documents that vec2text can invert
DOCUMENTS = [
    {"id": str(uuid.uuid4()), "text": "The cat sat on the mat."},
    {"id": str(uuid.uuid4()), "text": "Paris is the capital of France."},
    {"id": str(uuid.uuid4()), "text": "Machine learning uses neural networks."},
    {"id": str(uuid.uuid4()), "text": "The Eiffel Tower is located in Paris."},
    {"id": str(uuid.uuid4()), "text": "Water freezes at zero degrees Celsius."},
]


def configure_vault():
    data = json.dumps({'dimension': 768, 'scaling_factor': 10.0, 'approximation_factor': 5.0}).encode()
    req = urllib.request.Request(f'{VAULT_ADDR}/v1/vector/config/rotate', data=data,
        headers={'X-Vault-Token': VAULT_TOKEN, 'Content-Type': 'application/json'})
    urllib.request.urlopen(req)


def create_collection(name, dimension=768):
    try:
        req = urllib.request.Request(f'{QDRANT_URL}/collections/{name}', method='DELETE')
        urllib.request.urlopen(req)
    except: pass
    
    data = json.dumps({'vectors': {'size': dimension, 'distance': 'Cosine'}}).encode()
    req = urllib.request.Request(f'{QDRANT_URL}/collections/{name}', data=data,
        headers={'Content-Type': 'application/json'}, method='PUT')
    urllib.request.urlopen(req)


def encrypt_vector(vector):
    data = json.dumps({'vector': [float(v) for v in vector]}).encode()
    req = urllib.request.Request(f'{VAULT_ADDR}/v1/vector/encrypt/vector', data=data,
        headers={'X-Vault-Token': VAULT_TOKEN, 'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read())['data']['ciphertext']


def store_point(collection, point_id, vector, payload):
    data = json.dumps({
        'points': [{'id': point_id, 'vector': [float(v) for v in vector], 'payload': payload}]
    }).encode()
    req = urllib.request.Request(f'{QDRANT_URL}/collections/{collection}/points?wait=true',
        data=data, headers={'Content-Type': 'application/json'}, method='PUT')
    urllib.request.urlopen(req)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║   📦 Ingesting Demo Data for vec2text Attack                        ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    print("📦 Configuring infrastructure...")
    configure_vault()
    create_collection('raw_documents')
    create_collection('secure_documents')
    print("   ✅ Vault and Qdrant ready\n")

    print("📦 Loading GTR embedder...")
    from sentence_transformers import SentenceTransformer
    gtr = SentenceTransformer('sentence-transformers/gtr-t5-base')
    print("   ✅ Loaded\n")

    print("📝 Storing documents...\n")

    for doc in DOCUMENTS:
        print(f"   \"{doc['text']}\"")
        
        # Embed
        embedding = gtr.encode(doc['text'])
        
        # Store RAW
        store_point('raw_documents', doc['id'], embedding, {'text': doc['text']})
        print("      → raw_documents ✅")
        
        # Store ENCRYPTED
        encrypted = encrypt_vector(embedding)
        store_point('secure_documents', doc['id'], encrypted, {'text': doc['text']})
        print("      → secure_documents ✅")
        print()

    print("=" * 70)
    print("✅ Done! Data stored in both collections.")
    print()
    print("Next: Run the breach simulation:")
    print("   python3 scripts/attack-stored-vectors.py")
    print()


if __name__ == "__main__":
    main()

