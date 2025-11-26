#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Secure RAG - Complete Stack Initialization
# Runs all initialization scripts in the correct order
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Secure RAG Pipeline - Complete Initialization         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if containers are running
echo "🔍 Checking container status..."
cd "$PROJECT_DIR"

if ! docker compose ps | grep -q "running"; then
    echo "❌ Containers are not running!"
    echo ""
    echo "   Please start the stack first:"
    echo "   docker compose up --build -d"
    echo ""
    exit 1
fi

echo "✅ Containers are running"
echo ""

# ───────────────────────────────────────────────────────────────
# Step 1: Initialize Qdrant (basic health check)
# ───────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1/2: Checking Qdrant..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

QDRANT_URL="http://localhost:6333"

echo "⏳ Waiting for Qdrant..."
until curl -sf "${QDRANT_URL}/collections" > /dev/null 2>&1; do
    sleep 2
done

echo "✅ Qdrant is reachable"
echo ""

# ───────────────────────────────────────────────────────────────
# Step 2: Initialize Vault
# ───────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2/2: Initializing Vault..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

"$SCRIPT_DIR/init-vault.sh"

# ───────────────────────────────────────────────────────────────
# Summary
# ───────────────────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           🎉 Initialization Complete! 🎉                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│  Service URLs                                               │"
echo "├─────────────────────────────────────────────────────────────┤"
echo "│  Qdrant:  http://localhost:6333/dashboard                   │"
echo "│  Vault:   http://localhost:8200/ui  (token: root)           │"
echo "└─────────────────────────────────────────────────────────────┘"
echo ""

