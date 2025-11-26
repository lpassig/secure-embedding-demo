#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Vault Vector DPE Plugin Initialization Script
# Run this after `docker compose up` to configure the plugin
# ─────────────────────────────────────────────────────────────

set -e

# Configuration
VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"
PLUGIN_NAME="vault-vector-dpe"
PLUGIN_PATH="/vault/plugins/${PLUGIN_NAME}"
SECRETS_PATH="vector"

echo "═══════════════════════════════════════════════════════════"
echo "  Vault Vector DPE Plugin Initialization"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Export for vault CLI
export VAULT_ADDR
export VAULT_TOKEN

# Wait for Vault to be ready
echo "⏳ Waiting for Vault to be ready..."
until curl -sf "${VAULT_ADDR}/v1/sys/health" > /dev/null 2>&1; do
    echo "   Vault not ready yet, waiting..."
    sleep 2
done
echo "✅ Vault is ready!"
echo ""

# Login to Vault
echo "🔐 Logging into Vault..."
vault login "${VAULT_TOKEN}" > /dev/null 2>&1
echo "✅ Logged in successfully"
echo ""

# Calculate SHA256 of the plugin binary
echo "🔢 Calculating plugin SHA256..."
PLUGIN_SHA=$(docker exec vault sha256sum "${PLUGIN_PATH}" | cut -d' ' -f1)
echo "   SHA256: ${PLUGIN_SHA}"
echo ""

# Register the plugin
echo "📦 Registering plugin '${PLUGIN_NAME}'..."
vault plugin register \
    -sha256="${PLUGIN_SHA}" \
    -command="${PLUGIN_NAME}" \
    secret "${PLUGIN_NAME}"
echo "✅ Plugin registered"
echo ""

# Enable the secrets engine
echo "🚀 Enabling secrets engine at '${SECRETS_PATH}/'..."
vault secrets enable -path="${SECRETS_PATH}" "${PLUGIN_NAME}" 2>/dev/null || \
    echo "   (Secrets engine may already be enabled)"
echo "✅ Secrets engine enabled"
echo ""

# Configure the plugin with Scale-and-Perturb parameters
echo "⚙️  Configuring plugin parameters..."
vault write "${SECRETS_PATH}/config/rotate" \
    dimension=1536 \
    scaling_factor=10.0 \
    approximation_factor=5.0
echo "✅ Plugin configured with:"
echo "   - dimension: 1536"
echo "   - scaling_factor: 10.0"
echo "   - approximation_factor: 5.0"
echo ""

# Verify the setup
echo "🔍 Verifying setup..."
echo ""
echo "Enabled secrets engines:"
vault secrets list | grep -E "^(Path|vector)"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Vault Vector DPE Plugin Ready!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "You can now use the plugin:"
echo ""
echo "  # Encrypt a vector (must be 1536 dimensions)"
echo "  vault write vector/encrypt/vector vector='[0.1, 0.2, ...]'"
echo ""
echo "  # Note: The plugin uses Scale-and-Perturb encryption"
echo "  # which preserves approximate distances for similarity search"
echo ""
echo "  # From n8n, use HTTP Request to:"
echo "  POST http://vault:8200/v1/vector/encrypt/vector"
echo "  Header: X-Vault-Token: root"
echo ""

