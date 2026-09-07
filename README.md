# Oryvex Research Store

A full-stack, research-use-only peptide storefront: FastAPI + SQLite + Jinja2,
server-rendered, no JS framework. Orders use an **admin-contact flow** — no
online payment is taken.

- **Stack:** Python 3.12, FastAPI, Uvicorn (port **8012**), SQLAlchemy + SQLite
  (`oryvex.db`), Jinja2 templates, python-dotenv.
- **Compliance-first:** every product is labelled *Research Use Only*, a 21+ age
  gate blocks the site on first visit, a COA viewer appears on every product, and
  a research-use disclaimer is in every footer.

---

## 1. Local setup

```bash
# from the project root
python3 -m venv .venv && source .venv/bin/activate    # Python 3.12 recommended
pip install -r requirements.txt
cp .env.example .env                                   # then edit .env
./run.sh
```

Open http://localhost:8012 (store) and http://localhost:8012/admin (admin panel).

**Always start it with `./run.sh`, not `uvicorn` directly** — run.sh frees the
port first, so you never see "address already in use".

On startup the app creates the tables and runs `sync_products()` to load the
catalog from `backend/seed_data.py`.

> **Python 3.12 note (Jinja2):** the app builds its Jinja `Environment` with
> `cache_size=0` and passes it via `Jinja2Templates(env=...)`, and uses the newer
> `TemplateResponse(request, "x.html", {...})` signature. Keep both — they avoid a
> template-cache bug and the deprecated context signature on 3.12.

---

## 2. Environment variables (`.env`)

| Var | Purpose |
|---|---|
| `SMTP_HOST` / `SMTP_PORT` | Gmail: `smtp.gmail.com` / `587` |
| `SMTP_USER` | The Gmail address that sends mail |
| `SMTP_PASSWORD` | Gmail **App Password** (spaces are stripped automatically) |
| `OWNER_EMAIL` | Where new-order / new-inquiry alerts are delivered |
| `BUSINESS_EMAIL`, `BUSINESS_NAME`, `OWNER_PHONE`, `WHATSAPP` | Shown in templates + emails |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Admin panel HTTP Basic Auth |
| `DATABASE_URL` | Default `sqlite:///./oryvex.db` |
| `FREE_SHIP_THRESHOLD` / `FLAT_SHIPPING` | Shipping math (default `200` / `15`) |

### Gmail App Password
1. Enable 2-Step Verification on the Google account.
2. Google Account → Security → **App passwords** → generate one for "Mail".
3. Paste the 16-character value into `SMTP_PASSWORD`. Spaces don't matter — the
   app strips them.

If SMTP is not configured, the app still works; email sends are skipped and
logged (`[email] skipped …`) instead of crashing.

---

## 3. How orders work (no online payment)

1. Customer adds items to the cart and goes to **/checkout**.
2. They must tick the **21+ / research-use** checkbox (submit stays disabled
   until they do). The order posts to `POST /api/orders/` with
   `age_confirmed: true`.
3. The backend rejects any order without `age_confirmed` (**400**), computes
   shipping, saves the order, and emails:
   - the **customer** a receipt ("no payment taken yet"), and
   - the **owner** a `NEW ORDER — CONTACT CUSTOMER` alert with full details.
4. You contact the customer to confirm stock and arrange payment (bank transfer
   / Zelle / crypto — whatever you support), then update the order status in the
   admin panel.

**Shipping:** free base shipping at/above `FREE_SHIP_THRESHOLD`, otherwise
`FLAT_SHIPPING`, plus a flat international surcharge by freight region (see
`FREIGHT_REGIONS` in `backend/routes/orders.py`). The checkout JS mirrors this so
the on-screen total matches the backend.

---

## 4. Managing the catalog

Products live in **`backend/seed_data.py`** (`PRODUCTS_SEED`). To add/edit/remove
a product, edit that list and **restart** the app — `sync_products()` upserts by
`slug` (updates existing, inserts new, deletes rows no longer in the seed).

Each product dict: `slug, name, category, cas_number, molecular_formula, purity,
form, storage, price, original_price, variants (list of {strength, price}),
description, research_notes (list of strings), in_stock, badge, image`.

**Keep all copy research-framed** — mechanism/class only. No dosing, no human-use
language.

### Admin-owned fields are preserved on restart
`coa_file`, `coa_lab`, and `purity` are **not** overwritten by a restart/sync on
existing products (see `_ADMIN_FIELDS` in `seed_data.py`). This is deliberate: an
uploaded COA must survive re-syncing the catalog. Seed values for these fields
apply only when a product is first inserted. If you need to change purity on an
existing product, do it in the admin panel (or clear the DB row).

