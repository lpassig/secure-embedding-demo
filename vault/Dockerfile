# ─────────────────────────────────────────────────────────────
# Multi-stage build for HashiCorp Vault with Vector DPE Plugin
# Stage 1: Build the Go plugin
# Stage 2: Runtime with Vault
# ─────────────────────────────────────────────────────────────

# ============================================================
# STAGE 1: Builder - Compile the vault-vector-dpe plugin
# ============================================================
FROM golang:1.22 AS builder

WORKDIR /build

# Clone the vault-vector-dpe repository
RUN git clone https://github.com/lpassig/vault-vector-dpe.git .

# Show repo structure for debugging
RUN ls -la && ls -la cmd/

# Download dependencies
RUN go mod download

# Build the plugin binary from cmd directory
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o vault-vector-dpe ./cmd/...

# ============================================================
# STAGE 2: Runtime - Vault with the plugin
# ============================================================
FROM hashicorp/vault:latest

# Create plugin directory
RUN mkdir -p /vault/plugins

# Copy the compiled plugin from builder stage
COPY --from=builder /build/vault-vector-dpe /vault/plugins/vault-vector-dpe

# Ensure plugin is executable
RUN chmod +x /vault/plugins/vault-vector-dpe

# Expose Vault port
EXPOSE 8200

# Default entrypoint is vault, command will be passed from docker-compose
