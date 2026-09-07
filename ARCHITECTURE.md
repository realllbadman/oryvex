# Research-Peptide Store — Architecture / Reverse-Engineering Blueprint

A complete breakdown of how this store is built, so it can be rebuilt or re-skinned
for a new peptide site. Nothing here is copied from any third party — it's the
structure of this codebase.

---

## 1. What it is (philosophy)

A server-rendered, multi-page **research-use-only peptide storefront** with an
**admin-contact order flow**: customers place an order online, **no payment is
taken on the site**, the owner gets an email and contacts the customer to confirm
stock and arrange payment (crypto / Zelle / CashApp / etc.). Compliance is
structural, not decoration: 21+ age gate, "Research Use Only" everywhere, COA
viewer per product, and a global disclaimer.

---

## 2. Stack

- **Python 3.10+ / FastAPI / Uvicorn** — one process, port 8012 locally.
- **SQLite via SQLAlchemy** (`oryvex.db`) — no ORM migrations framework; a tiny
  idempotent `_migrate()` ALTERs new columns at boot.
- **Jinja2 server-rendered templates** — multi-page, **no JS framework**.
- **Vanilla JS** (`static/js/main.js`) + small inline page scripts.
- **python-dotenv** for config.
- Deployed behind **nginx** + **systemd** + **certbot** on a shared VPS.

---

## 3. Folder structure

```
backend/
  main.py            # FastAPI app: config, routes, lifespan, migrate
  models.py          # SQLAlchemy tables: Product, Order, Booking, Coupon, Review
  schemas.py         # Pydantic v2 request/response models
  database.py        # engine, SessionLocal, Base, get_db
  seed_data.py       # PRODUCTS_SEED + sync_products + price/variant/COA overrides
  routes/            # orders.py, bookings.py, coupons.py, reviews.py, admin.py
  services/          # email.py (SMTP senders), coupons.py (validate)
templates/           # base, index, products, product_detail, checkout, coas, _product_card
frontend/            # admin.html (SPA), about.html  — served as FileResponse
static/
  css/main.css       # full design system (CSS variable tokens)
  js/main.js         # cart, age gate, coupons, size dropdown, modals, filters…
  images/vials/      # per-product vial images (<slug>.png)
  coa/               # uploaded COA files (git-ignored)
scripts/
  gen_vials.py       # generate branded vial art per product
  gen_sample_coa.py  # generate original sample COAs (illustrative)
  import_photos.py   # background-remove + install real product photos by slug
deploy/              # oryvex.service (systemd), nginx.conf
.env / .env.example  # config + secrets (never committed)
requirements.txt / README.md / backups/
```

---

## 4. Data model (`models.py`)

- **Product** — slug, name, category, cas_number, molecular_formula, purity, form,
  storage, price (base "from"), original_price, `variants` (JSON: `[{strength,price}]`),
  description, `research_notes` (JSON list), in_stock, badge, image, `coa_file`, `coa_lab`.
- **Order** — customer fields (name/phone/email/company/address…), `freight_region`,
  contact_pref/best_time/notes, `items` (JSON), total, status, `coupon_code`,
  `discount`, `payment_method`, `shipping_method`, `insurance`, `age_confirmed`, created_at.
- **Booking** — inquiry/quote/COA-request form submissions.
- **Coupon** — code (UPPERCASE), kind (percent|fixed), value, active, min_subtotal,
  expires_at, description.
- **Review** — product_slug, name, rating (1–5), title, body, `approved` (moderated), created_at.

New columns are added at boot by `_migrate()` (SQLite `create_all` won't ALTER
existing tables), so schema changes are safe on redeploy.

---

## 5. Config system (the most important pattern)

Config flows **`.env` → `BUSINESS` dict (main.py) → every template via `_ctx()`**.

- `BUSINESS` reads each value with `os.getenv("KEY", <code default>)`.
- **Precedence: the server's `.env` overrides the code default.** So a value set in
  `.env` wins; if it's absent, the code default applies. This is the #1 source of
  "I changed it but the live site didn't" — the server `.env` still had the old value.
- Phone/WhatsApp are normalized: `whatsapp_digits` (for `wa.me/<digits>`) and
  `whatsapp_display` (compact `+…`) are derived so links work regardless of formatting.
