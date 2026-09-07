#!/usr/bin/env bash
# Oryvex Research — first-time VPS deploy. Run ON THE SERVER as a sudoer.
#
#   sudo DOMAIN=yourdomain.com bash deploy/deploy.sh
#
# Idempotent: safe to re-run. Does NOT touch .env, oryvex.db or static/coa/.
set -euo pipefail

DOMAIN="${DOMAIN:?set DOMAIN=yourdomain.com}"
APP_DIR="${APP_DIR:-/opt/oryvex}"
PORT="${PORT:-8012}"
SERVICE=oryvex

echo "▸ deploying $DOMAIN from $APP_DIR on 127.0.0.1:$PORT"

# ── refuse to trample another site on this port ──────────────────
if ss -ltn "sport = :$PORT" | grep -q LISTEN; then
  if ! systemctl is-active --quiet "$SERVICE"; then
    echo "✗ port $PORT is already in use by something that isn't $SERVICE."
    ss -ltnp "sport = :$PORT" | tail -n +2
    echo "  Re-run with a free port:  sudo DOMAIN=$DOMAIN PORT=8013 bash deploy/deploy.sh"
    exit 1
  fi
fi

cd "$APP_DIR"

# ── python env ───────────────────────────────────────────────────
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt
echo "✓ dependencies installed"

# ── .env must exist and carry real secrets (never in git) ────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✗ .env was missing — created from .env.example."
  echo "  Fill in SMTP_PASSWORD, ADMIN_PASSWORD, OWNER_EMAIL, then re-run."
  exit 1
fi
for k in SMTP_PASSWORD ADMIN_PASSWORD; do
  v=$(grep -E "^$k=" .env | cut -d= -f2-)
  [ -n "$v" ] || { echo "✗ $k is empty in .env"; exit 1; }
done
grep -qE '^ADMIN_PASSWORD=(change-me|oryvex-admin-change-me)$' .env && {
  echo "✗ ADMIN_PASSWORD is still the default — change it in .env"; exit 1; }
echo "✓ .env present with secrets set"

# ── systemd ──────────────────────────────────────────────────────
sed -e "s#/opt/oryvex#${APP_DIR}#g" -e "s#--port [0-9]*#--port ${PORT}#" \
    deploy/oryvex.service > "/etc/systemd/system/${SERVICE}.service"
systemctl daemon-reload
echo "✓ systemd unit installed"

# ── nginx vhost (http only; certbot adds 443) ────────────────────
sed -e "s/oryvexresearch\.com/${DOMAIN}/g" \
    -e "s#/opt/oryvex#${APP_DIR}#g" \
    -e "s#127\.0\.0\.1:[0-9]*#127.0.0.1:${PORT}#" \
    deploy/nginx.conf > "/etc/nginx/sites-available/${SERVICE}"
ln -sf "/etc/nginx/sites-available/${SERVICE}" "/etc/nginx/sites-enabled/${SERVICE}"
nginx -t
systemctl reload nginx
echo "✓ nginx vhost installed for ${DOMAIN}"

# ── ownership: SQLite + COA uploads must be writable by the service
chown -R www-data:www-data "$APP_DIR"
chmod 640 "$APP_DIR/.env"
echo "✓ ownership set"

systemctl enable --now "$SERVICE"
systemctl restart "$SERVICE"
sleep 3
systemctl is-active --quiet "$SERVICE" \
  && echo "✓ $SERVICE running on 127.0.0.1:$PORT" \
  || { echo "✗ service failed:"; journalctl -u "$SERVICE" -n 30 --no-pager; exit 1; }

curl -sf -o /dev/null "http://127.0.0.1:${PORT}/" \
  && echo "✓ app responding locally" || echo "✗ app not responding"

cat <<NOTE

Next, SSL. On a multi-site box do NOT use \`certbot --nginx\` — it can rewrite a
neighbouring site's vhost. Use:

  sudo certbot certonly --webroot -w /var/www/html -d ${DOMAIN} -d www.${DOMAIN}

then add a 443 server block to /etc/nginx/sites-available/${SERVICE} pointing at
those certs and reload nginx.

Redeploys after this:
  cd ${APP_DIR} && git pull && sudo chown -R www-data:www-data ${APP_DIR} \\
    && sudo systemctl restart ${SERVICE}
NOTE
