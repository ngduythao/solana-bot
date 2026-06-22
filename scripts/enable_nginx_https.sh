#!/usr/bin/env bash
set -euo pipefail
if [ ! -f .env ]; then echo "Missing .env"; exit 1; fi
source ./.env
: "${DOMAIN:?Need DOMAIN in .env}"
: "${LETSENCRYPT_EMAIL:?Need LETSENCRYPT_EMAIL in .env}"

mkdir -p certbot/www certbot/conf nginx/conf.d
cat > nginx/conf.d/dashboard.conf <<NGX
server {
  listen 80;
  server_name ${DOMAIN};
  location /.well-known/acme-challenge/ {
    root /var/www/certbot;
  }
  location / {
    proxy_pass http://dashboard:8080;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
}
NGX

docker compose up -d nginx
# Get/renew cert (webroot challenge)
docker compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot \
  -d "${DOMAIN}" --email "${LETSENCRYPT_EMAIL}" --agree-tos --no-eff-email

# Switch Nginx to 443 with SSL
cat > nginx/conf.d/dashboard.conf <<'NGX'
server {
  listen 80;
  server_name DOMAIN_REPLACE;
  return 301 https://$host$request_uri;
}
server {
  listen 443 ssl;
  server_name DOMAIN_REPLACE;

  ssl_certificate /etc/letsencrypt/live/DOMAIN_REPLACE/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/DOMAIN_REPLACE/privkey.pem;

  location / {
    proxy_pass http://dashboard:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
NGX
sed -i "s/DOMAIN_REPLACE/${DOMAIN}/g" nginx/conf.d/dashboard.conf
docker compose restart nginx

echo "✅ HTTPS enabled at https://${DOMAIN}"
echo "ℹ️  Certs in ./certbot/conf (Let's Encrypt). Use cron to renew monthly:"
echo "    docker compose run --rm certbot renew && docker compose restart nginx"