- Key config: `MIN_ORDER`, `FREE_SHIP_THRESHOLD`, `SHIP_PRIORITY`, `SHIP_OVERNIGHT`,
  `INSURANCE_FEE`, `PAYMENT_METHODS` (comma list), SMTP_*, OWNER_EMAIL, BUSINESS_NAME,
  ADMIN_USERNAME/PASSWORD, WHATSAPP, DIRECT_PHONE.

---

## 6. Backend routes

**Storefront (HTML):** `/`, `/products`, `/products/{slug}`, `/coas`, `/about`
(FileResponse), `/admin` (FileResponse).

**API:**
- `POST /api/orders/` — validates 21+, enforces `MIN_ORDER`, re-validates coupon
  server-side, computes shipping (method or international freight) + insurance,
  saves order, fires 2 emails via BackgroundTasks.
- `POST /api/bookings/` — inquiry; fires owner + customer emails.
- `GET /api/coupons/validate?code=&subtotal=` — server-side discount calc.
- `GET /api/reviews/{slug}` — approved reviews + average.
- `/api/admin/*` (HTTP Basic Auth): stats; orders CRUD; bookings CRUD; coupons CRUD;
  reviews moderation; `POST/DELETE /products/{slug}/coa` (upload / remove COA).

**Trailing slashes matter** on the POST endpoints (`/api/orders/`).

---

## 7. Catalog / seed system (`seed_data.py`)

`PRODUCTS_SEED` is a list of dicts (one per product). `sync_products(db)` upserts
by slug on boot (update existing, insert new, delete removed — but preserves
admin-owned fields like `coa_file`/`coa_lab`/`purity`). Layered post-processing:

1. `image` set to `/static/images/vials/<slug>.png`.
2. `_FROM_OVERRIDES` — set base "from" price per slug.
3. `_VARIANT_OVERRIDES` — exact per-size price ladders (replaces variants).
4. **2x-pack expansion** — adds a bulk pack after each single size for products
   without an exact ladder.
5. `_COA_*` spec overrides — purity/form/storage for products that have a certificate.

To add/edit products: edit `PRODUCTS_SEED` (+ overrides) and restart — no DB surgery.

---

## 8. Templates

- **base.html** — the shell: promo countdown bar, dark trust strip, nav, category
  chips, footer (contact + disclaimer), age-gate modal, cart drawer, quote modal,
  COA viewer modal, newsletter modal, reconstitution calculator modal, floating
  "Get X% Off" pill, Smartsupp snippet. Every page extends this.
- **index.html** — light hero w/ floating vials, feature bar, marquees, best-seller
  carousel, category grid, about band, scroll-reveal statement, embedded full
  "All Peptides" catalog (search + chips + grid), how-it-works, FAQ.
- **products.html** — "All Peptides" catalog page (search + category chips + grid).
- **product_detail.html** — spec table, **size dropdown** (native `<select>`, iOS
  picker on mobile), price, add-to-cart, trust badges, research context, inline
  COA (opens in popup), related products.
- **coas.html** — COA gallery (only products with an uploaded certificate).
- **_product_card.html** — reusable card macro (99% badge, price, Choose Size, COA eye).

Jinja is configured with `cache_size=0` and the newer `TemplateResponse(request,
name, ctx)` signature (Python 3.12 fix). Assets are cache-busted via
`?v=<mtime>` (`_asset_version()`).

---

## 9. Frontend JS

`static/js/main.js` (delegated events, no framework) owns: cart (localStorage
`pep_cart`) + drawer, **age gate** (sessionStorage), coupon capture from `?coupon=`
+ announcement bar, newsletter, reconstitution calculator, promo countdown,
product filters + category chips, product-detail **size dropdown**, COA viewer,
best-seller carousel, toasts. `checkout.html` has its own inline script for the
order form (totals, shipping method/insurance/freight, coupon apply, min-order and
21+ validation with on-screen messages).

## 10. Design system (`main.css`)

CSS-variable tokens: `--page` lilac, `--card`, `--ink` aubergine, `--royal`/`--indigo`/
`--violet` purples, `--green` status, `--danger`. Fonts: **Archivo** (headings,
900-weight neo-grotesque) + **Inter** (body) + **IBM Plex Mono** (countdown). To
re-skin a new site, mostly you change these tokens + fonts + `BUSINESS_NAME`.

---

## 11. Key features & how they work

- **Age gate** — full-screen modal, `sessionStorage` flag; shows once per session.
- **Cart** — localStorage, drawer with subtotal/shipping/total.
- **Checkout** — min-order gate ("add $X more"), 21+ required (both warn on click),
  **shipping model**: Free (≥ threshold) / Priority / Overnight, optional insurance,
  and **international freight replaces domestic shipping** (no double charge);
  coupon field; **payment-method picker** (from `PAYMENT_METHODS`, + "Other").
