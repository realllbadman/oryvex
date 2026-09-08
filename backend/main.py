"""FastAPI application entrypoint for the Oryvex Research store."""
import datetime
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.config import env_list, env_num, env_str
from backend.database import Base, SessionLocal, engine, get_db
from backend.models import Product

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
FRONTEND_DIR = BASE_DIR / "frontend"

# ─── Jinja2 (Python 3.12 fix) ────────────────────────────────────
# cache_size=0 avoids the bytecode-cache bug that surfaces on 3.12; we build
# the Environment explicitly and hand it to Jinja2Templates via `env=`.
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0,
)
templates = Jinja2Templates(env=_jinja_env)

# ─── Business config exposed to every template ───────────────────
def _digits(s: str) -> str:
    """Keep only digits — for wa.me / sms / tel links regardless of formatting."""
    return "".join(ch for ch in (s or "") if ch.isdigit())


_WA = os.getenv("WHATSAPP", "+14795895269")
_DIRECT = os.getenv("DIRECT_PHONE", "+16452170576")

BUSINESS = {
    "name": os.getenv("BUSINESS_NAME", "Oryvex Research"),
    "email": os.getenv("BUSINESS_EMAIL", "support@oryvexresearch.com"),
    "phone": os.getenv("OWNER_PHONE", "+1 (645) 217-0576"),
    "whatsapp": _WA,
    "whatsapp_digits": _digits(_WA),                 # for wa.me/<digits>
    "whatsapp_display": "+" + _digits(_WA),          # always compact: +13185875570
    "direct_phone": _DIRECT,
    "direct_digits": _digits(_DIRECT),               # for sms:/tel:
    "direct_display": "+" + _digits(_DIRECT),        # always compact: +13184578486
    "min_order": env_num("MIN_ORDER", "0"),
    "free_ship_threshold": env_num("FREE_SHIP_THRESHOLD", "250"),
    "flat_shipping": env_num("FLAT_SHIPPING", "15"),
    "ship_priority": env_num("SHIP_PRIORITY", "20"),
    "ship_overnight": env_num("SHIP_OVERNIGHT", "60"),
    "insurance_fee": env_num("INSURANCE_FEE", "15"),
    "payment_methods": env_list(
        "PAYMENT_METHODS", "Cash App,Zelle,Apple Pay,Chime,PayPal,Bitcoin"),
}

CATEGORIES = [
    {"slug": "research-peptides", "name": "All Peptides"},
    {"slug": "mist-applicators", "name": "Mist Applicators"},
]


def _parse(product: Product) -> dict:
    """Convert a Product row to a template-friendly dict (JSON fields parsed)."""
    variants = json.loads(product.variants) if product.variants else []
    notes = json.loads(product.research_notes) if product.research_notes else []
    return {
        "id": product.id,
        "slug": product.slug,
        "name": product.name,
        "category": product.category,
        "cas_number": product.cas_number,
        "molecular_formula": product.molecular_formula,
        "purity": product.purity,
        "form": product.form,
        "storage": product.storage,
        "price": product.price,
        "original_price": product.original_price,
        "variants": variants,
        "description": product.description,
        "research_notes": notes,
        "in_stock": bool(product.in_stock),
        "badge": product.badge,
        "image": product.image or "/static/images/placeholder.jpg",
        "coa_file": product.coa_file,
        "coa_lab": product.coa_lab,
    }


