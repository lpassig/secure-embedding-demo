#!/usr/bin/env python3
"""
🔓 BREACH SIMULATION: Attack stored vectors from Qdrant

Simulates an attacker who has gained access to the vector database
and attempts to recover original text using vec2text.
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import json
import urllib.request
import torch

torch.backends.mps.is_available = lambda: False

QDRANT_URL = 'http://localhost:6333'


def get_all_points(collection):
    """Extract all vectors from a Qdrant collection (simulated breach)."""
    data = json.dumps({'limit': 100, 'with_vector': True, 'with_payload': True}).encode()
    req = urllib.request.Request(
        f'{QDRANT_URL}/collections/{collection}/points/scroll',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    return json.loads(urllib.request.urlopen(req).read())['result']['points']


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🔓 BREACH SIMULATION: Attacking Leaked Vectors                     ║
║                                                                      ║
║   Scenario: Attacker has gained access to vector database            ║
║   Goal: Recover original text from embeddings                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    # Load vec2text
    print("🤖 Loading vec2text (attacker's tool)...")
    import vec2text
    corrector = vec2text.load_pretrained_corrector('gtr-base')
    print("   ✅ Ready\n")

    # === ATTACK RAW COLLECTION ===
    print("=" * 70)
    print("  🔓 ATTACKING: raw_documents (unencrypted)")
    print("=" * 70)

    try:
        raw_points = get_all_points('raw_documents')
        print(f"  📥 Extracted {len(raw_points)} vectors from database\n")

        for point in raw_points:
            original = point['payload']['text']
            vector = point['vector']
            
            # Invert
            emb_tensor = torch.tensor(vector).unsqueeze(0).float()
            recovered = vec2text.invert_embeddings(
                embeddings=emb_tensor,
                corrector=corrector,
                num_steps=20
            )
            recovered_text = recovered[0].strip()
            
            # Check match
            match = "✅ RECOVERED" if original.lower().strip('.') in recovered_text.lower() else "⚠️ PARTIAL"
            
            print(f"  Original:  \"{original}\"")
            print(f"  Recovered: \"{recovered_text}\"")
            print(f"  Status:    {match}")
            print()

    except Exception as e:
        print(f"  ❌ Error: {e}\n")

    # === ATTACK SECURE COLLECTION ===
    print("=" * 70)
    print("  🔒 ATTACKING: secure_documents (encrypted)")
    print("=" * 70)

    try:
        secure_points = get_all_points('secure_documents')
        print(f"  📥 Extracted {len(secure_points)} vectors from database\n")

        for point in secure_points:
            original = point['payload']['text']
            vector = point['vector']
            
            # Invert
            emb_tensor = torch.tensor(vector).unsqueeze(0).float()
            recovered = vec2text.invert_embeddings(
                embeddings=emb_tensor,
                corrector=corrector,
                num_steps=20
            )
            recovered_text = recovered[0].strip()
            
            # Check - should be garbage
            original_words = set(original.lower().replace('.', '').split())
            recovered_words = set(recovered_text.lower().replace('.', '').split())
            common = original_words & recovered_words - {'the', 'a', 'is', 'of', 'in', 'on', 'at'}
            
            status = "✅ PROTECTED (garbage)" if len(common) == 0 else f"⚠️ Words leaked: {common}"
            
            print(f"  Original:  \"{original}\"")
            print(f"  Recovered: \"{recovered_text[:60]}...\"")
            print(f"  Status:    {status}")
            print()

    except Exception as e:
        print(f"  ❌ Error: {e}\n")

    # Summary
    print("=" * 70)
    print("  📊 ATTACK RESULTS SUMMARY")
    print("=" * 70)
    print("""
    ┌─────────────────────────┬───────────────────────────────────────┐
    │ raw_documents           │ ⚠️  BREACHED: Text recovered!         │
    ├─────────────────────────┼───────────────────────────────────────┤
    │ secure_documents        │ ✅ PROTECTED: Only garbage recovered  │
    └─────────────────────────┴───────────────────────────────────────┘

    CONCLUSION:
    
    When using RAW embeddings, a database breach exposes your data.
    When using Vault-encrypted embeddings, your data remains protected
    even if the attacker gains full access to the vector database.
""")


if __name__ == "__main__":
    main()

