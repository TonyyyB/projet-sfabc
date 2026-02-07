#!/bin/bash
# ================================================================
#  init-letsencrypt.sh
#  Obtient le premier certificat Let's Encrypt pour le domaine.
#
#  Usage :
#    chmod +x init-letsencrypt.sh
#    sudo ./init-letsencrypt.sh
#
#  A executer UNE SEULE FOIS lors du premier deploiement.
#  Le renouvellement est ensuite automatique via le conteneur
#  certbot dans docker-compose.yml.
# ================================================================
set -e

# Charger les variables du .env (sans interpréter les $)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

if [ -z "$DOMAIN" ]; then
    echo "ERREUR : La variable DOMAIN n'est pas definie dans .env"
    exit 1
fi

if [ -z "$CERTBOT_EMAIL" ]; then
    echo "ERREUR : La variable CERTBOT_EMAIL n'est pas definie dans .env"
    exit 1
fi

echo "=== Obtention du certificat SSL pour : $DOMAIN ==="

# ---------------------------------------------------------------
# Etape 1 : Creer un certificat auto-signe temporaire
#   Permet a nginx de demarrer avec la config SSL complete
#   (il a besoin de fichiers cert pour demarrer, meme invalides)
# ---------------------------------------------------------------
echo ""
echo "[1/5] Creation d'un certificat temporaire auto-signe..."
docker compose run --rm --entrypoint "" certbot sh -c "\
    mkdir -p /etc/letsencrypt/live/$DOMAIN && \
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
        -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
        -subj '/CN=$DOMAIN' 2>/dev/null"

# ---------------------------------------------------------------
# Etape 2 : Demarrer tous les services
#   nginx utilise le cert temporaire pour demarrer sans erreur
# ---------------------------------------------------------------
echo ""
echo "[2/5] Demarrage de tous les services..."
docker compose up -d --force-recreate
echo "    Attente du demarrage de nginx (10s)..."
sleep 10

# ---------------------------------------------------------------
# Etape 3 : Supprimer le certificat temporaire
# ---------------------------------------------------------------
echo ""
echo "[3/5] Suppression du certificat temporaire..."
docker compose run --rm --entrypoint "" certbot sh -c "\
    rm -rf /etc/letsencrypt/live/$DOMAIN && \
    rm -rf /etc/letsencrypt/archive/$DOMAIN && \
    rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf"

# ---------------------------------------------------------------
# Etape 4 : Demander le vrai certificat Let's Encrypt
#   --entrypoint "" bypasse la boucle de renouvellement
#   pour executer directement certbot certonly
# ---------------------------------------------------------------
echo ""
echo "[4/5] Demande du certificat Let's Encrypt..."
docker compose run --rm --entrypoint "" certbot \
    certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email "$CERTBOT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

# ---------------------------------------------------------------
# Etape 5 : Recharger nginx avec le vrai certificat
# ---------------------------------------------------------------
echo ""
echo "[5/5] Rechargement de nginx avec le vrai certificat..."
docker compose exec nginx nginx -s reload

echo ""
echo "=========================================="
echo "  Certificat SSL obtenu et configure !"
echo "  --> https://$DOMAIN"
echo ""
echo "  Le renouvellement automatique est assure"
echo "  par le conteneur certbot."
echo "=========================================="