---

## 5. Uploading real COAs

In the admin panel → **Products / COA** tab → **Upload COA** for a product:
- attach a **PDF/PNG/JPG/WEBP** file,
- set the **testing lab** name and **purity** text.

Files are stored under `static/coa/` and linked from the product. Until you
upload one, the product shows **"COA pending"** — never a fake certificate.

> Only publish lab names and purity figures you can back with a real COA.

---

## 5b. Discount codes, newsletter & calculator

**Coupon codes.** Codes can be shared as `https://yoursite/?coupon=CODE` (e.g.
`?coupon=oryvex15`). On any page the code is captured, stored in `localStorage`, and
shown in the announcement bar; at checkout it's revalidated **server-side** and
applied. The order route never trusts a client-sent discount — it recomputes it
from the coupon in the DB. Manage codes in the admin **Coupons** tab (percent or
fixed, optional minimum subtotal, enable/disable, delete). Seed examples live in
`COUPONS_SEED` (`backend/seed_data.py`): `ORYVEX15` (15%), `WELCOME10` (10%),
`RESEARCH20` (20%), `BULK40` ($40 off over $350) — **replace these with your own real codes**. Seed
coupons are only *inserted* if missing, so admin edits are never clobbered on
restart.

**Newsletter / "Get 15% Off".** The floating pill and hero CTA open an email-
capture modal that saves the signup (as a `Newsletter Signup` inquiry) and
reveals a code (`WELCOME10` by default — keep it in sync with an active coupon;
the code lives in `main.js` as `NL_CODE`).

**Reconstitution calculator.** The 🧮 nav button opens a research reconstitution
calculator (peptide mass + solvent volume → concentration in mg/mL, mcg/mL, and
mcg per syringe unit). It is **concentration reference only, framed for lab use —
not dosing guidance**, consistent with the research-use-only policy.

## 6. Changing the admin password

Edit `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env` and restart. Auth is HTTP
Basic (`secrets.compare_digest`) on every `/api/admin/*` route. **Change the
default `changeme123` before going live**, and always run behind HTTPS so
credentials aren't sent in the clear.

---

## 7. VPS deployment

```bash
# on the server, as a deploy user
sudo mkdir -p /opt/oryvex && sudo chown $USER /opt/oryvex
git clone <your-repo> /opt/oryvex && cd /opt/oryvex
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # edit with real values; set a strong ADMIN_PASSWORD

# systemd service (port 8012, 127.0.0.1)
sudo cp deploy/oryvex.service /etc/systemd/system/oryvex.service
sudo systemctl daemon-reload && sudo systemctl enable --now oryvex

# nginx reverse proxy + static
sudo cp deploy/nginx.conf /etc/nginx/sites-available/oryvex
sudo ln -s /etc/nginx/sites-available/oryvex /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# SSL (after DNS is pointed at the server)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Nginx serves `/static/` (including `/static/coa/`) directly from disk and proxies
everything else to Uvicorn on `127.0.0.1:8012`. `client_max_body_size 20M` allows
COA uploads.

**Redeploy:** `cd /opt/oryvex && git pull && sudo systemctl restart oryvex`

The SQLite file `oryvex.db` and `static/coa/` hold your data — **back them up**
and don't let a redeploy wipe them (they're git-ignored; keep them out of the
repo).

---

## 8. Smartsupp live chat (optional)

`templates/base.html` has a commented Smartsupp placeholder just before
`</script>`/`</body>`. Paste your Smartsupp key snippet there to enable live chat.

---

## 9. Known gotchas

- **Python 3.12 + Jinja2:** keep `Environment(..., cache_size=0)` and
  `Jinja2Templates(env=...)`; use the new `TemplateResponse(request, name, ctx)`
  signature (never put `request` inside the context dict).
- **Trailing slashes:** POST endpoints are `POST /api/orders/` and
  `POST /api/bookings/` **with** the trailing slash.
- **Gmail App Password spaces:** the display value has spaces; the app strips
  them, but make sure you copied all 16 characters.
- **Port 8012:** the app, systemd unit, and any firewall rule must agree.
- **Age gate is per-session:** it uses `sessionStorage`, so it reappears in a new
  browser session by design.

---

## 10. Compliance — owner responsibilities

This software provides the compliance *structure* (RUO labelling, 21+ age gate,
COA viewer, footer disclaimer, no human-use copy). **You, the owner, are
responsible for the substance:**

1. **Supply real COAs** for your own inventory. Products without one show "COA
   pending" — do not substitute a placeholder or another company's certificate.
2. **Keep all copy research-use-only.** Do not add dosing, human-use, treatment,
   cure, or medical-benefit claims anywhere (product copy, About, emails, chat).
3. **Verify your own claims.** Only publish purity figures, testing-lab names,
   and manufacturer details that are true and backed by real documentation. The
   seed ships purity as an editable placeholder and leaves lab/manufacturer
   fields blank on purpose — fill in *your* real partners.
4. **Confirm legality.** It is your responsibility to confirm the legality of
   selling and shipping these compounds to each destination and jurisdiction you
   operate in, and to comply with all applicable laws and regulations.

The global disclaimer shown on every page:

> All products are sold strictly for in vitro laboratory research use only. Not
> for human or veterinary use, consumption, or application. Not FDA-approved to
> diagnose, treat, cure, or prevent any disease.

---

## Oryvex Research — site specifics

Rebuilt to match the reference storefront section-for-section: sale bar with
live countdown → white header (wordmark, centred nav, search/wishlist/cart) →
full-bleed molecular hero → stacked "Independently Tested" headings → Popular
Peptides grid → crimson feature band → About → FAQ accordion → "Advance Your
Science Now" CTA flowing into the 4-column footer → black legal strip with the
FDA disclaimer. Product pages use the reference's layout (breadcrumb, COA box,
strength swatches, quantity stepper); checkout uses its Information / Shipping
address / Shipping Protection / Researcher details structure.

Crimson `#e33548`, near-black `#181818`, Outfit throughout. **Product imagery
and all COAs are our own** — vial art is generated by `scripts/gen_vials.py`
and the hero/about artwork by `scripts/gen_art.py`; no third-party logo,
photography, certificate, or review was copied.

