# Re-render prompt — 20 vials with corrected strengths

Paste the whole block below into Grok as one message.

---

I need 20 separate product photographs. Every image is identical in style — only
the two label lines change. Generate them one at a time, in order, and label each
result with its number so I can match them up.

STYLE (identical for all 20):

Professional e-commerce product photograph of a single small pharmaceutical
glass vial standing upright, centred, shot straight on at eye level.

The vial: clear glass body, brushed silver aluminium flip-off cap with a deep
red plastic top, roughly 3cm tall, with a matte white paper label wrapped
around it.

The label, top to bottom, all text sharp and perfectly legible:
  - "ORYVEX RESEARCH" in small crimson letter-spaced uppercase at the top
  - a thin crimson rule beneath it
  - the COMPOUND NAME large, bold, black, uppercase, centred
  - the STRENGTH in white on a small crimson rounded badge directly below
  - "99% PURITY" and "FOR RESEARCH PURPOSES ONLY" in tiny grey uppercase
  - "ORYVEXRESEARCH.COM" in small crimson uppercase along the bottom edge

Lighting: soft even studio light from the upper left, gentle specular highlight
down the left side of the glass, soft contact shadow beneath the vial.
Background: flat light warm-grey seamless (#ECECEC), no gradient, no props,
no hands, no text outside the label.

Square 1:1, centred with generous margin, product occupies ~70% of the frame.
Photorealistic, commercial catalogue style, tack sharp, high detail, 4K.

Avoid: blurry or warped text, misspelled text, extra vials, hands, people,
syringes, needles, pills, other brand names, logos, watermarks, busy or
gradient background, tilted vial, cropped label.

THE 20 IMAGES — use exactly these two lines on each label:

 1.  ADAMAX               —  5MG
 2.  AHK-CU               —  100MG
 3.  CJC-1295 (NO DAC)    —  5MG
 4.  DSIP                 —  10MG
 5.  EPITHALON            —  10MG
 6.  FOXO4-DRI            —  10MG
 7.  GHK-CU               —  50MG
 8.  GLOW                 —  70MG
 9.  GLP-2                —  10MG
10.  GLP-3RT              —  5MG
11.  GLUTATHIONE          —  600MG
12.  IGF1-LR3             —  1MG
13.  IPAMORELIN           —  10MG
14.  KISSPEPTIN           —  10MG
15.  KLOW                 —  80MG
16.  KPV                  —  10MG
17.  N-ACETYL EPITALON    —  5MG
18.  NAD+                 —  500MG
19.  PEG-MGF              —  2MG
20.  WOLVERINE BLEND      —  5MG/5MG

Spelling matters — copy the names exactly as written, including the hyphens,
the "+" in NAD+, the brackets in CJC-1295 (NO DAC), and the slash in the
WOLVERINE BLEND strength (5MG/5MG, not 5MG).

---

Drop the results into `~/Downloads/oryvex/` and they get installed with:

```bash
cd /home/yenchi/labs/oryvex && python3 scripts/import_photos.py
```
