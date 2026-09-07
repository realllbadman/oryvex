# Product image prompt — Oryvex Research vials

Use this with Grok (or any image model: Midjourney, DALL·E, Ideogram, Flux).
It describes **our own** vial: our brand name, our label design, our colours.
Do not reference another company's product, packaging, or photographs.

---

## The prompt (copy/paste, swap the two ALL-CAPS fields)

```
Professional e-commerce product photograph of a single small pharmaceutical
glass vial standing upright, centred, shot straight on at eye level.

The vial: clear glass body, crimson aluminium flip-off cap, roughly 3cm tall,
with a matte white paper label wrapped around it.

The label, top to bottom, all text sharp and perfectly legible:
  - "ORYVEX RESEARCH" in small crimson letter-spaced uppercase at the top
  - a thin crimson rule beneath it
  - "COMPOUND-NAME" large, bold, black, uppercase, centred
  - "STRENGTH" in white on a small crimson rounded badge directly below
  - "99% PURITY" and "FOR RESEARCH PURPOSES ONLY" in tiny grey uppercase
  - "ORYVEXRESEARCH.COM" in small crimson uppercase along the bottom edge

Lighting: soft even studio light from the upper left, gentle specular highlight
down the left side of the glass, soft contact shadow beneath the vial.
Background: flat light warm-grey seamless (#ECECEC), no gradient, no props,
no hands, no text outside the label.

Square 1:1, centred with generous margin, product occupies ~70% of the frame.
Photorealistic, commercial catalogue style, tack sharp, high detail, 4K.
```

**Negative prompt** (where supported):

```
blurry, warped text, misspelled text, extra vials, hands, people, syringes,
needles, pills, medical claims, dosage instructions, other brand names, logos,
watermarks, busy background, gradient background, reflections of a room,
tilted vial, cropped label
```

---

## Filling in the two fields

`COMPOUND-NAME` and `STRENGTH` come straight from the catalog — use the
product's name and its **first** (smallest) size:

| COMPOUND-NAME | STRENGTH |
|---|---|
| BPC-157 | 10MG |
| GLP-3RT | 5MG |
| GLUTATHIONE | 600MG |
| TESAMORELIN | 2MG |
| BACTERIOSTATIC WATER | 10ML |
| … | … |

`python3 -c "import backend.seed_data as s; [print(p['name'].upper(), '|', p['variants'][0]['strength'].upper()) for p in s.PRODUCTS_SEED]"`
prints the whole list.

### For the 7 mist applicators

Replace the vial sentence with:

```
The applicator: white opaque plastic bottle with a fine-mist nasal spray pump
and a clear protective over-cap, roughly 8cm tall, same white label design.
```

and set `COMPOUND-NAME` to e.g. `PT-141` with a second label line reading
`MIST APPLICATOR` in small black uppercase.

---

## Getting them into the site

Save each as `<slug>.png` (transparent or #ECECEC background both work — the
card panel is #ECECEC) into `static/images/vials/`. The slug is the URL segment,
e.g. `bpc-157-mist-applicator.png`. Existing generated art is overwritten.

```bash
python3 -c "import backend.seed_data as s; [print(p['slug']) for p in s.PRODUCTS_SEED]"
```

`scripts/import_photos.py` will background-remove and install real photos by
slug if you'd rather drop in unedited files.

---

## Two rules to keep

1. **Never** ask the model for another company's vial, label, or photograph, and
   never upload their product images as a reference. Describe ours.
2. Keep the label free of dosing, treatment, or human-use language — "FOR
   RESEARCH PURPOSES ONLY" stays on every one.

---

# About-section image prompt

The photo beside "About Oryvex Research" on the homepage. One landscape image,
saved as `static/images/about-lab.jpg`. Generate it the same way as the vials.

```
Professional editorial photograph of a scientist working at a laboratory bench,
shot at eye level with a shallow depth of field.

Subject: a researcher in a white lab coat and blue nitrile gloves, framed from
the chest down so the face is not the subject — hands in focus, holding a clear
glass test tube of pale amber liquid over a rack of tubes, the other hand
steadying a pipette. Calm, deliberate, unhurried.

Setting: a clean modern research lab. A rack of test tubes and two Erlenmeyer
flasks sit on a white bench in the mid-ground; racks, bottles and equipment blur
softly into the background. Neutral white and steel surfaces, one small crimson
accent — a red cap or a red-labelled bottle — to tie into the brand.

Light: soft, bright, diffused daylight from the left, gentle falloff to the
right, no harsh shadows, no colour cast.

Composition: landscape 4:3, subject slightly right of centre, generous clean
space, background falling away out of focus.

Photorealistic editorial stock photography, natural colour, tack-sharp on the
hands and glassware, high resolution, 4K.
```

**Negative prompt:**

```
face closeup, portrait, eye contact, cartoon, illustration, 3D render, CGI,
plastic look, distorted hands, extra fingers, warped glassware, text, labels
with writing, logos, watermark, syringes, needles, pills, medical procedure,
patient, hospital, dark background, heavy colour grade, fisheye
```

Save it as `static/images/about-lab.jpg` (landscape, roughly 1400×1050 or any
4:3). It's cache-busted, so a normal refresh picks it up.

Two things to keep it honest: don't caption it as your own facility, and avoid
anything that reads as a clinical or patient setting — this is a research
supplier, not a clinic.
