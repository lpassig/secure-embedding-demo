# Secure RAG - Proof of Concept

A demonstration that **vector embeddings can be inverted to recover original text**, and how **Scale-and-Perturb encryption** protects against this attack.

## The Problem

Research shows that text embeddings reveal almost as much as the original text:
- [Text Embeddings Reveal (Almost) As Much As Text](https://arxiv.org/abs/2310.06816)
- Tools like [vec2text](https://github.com/vec2text/vec2text) can invert embeddings back to text

**If an attacker gains access to your vector database, they can recover your documents.**

## The Solution

This PoC uses HashiCorp Vault with a custom **Scale-and-Perturb** plugin to encrypt vectors before storing them. The encryption:
- Preserves approximate distances (so semantic search still works)
- Shifts vectors ~100% away from their original position
- Makes inversion attacks produce garbage

## Quick Start

### 1. Start the Stack

```bash
docker compose up --build -d
```

### 2. Initialize Services

```bash
./scripts/init-all.sh
```

### 3. Set Up Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install sentence-transformers vec2text
```

### 4. Run the Demo

```bash
# See the attack in action
python3 scripts/demo-real-vec2text.py
```

## Demo Results

```
📄 Original: "The cat sat on the mat."

🔓 RAW EMBEDDING:
   Recovered: "The cat sat on the mat."     ← ⚠️ EXACT MATCH!

🔒 ENCRYPTED EMBEDDING:
   Recovered: "singlet skirmish. I was..."  ← ✅ GARBAGE
```

| Vector Type | Attack Result |
|-------------|---------------|
| **RAW** | ⚠️ Text recovered exactly |
| **ENCRYPTED** | ✅ Only garbage recovered |

## Full Pipeline Demo

### Ingest Documents

```bash
# Ingest 5 sample documents with GTR embeddings (768-dim)
python3 scripts/ingest-gtr.py
```

### Semantic Search

```bash
python3 scripts/search-gtr.py "What is a vector database?"
```

### Breach Simulation

```bash
# Store data in both raw and encrypted collections
python3 scripts/ingest-demo-data.py

# Simulate attacker extracting and inverting vectors
python3 scripts/attack-stored-vectors.py
```

## Project Structure

```
secure-embedding-demo/
├── docker-compose.yml          # Stack: Qdrant + Vault with plugin
├── vault/
│   └── Dockerfile              # Builds Vault + vector encryption plugin
├── scripts/
│   ├── init-all.sh             # Initialize services (Vault + Qdrant)
│   ├── init-vault.sh           # Register Vault plugin
│   ├── ingest-gtr.py           # Embed → Encrypt → Store (RAG-style)
│   ├── search-gtr.py           # Semantic search over encrypted vectors
│   ├── demo-real-vec2text.py   # 🔓 Main inversion demo
│   ├── ingest-demo-data.py     # Store RAW + ENCRYPTED side by side
│   └── attack-stored-vectors.py # Breach simulation on stored vectors
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Qdrant | 6333 | Vector database (dashboard enabled) |
| Vault | 8200 | Vector encryption via Scale-and-Perturb plugin |

## API Reference

### Encrypt Vector

```bash
curl -X POST http://localhost:8200/v1/vector/encrypt/vector \
  -H "X-Vault-Token: root" \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, ...]}'
```

Response:
```json
{"data": {"ciphertext": [5.13, -2.4, ...]}}
```

## How It Works

1. **Raw embedding**: `text → GTR model → 768-dim vector`
2. **Encryption**: `vector → Vault Scale-and-Perturb → shifted vector`
3. **Storage**: `shifted vector → Qdrant`
4. **Search**: Query is also encrypted, distances preserved

### Why semantic search still works

- **Same transform for all vectors**: Vault encrypts **both** stored document embeddings and incoming query embeddings with the **same** secret, distance-preserving transform.
- **Distances are preserved**: For a query \(q\) and document \(x\), the distance in raw space and encrypted space stay close: \(\text{dist}(q, x) \approx \text{dist}(E_k(q), E_k(x))\).
- **Neighbors stay neighbors**: Because distances are preserved, the **nearest neighbors** in encrypted space are almost the same as in raw space → search quality is retained.
- **But inversion breaks**: Individual encrypted vectors are shifted ~100% away from their originals and depend on a **secret key**, so inversion models (like vec2text) cannot map them back to text.

So you get **usable semantic search** and **strong protection** against embedding inversion at the same time.

## Requirements

- Docker & Docker Compose
- Python 3.10+
- ~2GB disk space (for vec2text models)

## License

MIT
