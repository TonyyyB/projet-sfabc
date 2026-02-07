#!/bin/bash
# ================================================================
#  init-letsencrypt.sh
#  Obtient le premier certificat Let's Encrypt pour le domaine.
#
#  Usage :
#    chmod +x init-letsencrypt.sh
#    sudo ./init-letsencrypt.sh
#
#     À exécuter UNE SEULE FOIS lors du premier déploiement.
#     Le renouvellement est ensuite automatique via le conteneur
#     certbot dans docker-compose.yml.
# ================================================================
set -e

# Charger les variables du .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DOMAIN" ]; then
    echo "La variable DOMAIN n'est pas définie dans .env"
    exit 1
fi

if [ -z "$CERTBOT_EMAIL" ]; then
    echo "La variable CERTBOT_EMAIL n'est pas définie dans .env"
    exit 1
fi

echo "Obtention du certificat SSL pour : $DOMAIN"

# 1. Créer un fichier nginx temporaire (HTTP uniquement, pour le challenge)
cat > nginx/nginx-init.conf <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'Waiting for SSL certificate...';
        add_header Content-Type text/plain;
    }
}
EOF

# 2. Démarrer nginx avec la config temporaire + certbot volumes
docker compose down || true

# Remplacer temporairement le template nginx
ORIG_TEMPLATE="nginx/nginx.conf.template"
BACKUP_TEMPLATE="nginx/nginx.conf.template.bak"
cp "$ORIG_TEMPLATE" "$BACKUP_TEMPLATE"
cp nginx/nginx-init.conf "$ORIG_TEMPLATE"

# Démarrer seulement nginx (sans la partie SSL)
# On surcharge la variable DOMAIN pour envsubst
DOMAIN=$DOMAIN docker compose up -d nginx

echo "Attente du démarrage de nginx..."
sleep 5

# 3. Lancer certbot pour obtenir le certificat
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$CERTBOT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

# 4. Restaurer la vraie config nginx (avec SSL)
mv "$BACKUP_TEMPLATE" "$ORIG_TEMPLATE"
rm -f nginx/nginx-init.conf

# 5. Redémarrer tout avec la config SSL complète
echo "Redémarrage avec la configuration HTTPS..."
docker compose down
docker compose up -d

echo ""
echo "Certificat SSL obtenu et configuré !"
echo "   → https://$DOMAIN"
echo ""
echo "   Le renouvellement automatique est assuré par le conteneur certbot."