**One deliberate divergence:** the reference checkout collects card details.
This store takes **no payment online** — it keeps the admin-contact flow, so
checkout shows the payment-method picker (Cash App / Zelle / Apple Pay / Chime
/ PayPal / Bitcoin) instead of card fields. Rendering a card form that doesn't
charge anything would be collecting card numbers under false pretenses.

### Catalog (47 SKUs, 2 categories)

Names, prices, sale prices and size ladders are matched one-for-one to the
reference storefront. Product copy is our own.

| Product | Category | From | Was | Sizes |
|---|---|---|---|---|
| 5-Amino-1MQ | All Peptides | $39.99 | $47.99 | 10mg $39.99 / 50mg $119.99 |
| AHK-Cu | All Peptides | $89.99 | $107.99 | 100mg $89.99 |
| ARA-290 | All Peptides | $67.99 | $81.99 | 10mg $67.99 / 50mg $159.99 |
| Adamax | All Peptides | $65.99 | $70.99 | 5mg $65.99 |
| BPC-157 | All Peptides | $44.99 | $53.99 | 10mg $44.99 |
| BPC-157 — Mist Applicator | Mist Applicators | $89.99 | $107.99 | 10mg $89.99 |
| Bacteriostatic Water | All Peptides | $19.99 | $29.99 | 10ml $19.99 / 20ml $37.99 / 30ml $55.99 |
| CJC-1295 (No DAC) | All Peptides | $39.99 | $47.99 | 5mg $39.99 / 10mg $64.99 |
| CJC-1295 / Ipamorelin (No DAC) | All Peptides | $74.99 | $89.99 | 10mg $74.99 |
| Cagrilintide | All Peptides | $119.99 | $143.99 | 10mg $119.99 |
| DSIP | All Peptides | $59.99 | $71.99 | 10mg $59.99 |
| DSIP — Mist Applicator | Mist Applicators | $74.99 | $89.99 | 5mg $74.99 |
| Epithalon | All Peptides | $54.99 | $65.99 | 10mg $54.99 / 40mg $99.99 |
| FOXO4-DRI | All Peptides | $179.99 | $215.99 | 10mg $179.99 |
| GHK-Cu | All Peptides | $44.99 | $53.99 | 50mg $44.99 / 100mg $74.99 |
| GLOW | All Peptides | $100.00 | $120.00 | 70mg $100.00 |
| GLP-1T | All Peptides | $59.99 | $71.99 | 10mg $59.99 |
| GLP-2 | All Peptides | $49.99 | $82.99 | 10mg $49.99 |
| GLP-3RT | All Peptides | $54.99 | $65.99 | 5mg $54.99 / 10mg $79.99 / 20mg $129.99 / 30mg $149.99 |
| Glutathione | All Peptides | $40.00 | $48.00 | 600mg $40.00 / 1500mg $89.99 |
| IGF1-LR3 | All Peptides | $89.99 | $107.99 | 1mg $89.99 |
| Ipamorelin | All Peptides | $74.99 | $89.99 | 10mg $74.99 |
| KLOW | All Peptides | $112.00 | $126.00 | 80mg $112.00 |
| KPV | All Peptides | $44.99 | $53.99 | 10mg $44.99 / 30mg $119.99 |
| KPV — Mist Applicator | Mist Applicators | $79.99 | $95.99 | 10mg $79.99 |
| Kisspeptin | All Peptides | $34.99 | $41.99 | 10mg $34.99 |
| LL-37 | All Peptides | $89.99 | $107.99 | 5mg $89.99 |
| MOTS-C | All Peptides | $54.99 | $77.99 | 10mg $54.99 / 40mg $139.99 |
| MT-1 | All Peptides | $49.99 | $83.99 | 10mg $49.99 |
| MT-2 | All Peptides | $40.99 | $49.99 | 10mg $40.99 |
| MT-2 — Mist Applicator | Mist Applicators | $99.99 | $119.99 | 10mg $99.99 |
| N-Acetyl Epitalon | All Peptides | $64.99 | $77.99 | 5mg $64.99 |
| NAD+ | All Peptides | $74.99 | $89.99 | 500mg $74.99 / 1000mg $129.99 |
| PEG-MGF | All Peptides | $99.99 | $132.99 | 2mg $99.99 |
| PT-141 | All Peptides | $69.99 | $83.99 | 10mg $69.99 |
| PT-141 — Mist Applicator | Mist Applicators | $99.99 | $149.99 | 10mg $99.99 |
| Pinealon | All Peptides | $54.99 | $66.99 | 10mg $54.99 |
| SLU-PP-332 | All Peptides | $134.99 | $167.90 | 10mg $134.99 |
| SS-31 | All Peptides | $55.99 | $65.99 | 10mg $55.99 / 50mg $159.99 |
| Selank | All Peptides | $39.99 | $47.99 | 10mg $39.99 |
| Selank — Mist Applicator | Mist Applicators | $64.99 | $77.99 | 5mg $64.99 / 10mg $109.99 |
| Semax | All Peptides | $39.99 | $47.99 | 10mg $39.99 |
| Semax — Mist Applicator | Mist Applicators | $64.99 | $77.99 | 5mg $64.99 / 10mg $109.99 |
| TB-500 | All Peptides | $44.99 | $53.99 | 10mg $44.99 |
| Tesamorelin | All Peptides | $50.00 | $60.00 | 2mg $50.00 / 5mg $65.00 / 10mg $85.00 / 20mg $139.00 |
| Thymosin Alpha-1 | All Peptides | $119.99 | $191.99 | 10mg $119.99 |
| Wolverine Blend | All Peptides | $59.99 | $71.99 | 5mg/5mg $59.99 / 10mg/10mg $89.99 |

