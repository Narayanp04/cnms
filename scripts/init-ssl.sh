#!/bin/bash
# =============================================================================
# ConnectXperts NMS - Initial SSL Certificate Setup
# Domain: monitor.connectxperts.in
# =============================================================================
# This script requests the initial Let's Encrypt certificate.
# Run this ONCE before the first production deployment.
#
# Prerequisites:
#   1. DNS A record for monitor.connectxperts.in must point to your server IP
#   2. Port 80 must be publicly accessible (for ACME HTTP-01 challenge)
#   3. Docker and Docker Compose must be installed
#
# Usage:
#   chmod +x scripts/init-ssl.sh
#   ./scripts/init-ssl.sh
# =============================================================================

set -euo pipefail

DOMAINS="monitor.connectxperts.in,status.connectxperts.in"
EMAIL="${CERTBOT_EMAIL:-admin@connectxperts.in}"

echo "========================================"
echo " ConnectXperts NMS - SSL Setup"
echo " Domains: $DOMAINS"
echo " Email:   $EMAIL"
echo "========================================"

# Ensure certbot directories exist
echo ""
echo "[1/5] Creating certbot directories..."
mkdir -p data/certbot/www data/certbot/conf
echo "  ✅ Done"

# Start nginx alone so it can serve the ACME challenge
echo ""
echo "[2/5] Starting nginx for ACME challenge..."
docker compose -f docker-compose.prod.yml up -d nginx 2>/dev/null || true
echo "  ✅ Nginx started on port 80"

# Wait for nginx to be ready
sleep 3

# Request the certificate
echo ""
echo "[3/5] Requesting Let's Encrypt certificate (multi-domain)..."
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d "$DOMAINS" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  --expand

echo "  ✅ Certificate obtained!"

# Stop the standalone nginx
echo ""
echo "[4/5] Stopping temporary nginx..."
docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true
echo "  ✅ Done"

# Update .env.production with correct CORS origins
echo ""
echo "[5/5] Updating CORS origins in .env.production..."
CORS_URL="https://monitor.connectxperts.in"
if grep -q "CORS_ORIGINS" backend/.env.production 2>/dev/null; then
  sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=$CORS_URL|" backend/.env.production
else
  echo "CORS_ORIGINS=$CORS_URL" >> backend/.env.production
fi
echo "  ✅ CORS_ORIGINS set to $CORS_URL"

echo ""
echo "========================================"
echo " ✅ SSL Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Start all services:"
echo "     docker compose -f docker-compose.prod.yml up -d"
echo ""
echo "  2. Your sites will be available at:"
echo "     https://monitor.connectxperts.in"
echo "     https://status.connectxperts.in"
echo ""
echo "  3. Certificates auto-renew every 12 hours via the certbot container."
echo ""
