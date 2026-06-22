
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi

apt-get update -y
apt-get install -y nginx openssl

CN_SERVER="${MTLS_SERVER_CN:-solbot.local}"
WORK="/etc/solbot/mtls"
mkdir -p "$WORK/certs" "$WORK/private"
cd "$WORK"

# Generate CA
if [[ ! -f ca.key ]]; then
  openssl genrsa -out ca.key 4096
  openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -subj "/CN=Solbot CA" -out ca.crt
fi

# Server cert
if [[ ! -f server.key ]]; then
  openssl genrsa -out server.key 4096
  openssl req -new -key server.key -subj "/CN=${CN_SERVER}" -out server.csr
  openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 1095 -sha256
fi

# Client cert (one default client)
if [[ ! -f client.key ]]; then
  openssl genrsa -out client.key 4096
  openssl req -new -key client.key -subj "/CN=admin" -out client.csr
  openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 1095 -sha256
  # bundle to PKCS#12 for browser import
  openssl pkcs12 -export -inkey client.key -in client.crt -certfile ca.crt -out client.p12 -passout pass:
fi

# Nginx site
cat >/etc/nginx/sites-available/solbot_mtls <<'EOF'
server {
    listen              443 ssl;
    server_name         _;
    ssl_certificate     /etc/solbot/mtls/server.crt;
    ssl_certificate_key /etc/solbot/mtls/server.key;
    ssl_client_certificate /etc/solbot/mtls/ca.crt;
    ssl_verify_client on;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Proxy to local dashboard
    location / {
        proxy_pass http://127.0.0.1:8081/pro;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Host $host;
    }
}
EOF

ln -sf /etc/nginx/sites-available/solbot_mtls /etc/nginx/sites-enabled/solbot_mtls
rm -f /etc/nginx/sites-enabled/default || true
nginx -t
systemctl enable nginx --now

echo "[MTLS] Installed."
echo "[MTLS] Download client cert for browser: /etc/solbot/mtls/client.p12 (no password)"
echo "[MTLS] Access dashboard at https://<server-ip>/ (client cert required)"
