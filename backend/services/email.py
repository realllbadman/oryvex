"""Email service (Gmail STARTTLS 587) for the admin-contact order flow.

Four senders:
  1. send_customer_confirmation(booking)         → inquiry / COA-request receipt
  2. send_owner_notification(booking)            → new-inquiry alert to owner
  3. send_order_customer_confirmation(...)        → "order received, no payment taken"
  4. send_order_owner_notification(...)           → "NEW ORDER — CONTACT CUSTOMER"

All sends are wrapped in try/except and log-and-return on failure so a mail
outage never crashes a request or a BackgroundTask.
"""
import os

from backend.config import env_num
from email.message import EmailMessage

import aiosmtplib

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(env_num("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
# Gmail app-passwords are displayed with spaces; strip them for Gmail only.
# Other providers (Titan, etc.) keep the password exactly as entered.
_raw_pw = os.getenv("SMTP_PASSWORD", "")
SMTP_PASSWORD = _raw_pw.replace(" ", "") if "gmail" in SMTP_HOST.lower() else _raw_pw
OWNER_EMAIL = os.getenv("OWNER_EMAIL", SMTP_USER)
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Oryvex Research")
BUSINESS_EMAIL = os.getenv("BUSINESS_EMAIL", SMTP_USER)
OWNER_PHONE = os.getenv("OWNER_PHONE", "")
WHATSAPP = os.getenv("WHATSAPP", "")
PAYMENT_METHODS = [m.strip() for m in os.getenv(
    "PAYMENT_METHODS",
    "Apple Pay,Chime,CashApp,Zelle,Venmo,Bitcoin (Crypto),E-Transfer"
).split(",") if m.strip()]

DISCLAIMER = (
    "All products are sold strictly for in vitro laboratory research use only. "
    "Not for human or veterinary use, consumption, or application. Not "
    "FDA-approved to diagnose, treat, cure, or prevent any disease."
)


def _base_html(title: str, body: str) -> str:
    """Wrap `body` in a branded header + footer with contact and disclaimer."""
    return f"""\
<!doctype html>
<html>
<body style="margin:0;background:#f3f0fa;font-family:Arial,Helvetica,sans-serif;color:#1a0f33;">
  <div style="max-width:640px;margin:0 auto;background:#ffffff;">
    <div style="background:linear-gradient(165deg,#2d1b52,#1a0f33);padding:28px 32px;">
      <div style="color:#ffffff;font-size:20px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">
        {BUSINESS_NAME}
      </div>
      <div style="color:#b9a7e6;font-size:13px;margin-top:4px;">{title}</div>
    </div>
    <div style="padding:28px 32px;font-size:15px;line-height:1.6;">
      {body}
    </div>
    <div style="padding:22px 32px;background:#1a0f33;color:#cbb8e8;font-size:12px;line-height:1.6;">
      <div style="margin-bottom:10px;">
        <strong style="color:#ffffff;">{BUSINESS_NAME}</strong><br/>
        Email: {BUSINESS_EMAIL}{(' &middot; Phone: ' + OWNER_PHONE) if OWNER_PHONE else ''}{(' &middot; WhatsApp: ' + WHATSAPP) if WHATSAPP else ''}
      </div>
      <div style="color:#8b7bb0;">{DISCLAIMER}</div>
    </div>
  </div>
</body>
</html>"""


def _rows(items) -> str:
    """Render an itemized HTML table body from a list of order items."""
    out = []
    for it in items:
        # accept dicts or objects
        name = it.get("name") if isinstance(it, dict) else getattr(it, "name", "")
        strength = it.get("strength") if isinstance(it, dict) else getattr(it, "strength", None)
        qty = it.get("quantity") if isinstance(it, dict) else getattr(it, "quantity", 0)
        unit = it.get("unit_price") if isinstance(it, dict) else getattr(it, "unit_price", 0)
        line = float(unit) * int(qty)
        out.append(
            f'<tr>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e6e0f2;">{name}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e6e0f2;">{strength or "—"}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e6e0f2;text-align:center;">{qty}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e6e0f2;text-align:right;">${float(unit):,.2f}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e6e0f2;text-align:right;">${line:,.2f}</td>'
            f'</tr>'
        )
    return "".join(out)


def _items_table(items, total: float, shipping: float,
                 discount: float = 0.0, coupon_code=None,
                 insurance: float = 0.0, ship_name: str = "Shipping",
                 freight: float = 0.0) -> str:
    subtotal = round(total - shipping - insurance - freight + discount, 2)
    ship_price_txt = "FREE" if shipping == 0 else f"${shipping:,.2f}"
    discount_row = ""
    freight_row = ""
    if freight and freight > 0:
        freight_row = (
            '<tr><td colspan="4" style="padding:8px 10px;text-align:right;">International freight</td>'
            f'<td style="padding:8px 10px;text-align:right;">${freight:,.2f}</td></tr>'
        )
    insurance_row = ""
    if insurance and insurance > 0:
        insurance_row = (
            '<tr><td colspan="4" style="padding:8px 10px;text-align:right;">Shipping insurance</td>'
            f'<td style="padding:8px 10px;text-align:right;">${insurance:,.2f}</td></tr>'
        )
    if discount and discount > 0:
        code_txt = f" ({coupon_code})" if coupon_code else ""
        discount_row = (
            f'<tr style="color:#22c55e;"><td colspan="4" style="padding:8px 10px;text-align:right;">'
            f'Discount{code_txt}</td>'
            f'<td style="padding:8px 10px;text-align:right;">-${discount:,.2f}</td></tr>'
        )
    return f"""\
<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">
  <thead>
    <tr style="background:#efeafb;color:#4a2f8f;text-align:left;">
      <th style="padding:8px 10px;">Product</th>
      <th style="padding:8px 10px;">Strength</th>
      <th style="padding:8px 10px;text-align:center;">Qty</th>
      <th style="padding:8px 10px;text-align:right;">Unit</th>
      <th style="padding:8px 10px;text-align:right;">Line</th>
    </tr>
  </thead>
  <tbody>{_rows(items)}</tbody>
  <tfoot>
    <tr><td colspan="4" style="padding:8px 10px;text-align:right;">Subtotal</td>
        <td style="padding:8px 10px;text-align:right;">${subtotal:,.2f}</td></tr>
    {discount_row}
    <tr><td colspan="4" style="padding:8px 10px;text-align:right;">Shipping ({ship_name})</td>
        <td style="padding:8px 10px;text-align:right;">{ship_price_txt}</td></tr>
    {freight_row}
    {insurance_row}
    <tr style="font-weight:700;color:#4a2f8f;">
        <td colspan="4" style="padding:8px 10px;text-align:right;">Total</td>
        <td style="padding:8px 10px;text-align:right;">${total:,.2f}</td></tr>
  </tfoot>
</table>"""


async def _send(to: str, subject: str, html: str) -> bool:
    """Send one HTML email. Returns True on success, False on any failure."""
    if not (SMTP_USER and SMTP_PASSWORD and to):
        print(f"[email] skipped '{subject}' → {to} (SMTP not configured)")
        return False
    msg = EmailMessage()
    msg["From"] = f"{BUSINESS_NAME} <{SMTP_USER}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("This message requires an HTML-capable email client.")
    msg.add_alternative(html, subtype="html")
    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            timeout=20,
        )
        return True
    except Exception as exc:  # never crash the caller
        print(f"[email] FAILED '{subject}' → {to}: {exc}")
        return False


def _g(obj, key, default=""):
    """Read a field from a dict or an object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


# ─── 1. Inquiry receipt to customer ──────────────────────────────
async def send_customer_confirmation(booking) -> bool:
    name = f"{_g(booking, 'first_name')} {_g(booking, 'last_name')}".strip()
    body = f"""\
<p>Hi {name or 'there'},</p>
<p>Thanks for reaching out to {BUSINESS_NAME}. We've received your inquiry and a
member of our team will reply shortly.</p>
<table style="width:100%;font-size:14px;margin:14px 0;">
  <tr><td style="color:#8b83a3;padding:4px 0;">Topic</td><td>{_g(booking,'service') or 'General Inquiry'}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Product of interest</td><td>{_g(booking,'product_interest') or '—'}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;vertical-align:top;">Your message</td><td>{_g(booking,'details') or '—'}</td></tr>
</table>
<p style="color:#8b83a3;font-size:13px;">Please note: all materials are supplied for laboratory research use only.</p>"""
    return await _send(_g(booking, "email"), f"We received your inquiry — {BUSINESS_NAME}",
                       _base_html("Inquiry received", body))


# ─── 2. Inquiry alert to owner ───────────────────────────────────
async def send_owner_notification(booking) -> bool:
    name = f"{_g(booking, 'first_name')} {_g(booking, 'last_name')}".strip()
    body = f"""\
<p><strong>New inquiry received.</strong></p>
<table style="width:100%;font-size:14px;margin:14px 0;">
  <tr><td style="color:#8b83a3;padding:4px 0;">Name</td><td>{name}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Email</td><td>{_g(booking,'email')}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Phone</td><td>{_g(booking,'phone') or '—'}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Topic</td><td>{_g(booking,'service') or 'General Inquiry'}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Product</td><td>{_g(booking,'product_interest') or '—'}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;vertical-align:top;">Details</td><td>{_g(booking,'details') or '—'}</td></tr>
</table>"""
    return await _send(OWNER_EMAIL, f"New inquiry — {name or 'website'}",
                       _base_html("New inquiry", body))


# ─── 3. Order receipt to customer (no payment taken) ─────────────
async def send_order_customer_confirmation(customer, items, total, shipping,
                                           discount=0.0, coupon_code=None,
                                           insurance=0.0, ship_label="Shipping",
                                           freight=0.0) -> bool:
    name = f"{_g(customer,'first_name')} {_g(customer,'last_name')}".strip()
    body = f"""\
<p>Hi {name or 'there'},</p>
<p>Your order has been received. <strong>No payment has been taken yet.</strong>
Our team will contact you shortly to confirm stock availability and arrange
payment.</p>
<p style="font-size:13px;color:#4a2f8f;"><strong>Accepted payment methods:</strong>
{" &middot; ".join(PAYMENT_METHODS)}.</p>
{_items_table(items, total, shipping, discount, coupon_code, insurance, ship_label, freight)}
<p style="color:#8b83a3;font-size:13px;">By submitting this order you confirmed
you are 21+ and that these products are for laboratory research use only.</p>"""
    return await _send(_g(customer, "email"), f"Order received — {BUSINESS_NAME}",
                       _base_html("Order received", body))


# ─── 4. Order alert to owner (CONTACT CUSTOMER) ──────────────────
async def send_order_owner_notification(customer, items, total, shipping,
                                        discount=0.0, coupon_code=None,
                                        insurance=0.0, ship_label="Shipping",
                                        freight=0.0) -> bool:
    name = f"{_g(customer,'first_name')} {_g(customer,'last_name')}".strip()
    addr = ", ".join(filter(None, [
        _g(customer, "address"), _g(customer, "city"), _g(customer, "state"),
        _g(customer, "zip"), _g(customer, "country"),
    ]))
    body = f"""\
<p><strong style="color:#e11d48;">NEW ORDER — CONTACT CUSTOMER TO CONFIRM &amp; ARRANGE PAYMENT.</strong></p>
<table style="width:100%;font-size:14px;margin:14px 0;">
  <tr><td style="color:#8b83a3;padding:4px 0;">Name</td><td>{name}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Company</td><td>{_g(customer,'company') or '—'}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Email</td><td>{_g(customer,'email')}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Phone</td><td>{_g(customer,'phone')}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Address</td><td>{addr or '—'}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Freight region</td><td>{_g(customer,'freight_region') or '—'}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Preferred contact</td><td>{_g(customer,'contact_pref') or '—'} ({_g(customer,'best_time') or 'any time'})</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Preferred payment</td><td><strong>{_g(customer,'payment_method') or '—'}</strong></td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;">Shipping method</td><td>{ship_label}{' + insurance' if insurance else ''}</td></tr>
  <tr><td style="color:#8b83a3;padding:4px 0;vertical-align:top;">Notes</td><td>{_g(customer,'notes') or '—'}</td></tr>
</table>
{_items_table(items, total, shipping, discount, coupon_code, insurance, ship_label, freight)}
<p style="color:#22c55e;font-size:13px;">✔ Customer confirmed 21+ and laboratory research use.</p>"""
    return await _send(OWNER_EMAIL, "NEW ORDER — CONTACT CUSTOMER",
                       _base_html("New order", body))
