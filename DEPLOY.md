# Deploy Oryvex Research on the VPS

Real config: app dir `/opt/oryvex`, runs on `127.0.0.1:8012`, systemd unit
`oryvex`, nginx vhost for `oryvexresearch.com`, user `www-data`.

**A) first-time deploy** below, **B) redeploy** further down. Already live and you
only changed code? Jump to **B**.

---

## Pre-flight (once)

- VPS with sudo (Ubuntu/Debian), Python 3.10+.
- DNS: **A record** for `oryvexresearch.com` (and `www`) → the VPS IP.
- Port **8012** must be free — this box already runs peptides on 8005 and
  another app on 8006:
  ```bash
  sudo ss -ltnp | grep 8012      # empty = free
  ```
  If taken, pick a new port and change it in the systemd unit **and** nginx.

---

## A) First-time deploy

### 1. Get the code onto the server
```bash
sudo mkdir -p /opt/oryvex
sudo chown $USER:$USER /opt/oryvex
git clone https://github.com/realllbadman/oryvex.git /opt/oryvex
cd /opt/oryvex
```

### 2. Virtualenv + dependencies
```bash
cd /opt/oryvex
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

### 3. Create the server .env  (NEVER comes from git — set it by hand)
```bash
cp .env.example .env
nano .env
```
Fill in for real:
- `SMTP_PASSWORD=` the Gmail App Password (16 chars, spaces are stripped)
- `SMTP_USER=oryvexresearch@gmail.com`
- `OWNER_EMAIL=` **a different inbox than SMTP_USER** — Gmail hides self-sent
  mail from the Inbox (it lands in All Mail). Right now both are
  `oryvexresearch@gmail.com`, so order alerts will look missing.
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — make this long and random. `/admin` is
  HTTP Basic on the public internet and exposes every order and customer.
- `BUSINESS_NAME=Oryvex Research`, `WHATSAPP=+14795895269`,
  `DIRECT_PHONE=+16452170576`, `OWNER_PHONE=+1 (645) 217-0576`
- `MIN_ORDER=0`, `FREE_SHIP_THRESHOLD=250`,
  `PAYMENT_METHODS=Cash App,Zelle,Apple Pay,Chime,PayPal,Bitcoin`

> **The server `.env` overrides the code defaults.** If a value looks wrong on
> the live site, it's almost always this file.

### 4. Permissions (SQLite + uploaded COAs must be writable by www-data)
```bash
sudo chown -R www-data:www-data /opt/oryvex
sudo chmod 640 /opt/oryvex/.env
```

### 5. Install the systemd service
```bash
sudo cp /opt/oryvex/deploy/oryvex.service /etc/systemd/system/oryvex.service
sudo systemctl daemon-reload
sudo systemctl enable --now oryvex
systemctl status oryvex --no-pager        # active (running)
curl -I http://127.0.0.1:8012             # HTTP/1.1 200
journalctl -u oryvex -f                    # live logs (Ctrl-C to stop)
```

### 6. Install the nginx vhost
```bash
sudo cp /opt/oryvex/deploy/nginx.conf /etc/nginx/sites-available/oryvex
sudo ln -s /etc/nginx/sites-available/oryvex /etc/nginx/sites-enabled/oryvex
sudo nginx -t && sudo systemctl reload nginx
```
`http://oryvexresearch.com` should now load — check DNS first with
`dig +short oryvexresearch.com`.

### 7. SSL — the SAFE method (multi-site VPS)

`certonly` obtains the cert **without** rewriting any vhost. Do not use plain
`certbot --nginx` here — that's what once made a domain serve the used-cars site.

```bash
sudo certbot certonly --nginx -d oryvexresearch.com -d www.oryvexresearch.com
```

Then replace the port-80 block in `/etc/nginx/sites-available/oryvex` with the
redirect + 443 pair — this exact block is already at the bottom of
`deploy/nginx.conf`, commented out, so you can just uncomment it:

```nginx
server {
    listen 80;
    server_name oryvexresearch.com www.oryvexresearch.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name oryvexresearch.com www.oryvexresearch.com;

    ssl_certificate     /etc/letsencrypt/live/oryvexresearch.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/oryvexresearch.com/privkey.pem;

    client_max_body_size 20M;

    location /static/ { alias /opt/oryvex/static/; expires 7d; access_log off; }
    location / {
        proxy_pass         http://127.0.0.1:8012;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```
```bash
sudo nginx -t && sudo systemctl reload nginx
sudo certbot renew --dry-run
```

### 8. Verify
- `https://oryvexresearch.com` loads with a padlock.
- 21+ age gate appears, catalog shows **47 products**.
- Place a test order → owner email arrives (check spam / All Mail).
- Log into `/admin`, upload one COA → the COA button appears on that product
  only (products without a certificate show no COA affordance at all).
- **Re-check your other sites still load** — proves nothing was disturbed.

---

## B) Redeploy (site already live, you pushed new code)

From your laptop: `git push`. Then on the server:
```bash
cd /opt/oryvex
sudo -u www-data git pull                 # .env / oryvex.db / static/coa NOT touched
.venv/bin/pip install -r requirements.txt # only if deps changed
sudo chown -R www-data:www-data /opt/oryvex
sudo systemctl restart oryvex
systemctl status oryvex --no-pager
```
Changed a business value (payment methods, phone, thresholds)? Edit the **server
`.env`** too — `git pull` never changes it — then restart.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| 502 Bad Gateway | app not running → `journalctl -u oryvex -f`; check port 8012 |
| Change didn't show up | server `.env` still has the old value; or hard-refresh (assets are `?v=`-busted) |
| Wrong site served on the domain | another vhost grabbed it — give this site its own `server_name` block and reload |
| Orders save but no email | `SMTP_PASSWORD` blank in server `.env`, or `OWNER_EMAIL == SMTP_USER` |
| COA upload fails / DB read-only | `sudo chown -R www-data:www-data /opt/oryvex` |
| Port 8012 in use | `sudo ss -ltnp \| grep 8012`; new port in unit + nginx, or `sudo fuser -k 8012/tcp` if stale |
| Product images missing | they're committed under `static/images/vials/` — confirm `git pull` brought them |

## Back up (before big changes)
```bash
cp /opt/oryvex/oryvex.db ~/oryvex-$(date +%F).db
cp /opt/oryvex/.env ~/oryvex.env.bak
tar czf ~/oryvex-coa-$(date +%F).tgz -C /opt/oryvex static/coa
```

---

## Shortcut

`deploy/deploy.sh` does steps 2, 4, 5 and 6 in one pass and refuses to run if the
port belongs to another site, `.env` is missing, or `ADMIN_PASSWORD` is still the
default. Steps 1, 3 and 7 stay manual.

```bash
sudo DOMAIN=oryvexresearch.com bash /opt/oryvex/deploy/deploy.sh
```