def _migrate(engine) -> None:
    """Add columns introduced after the first release (SQLite create_all does
    not ALTER existing tables). Idempotent — safe to run on every boot."""
    from sqlalchemy import text

    wanted = {
        "orders": {
            "coupon_code": "TEXT",
            "discount": "FLOAT DEFAULT 0",
            "payment_method": "TEXT",
            "shipping_method": "TEXT",
            "insurance": "FLOAT DEFAULT 0",
        },
    }
    with engine.begin() as conn:
        for table, cols in wanted.items():
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            for col, ddl in cols.items():
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate(engine)
    from backend.seed_data import sync_coupons, sync_products

    db = SessionLocal()
    try:
        sync_products(db)
        sync_coupons(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Oryvex Research Store", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ─── Routers ─────────────────────────────────────────────────────
from backend.routes import admin, bookings, coupons, orders, reviews  # noqa: E402

app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(coupons.router, prefix="/api/coupons", tags=["coupons"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


def _asset_version() -> str:
    """Cache-busting token = newest mtime of main.css / main.js. Changing the
    files changes the token, so browsers always refetch the current assets."""
    latest = 0.0
    for rel in ("css/main.css", "js/main.js", "favicon.ico",
                "images/hero-molecules.jpg", "images/about-lab.jpg"):
        try:
            latest = max(latest, (STATIC_DIR / rel).stat().st_mtime)
        except OSError:
            pass
    # Product art shares the token. nginx serves /static/ with `expires 7d`, so
    # without this a re-shoot leaves visitors on stale images for a week — and a
    # stale image against fresh CSS renders wrong (an old portrait cutout under
    # object-fit:cover shows up zoomed and cropped).
    try:
        vials = STATIC_DIR / "images" / "vials"
        latest = max([latest, vials.stat().st_mtime]
                     + [f.stat().st_mtime for f in vials.glob("*.png")])
    except (OSError, ValueError):
        pass
    return str(int(latest)) or "1"


def _ctx(request: Request, **extra) -> dict:
    ctx = {
        "business": BUSINESS,
        "categories": CATEGORIES,
        "asset_v": _asset_version(),
        "now_year": datetime.date.today().year,
    }
    ctx.update(extra)
    return ctx


# ─── Storefront routes ───────────────────────────────────────────
@app.get("/")
def home(request: Request):
    db = SessionLocal()
    try:
        products = [_parse(p) for p in db.query(Product).all()]
    finally:
        db.close()
    featured = [p for p in products if p["badge"] == "Best Seller"][:8]
    counts = {c["slug"]: 0 for c in CATEGORIES}
    for p in products:
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    return templates.TemplateResponse(
        request,
        "index.html",
        _ctx(request, products=products, featured=featured, counts=counts),
    )


@app.get("/products")
def products_page(request: Request):
    db = SessionLocal()
    try:
        products = [_parse(p) for p in db.query(Product).all()]
    finally:
        db.close()
    return templates.TemplateResponse(
        request,
        "products.html",
        _ctx(request, products=products),
    )


@app.get("/coas")
def coas_page(request: Request):
    db = SessionLocal()
    try:
        products = [_parse(p) for p in db.query(Product).order_by(Product.name).all()]
    finally:
        db.close()
    with_coa = [p for p in products if p.get("coa_file")]
    return templates.TemplateResponse(
        request, "coas.html",
        _ctx(request, products=with_coa, count=len(with_coa)),
    )


@app.get("/products/{slug}")
def product_detail(request: Request, slug: str):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.slug == slug).first()
        if not product:
            return templates.TemplateResponse(
                request, "product_detail.html",
                _ctx(request, product=None, related=[]), status_code=404,
            )
        parsed = _parse(product)
        related = [
            _parse(p)
            for p in db.query(Product)
            .filter(Product.category == product.category, Product.slug != slug)
            .limit(4)
            .all()
        ]
    finally:
        db.close()
    return templates.TemplateResponse(
        request, "product_detail.html",
        _ctx(request, product=parsed, related=related),
    )


@app.get("/checkout")
def checkout_page(request: Request):
    return templates.TemplateResponse(request, "checkout.html", _ctx(request))


@app.get("/about")
def about_page():
    return FileResponse(str(FRONTEND_DIR / "about.html"))


@app.get("/admin")
def admin_page():
    return FileResponse(str(FRONTEND_DIR / "admin.html"))