- **Coupons** — `?coupon=CODE` captured to localStorage, validated server-side,
  applied at checkout; admin CRUD; seed codes in `COUPONS_SEED`.
- **COA system** — admin uploads a real PDF/image per product; shows "COA pending"
  until then (never a fake certificate); viewer modal; Remove button per product.
- **Admin panel** — self-contained SPA (`frontend/admin.html`), HTTP Basic Auth,
  tabs for Orders / Inquiries / Products+COA / Coupons / Reviews, stats, moderation.
- **Email** — `services/email.py`, aiosmtplib STARTTLS:587, 4 senders (customer +
  owner for both inquiries and orders). Provider-agnostic (Gmail or Titan; Gmail
  app-password spaces are stripped only for Gmail). **Gotcha:** if `OWNER_EMAIL` ==
  the sending address, Gmail hides the copy from your Inbox (it's in All Mail) — use
  a different `OWNER_EMAIL`. On the server, `SMTP_PASSWORD` must be set in `.env`.
- **Reviews** — real, moderated (customer submits → admin approves → shows). No
  fabricated reviews.
- Extras: Smartsupp live chat (key in base.html), reconstitution calculator,
  newsletter capture, promo countdown, scroll-reveal typography.

---

## 12. Order flow (no online payment)

Add to cart → checkout (contact + shipping + payment method + 21+) → `POST /api/orders/`
→ order saved + **owner emailed "NEW ORDER — CONTACT CUSTOMER"** + customer emailed a
receipt ("no payment taken yet") → owner confirms stock and arranges payment manually
→ status updated in admin. **No card processing anywhere.**

---

## 13. Deployment

Per-app on the VPS: **systemd** service running uvicorn on a unique `127.0.0.1:PORT`,
**nginx** reverse proxy (name-based vhost → that port, serves `/static/` from disk),
**certbot** for SSL. Redeploy = `git pull` + `chown www-data` + `systemctl restart`.
`.env`, `oryvex.db`, and `static/coa/` are **not** in git — set/back-up separately.
(See the separate "Deploy a new site on the VPS" checklist for the exact steps and
the certbot-vhost gotcha.)

---

## 14. Compliance (required structural features for any peptide site)

These are not optional — build them in and keep them truthful:
1. **21+ age gate** blocking entry.
2. **"Research Use Only — not for human consumption"** on every product; no dosing /
   human-use / treatment claims anywhere.
3. **COA viewer per product** — only display **real** lab certificates; "COA pending"
   otherwise. Never fabricate certificates, purity numbers, lab names, or reviews.
4. **Global footer disclaimer** (in vitro research use only; not FDA-approved…).
5. Owner verifies purity/lab/manufacturer claims are true and confirms the **legality**
   of selling/shipping in their jurisdictions.

---

## 15. To rebuild / re-skin for a NEW peptide site

The "knobs" you change:
- **Brand & config:** `BUSINESS_NAME` + all `.env` values (domain, emails, phone,
  payment methods, thresholds).
- **Catalog:** rewrite `PRODUCTS_SEED` (+ price/variant overrides) with your products.
- **Images:** run `scripts/gen_vials.py` (branded placeholder art) or drop real
  photos into `static/images/vials/<slug>.png` (use `import_photos.py`).
- **Look:** swap the CSS tokens (`--violet` etc.) + Google fonts in `base.html`.
- **Copy:** hero/about/FAQ text in `index.html`, `about.html`.
- **Chat/analytics:** Smartsupp key in `base.html`.
- Everything else (cart, checkout, coupons, shipping, admin, email, COA system)
  works unchanged.

---

## 16. Gotchas cheat-sheet

- Server **`.env` overrides code defaults** — change values there + restart.
- `git pull` never touches `.env`, `oryvex.db`, or `static/coa/`.
- Jinja needs `cache_size=0` + new `TemplateResponse` signature on Python 3.12.
- POST endpoints use **trailing slashes** (`/api/orders/`).
- `chown -R www-data` after every server pull (SQLite/uploads must be writable).
- Gmail self-send hides from Inbox → use a different `OWNER_EMAIL`.
- Native `<select>` gives the iOS size-picker automatically on mobile.
- On a multi-site VPS, don't let `certbot --nginx` rewrite another site's vhost —
  use `certonly` + your own 443 block.