The listed price is the smallest size; the strike-through is the "was" price.
Edit `backend/seed_data.py` and restart to change any of it — the seed re-syncs
by slug on boot and never clobbers an uploaded COA.

### Contact / payment config

- WhatsApp `+1 (479) 589-5269` → `WHATSAPP`
- iMessage / text `+1 (645) 217-0576` → `DIRECT_PHONE`
- Payments: Cash App, Zelle, Apple Pay, Chime, PayPal, Bitcoin → `PAYMENT_METHODS`
- Free shipping from **$250**, no order minimum (`MIN_ORDER=0`)

### Before going live — owner checklist

1. Set the real domain + emails in `.env` (`BUSINESS_EMAIL`, `OWNER_EMAIL`,
   `SMTP_*`) and change `ADMIN_PASSWORD`.
2. Upload real COAs in the admin panel. Until then every product correctly
   shows **COA pending** — never publish a certificate you don't have.
3. The `99% PURE` card badge and the `≥99% HPLC` purity placeholder are
   **claims**: confirm they're true for your material, or edit them in
   `seed_data.py` / the admin panel.
4. Paste your own live-chat snippet into `templates/base.html` (the previous
   site's Smartsupp key has been removed).
5. Confirm the legality of selling/shipping these compounds in your
   jurisdictions.


### Running it (use `run.sh` — it frees the port first)

```bash
./run.sh            # foreground, --reload, Ctrl+C to stop
./run.sh bg         # background, logs to server.log
./run.sh stop       # stop it
PORT=8020 ./run.sh  # different port
```

`run.sh` finds whatever is listening on the port (via `ss`, falling back to
`lsof`/`fuser`), checks `/proc/<pid>/cmdline` to confirm it's this app's uvicorn,
and replaces it. If a **different** program holds the port it does not kill it —
it moves to the next free port and tells you the new URL. Either way starting
always succeeds, so "address already in use" cannot happen.

`./run.sh status` says what's running where; `./run.sh stop` shuts it down.
