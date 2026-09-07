# COA prompt — Oryvex Research certificates

Generates a **Certificate of Analysis** page in the same visual register as the
reference site's: a clean one-page lab document, letterhead at top, sample
summary, an analytical results table, storage/handling, and a certification
block at the bottom.

> **Read this first.** A COA is a factual lab record. Only publish one for
> material you have actually had tested, with the real lab's name, the real lot
> number and the real figures. A generated certificate is a **template** — fill
> it with your own data, or leave the product showing "COA pending". The site is
> built to show "COA pending" honestly and it costs you nothing to leave it
> there. Never publish a fabricated purity figure, lab name, signature or
> accreditation.

---

## The prompt (swap the ALL-CAPS fields)

```
A clean, professional one-page Certificate of Analysis document for a research
chemical supplier, rendered as a flat white A4 page, straight on, no perspective,
no shadow, no desk, no hands — the document fills the frame.

LAYOUT, top to bottom:

1. HEADER BAND, white with a thin crimson (#E33548) rule beneath it:
   - top left: a small circular crimson badge with a white letter "O", and
     beside it "ORYVEX RESEARCH" in crimson letter-spaced uppercase, with
     "RESEARCH LABORATORIES" small and grey underneath
   - top right, small grey text, right aligned:
     "oryvexresearch.com" and "support@oryvexresearch.com"
   - centred below: "CERTIFICATE OF ANALYSIS" in large bold black uppercase

2. Two thumbnail photographs of a clear glass vial with a crimson cap and a
   white "ORYVEX RESEARCH / COMPOUND-NAME" label, side by side at the left,
   small, on a light grey tile.

3. A two-column detail block, small grey labels with black values:
   Client: Oryvex Research      Accession #: ACCESSION
   Lot: LOT                     Search Code: CODE
   Received: RECEIVED-DATE      Reported: REPORTED-DATE

4. Section heading "SAMPLE SUMMARY" in small bold uppercase on a pale grey bar,
   then rows:
   Sample Name: COMPOUND-NAME    Purity: PURITY
   Appearance: APPEARANCE        Net Content: STRENGTH

5. Section heading "ANALYTICAL RESULTS" on a pale grey bar, then a bordered
   four-column table with the header row METHOD | SPECIFICATION | RESULT and
   rows:
   Identity Confirmation | LC-MS | Conforms | Conforms
   Purity | HPLC-UV | >= 99.0% | PURITY
   Water / Moisture | Karl Fischer | <= 5.0% | MOISTURE
   Related Substances | HPLC | <= 1.0% | RELATED
   Appearance | Visual Inspection | APPEARANCE | Conforms

6. Section heading "STORAGE & HANDLING" on a pale grey bar, then:
   Physical Form: APPEARANCE
   Storage Condition: Store refrigerated at 2-8 C (36-46 F). Protect from
   light, heat and moisture. Keep vial tightly sealed until use.
   For research use only. Not for human or veterinary use.

7. Section heading "CERTIFICATION" on a pale grey bar, then a two-column block:
   Testing Laboratory: LAB-NAME     Date of Analysis: ANALYSIS-DATE
   Lab / COA No.: COA-NUMBER        Retest / Expiry: EXPIRY-DATE
   with a blank ruled line labelled "Authorized By (QA)" and no signature drawn.

8. Footer rule in crimson with small grey centred text:
   "This certificate applies only to the lot identified above."

STYLE: crisp modern sans-serif throughout, black text on white, crimson used
only for the logo, the rules and the section accents. Generous margins,
everything precisely aligned, all text sharp and legible, high resolution,
document scan quality, 300 DPI, portrait.
```

**Negative prompt:**

```
blurry, warped text, misspelled text, lorem ipsum, handwriting, signature,
stamp, seal, holograms, watermark, photograph of a desk, hands, perspective,
tilt, drop shadow, dark background, colourful background, other brand names,
FDA logo, accreditation logos, ISO logos, barcodes
```

---

## Fields to fill in

| Field | Where it comes from |
|---|---|
| `COMPOUND-NAME` | product name, e.g. `BPC-157` |
| `STRENGTH` | the size on that vial, e.g. `10 mg` |
| `PURITY` | **your lab's actual figure**, e.g. `99.4%` |
| `APPEARANCE` | `White lyophilized powder` (GHK-Cu is blue) |
| `LOT` / `ACCESSION` / `CODE` | your own lot and accession references |
| `LAB-NAME` / `COA-NUMBER` | the lab that actually ran it |
| dates | received / reported / analysis / retest |

Leave `Authorized By (QA)` blank in the image — a generated signature on a lab
record is a forged document. Sign or counter-sign the real one out of band.

---

## Uploading a COA

Don't drop these into `static/coa/` by hand — use the admin panel so the
database points at them:

1. `http://127.0.0.1:8012/admin` → log in (`ADMIN_USERNAME` / `ADMIN_PASSWORD`
   from `.env`)
2. **Products + COA** tab → find the product → **Upload COA**
3. Attach the PDF/PNG/JPG and fill in the **lab name**

The product page flips from "COA pending" to "Third-party tested by <lab>", the
COA button opens it in the viewer, and it appears on `/coas`. **Remove COA**
takes it back down. Uploaded files survive restarts and catalog re-syncs.

Accepted: PDF, PNG, JPG, WEBP. A PDF is better than an image — it stays sharp
when a customer zooms in.
