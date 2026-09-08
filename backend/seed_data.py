"""Oryvex Research — product catalog seed + idempotent sync.

PRODUCTS_SEED holds the full catalog across 3 categories. All copy is
RESEARCH-CONTEXT ONLY — mechanism/class descriptions and neutral lab notes
(molecular target, solubility, reconstitution, storage). There is intentionally
NO dosing, NO human-use language, and NO fabricated purity/lab data: `purity`
is the admin-editable placeholder and coa_file/coa_lab stay None until the
owner uploads a REAL certificate.

sync_products() upserts by slug:
  - update existing rows whose slug is in the seed
  - insert new rows
  - delete rows whose slug is no longer in the seed
  - commit once
"""
import json

from backend.models import Coupon, Product

# Example discount codes — OWNER-EDITABLE placeholders. Manage these in the
# admin "Coupons" tab; swap in your own real codes/values.
COUPONS_SEED: list[dict] = [
    {"code": "WELCOME10", "kind": "percent", "value": 10, "active": 1,
     "min_subtotal": 0, "description": "10% off first order (newsletter signup)"},
    {"code": "ORYVEX15", "kind": "percent", "value": 15, "active": 1,
     "min_subtotal": 0, "description": "15% off — affiliate / referral code"},
    {"code": "RESEARCH20", "kind": "percent", "value": 20, "active": 1,
     "min_subtotal": 0, "description": "20% off — newsletter / popup code"},
    {"code": "BULK40", "kind": "fixed", "value": 40, "active": 1,
     "min_subtotal": 350, "description": "$40 off orders over $350"},
]

# Shared placeholders (owner overrides per-product in the admin panel).
_PURITY = "≥99% HPLC"
_FORM_PEPTIDE = "Lyophilized powder"
_FORM_SOLUTION = "Sterile solution"
_STORE_COLD = "Store at -20°C"
_STORE_COOL = "Store refrigerated at 2–8°C; protect from light"
_STORE_DRY = "Store in a cool, dry place, away from light"
_IMG = "/static/images/placeholder.jpg"

# Reusable neutral lab notes (no dosing / no human-use instructions).
_NOTE_SOLUBILITY_PEP = (
    "Soluble in sterile or bacteriostatic water; some analogs benefit from "
    "mild acetic acid for reconstitution."
)
_NOTE_RECON = (
    "Reconstitute by adding solvent slowly down the vial wall and swirling "
    "gently — do not shake."
)
_NOTE_STORE_PEP = (
    "Store lyophilized powder at -20°C; keep any reconstituted solution "
    "refrigerated (2–8°C) for short-term laboratory use."
)
_NOTE_MIST = (
    "Supplied pre-measured in a metered mist applicator for bench handling; "
    "the applicator is a dispensing format only, not a use instruction."
)
_NOTE_STORE_MIST = (
    "Keep the applicator upright and refrigerated (2–8°C); protect from light "
    "and heat. Do not freeze once in solution."
)


def _pep_notes(target: str) -> list[str]:
    """Standard 4-bullet note block for a lyophilized peptide."""
    return [target, _NOTE_SOLUBILITY_PEP, _NOTE_RECON, _NOTE_STORE_PEP]


def _mist_notes(target: str) -> list[str]:
    """Standard 3-bullet note block for a mist-applicator format."""
    return [target, _NOTE_MIST, _NOTE_STORE_MIST]


# One dict per product. `variants` and `research_notes` are declared as native
# Python objects and serialized to JSON text by _normalize().
PRODUCTS_SEED: list[dict] = [
    {
        "slug": "5-amino-1mq",
        "name": "5-Amino-1MQ",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 39.99, "original_price": 47.99,
        "variants": [{"strength": "10mg", "price": 39.99}, {"strength": "50mg", "price": 119.99}],
        "description": "A small-molecule NNMT inhibitor studied in metabolic and adipocyte research.",
        "research_notes": _pep_notes(
            "Molecular target: nicotinamide N-methyltransferase (NNMT) inhibition in in vitro metabolic assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "adamax",
        "name": "Adamax",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 65.99, "original_price": 70.99,
        "variants": [{"strength": "5mg", "price": 65.99}],
        "description": "A synthetic nootropic-class research peptide used as a reference compound in neuropeptide studies.",
        "research_notes": _pep_notes(
            "Molecular target: neuropeptide signalling pathways examined in in vitro neuronal models."),
        "in_stock": True, "badge": "New", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "ahk-cu",
        "name": "AHK-Cu",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 89.99, "original_price": 107.99,
        "variants": [{"strength": "100mg", "price": 89.99}],
        "description": "A copper-binding tripeptide complex used as a reference compound in cosmetic and matrix-biology research.",
        "research_notes": _pep_notes(
            "Molecular target: copper-peptide complex studied in in vitro follicle and matrix assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "ara-290",
        "name": "ARA-290",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 67.99, "original_price": 81.99,
        "variants": [{"strength": "10mg", "price": 67.99}, {"strength": "50mg", "price": 159.99}],
        "description": "An 11-amino-acid erythropoietin-derived peptide studied in tissue-protection research.",
        "research_notes": _pep_notes(
            "Molecular target: the innate repair receptor (IRR) complex in in vitro studies."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "bacteriostatic-water",
        "name": "Bacteriostatic Water",
        "category": "research-peptides",
        "cas_number": "7732-18-5",
        "molecular_formula": "H2O",
        "purity": "USP grade", "form": "Sterile water with 0.9% benzyl alcohol", "storage": _STORE_DRY,
        "price": 19.99, "original_price": 29.99,
        "variants": [{"strength": "10ml", "price": 19.99}, {"strength": "20ml", "price": 37.99}, {"strength": "30ml", "price": 55.99}],
        "description": "Sterile water containing 0.9% benzyl alcohol as a bacteriostatic preservative \u2014 the standard solvent for reconstituting lyophilized research peptides.",
        "research_notes": [
            "Use as the reconstitution solvent for lyophilized research peptides in laboratory work.",
            _NOTE_RECON,
            "Store at room temperature in a cool, dry place away from light."
        ],
        "in_stock": True, "badge": "Lab Essential", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "bpc-157",
        "name": "BPC-157",
        "category": "research-peptides",
        "cas_number": "137525-51-0",
        "molecular_formula": "C62H98N16O22",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 44.99, "original_price": 53.99,
        "variants": [{"strength": "10mg", "price": 44.99}],
        "description": "A pentadecapeptide gastric fragment used widely in angiogenesis and tissue-repair research.",
        "research_notes": _pep_notes(
            "Molecular target: angiogenic and repair signalling examined in in vitro wound models."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "bpc-157-mist-applicator",
        "name": "BPC-157 \u2014 Mist Applicator",
        "category": "mist-applicators",
        "cas_number": "137525-51-0",
        "molecular_formula": "C62H98N16O22",
        "purity": _PURITY, "form": _FORM_SOLUTION, "storage": _STORE_COOL,
        "price": 89.99, "original_price": 107.99,
        "variants": [{"strength": "10mg", "price": 89.99}],
        "description": "A pentadecapeptide gastric fragment used widely in angiogenesis and tissue-repair research, supplied in a metered mist applicator for laboratory handling.",
        "research_notes": _mist_notes(
            "Molecular target: angiogenic and repair signalling examined in in vitro wound models."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "cagrilintide",
        "name": "Cagrilintide",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 119.99, "original_price": 143.99,
        "variants": [{"strength": "10mg", "price": 119.99}],
        "description": "A long-acting amylin analog studied in metabolic and energy-homeostasis research.",
        "research_notes": _pep_notes(
            "Molecular target: amylin/calcitonin receptor agonism in in vitro receptor-binding studies."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "cjc-1295-no-dac",
        "name": "CJC-1295 (No DAC)",
        "category": "research-peptides",
        "cas_number": "863288-34-0",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 39.99, "original_price": 47.99,
        "variants": [{"strength": "5mg", "price": 39.99}, {"strength": "10mg", "price": 64.99}],
        "description": "A growth-hormone-releasing hormone analog (modified GRF 1-29) used in secretagogue research.",
        "research_notes": _pep_notes(
            "Molecular target: GHRH receptor agonism in in vitro pituitary-cell assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "cjc-1295-ipamorelin",
        "name": "CJC-1295 / Ipamorelin (No DAC)",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 74.99, "original_price": 89.99,
        "variants": [{"strength": "10mg", "price": 74.99}],
        "description": "A combined GHRH-analog and ghrelin-receptor agonist preparation for comparative secretagogue research.",
        "research_notes": _pep_notes(
            "Composition: two-peptide research blend. Handle as a single preparation; see the certificate for component identity."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "dsip",
        "name": "DSIP",
        "category": "research-peptides",
        "cas_number": "62568-57-4",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 59.99, "original_price": 71.99,
        "variants": [{"strength": "10mg", "price": 59.99}],
        "description": "Delta sleep-inducing peptide, a nonapeptide used as a reference compound in neuroendocrine research.",
        "research_notes": _pep_notes(
            "Molecular target: neuroendocrine signalling pathways examined in in vitro models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "dsip-mist-applicator",
        "name": "DSIP \u2014 Mist Applicator",
        "category": "mist-applicators",
        "cas_number": "62568-57-4",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_SOLUTION, "storage": _STORE_COOL,
        "price": 74.99, "original_price": 89.99,
        "variants": [{"strength": "5mg", "price": 74.99}],
        "description": "Delta sleep-inducing peptide, a nonapeptide used as a reference compound in neuroendocrine research, supplied in a metered mist applicator for laboratory handling.",
        "research_notes": _mist_notes(
            "Molecular target: neuroendocrine signalling pathways examined in in vitro models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "epithalon",
        "name": "Epithalon",
        "category": "research-peptides",
        "cas_number": "307297-39-8",
        "molecular_formula": "C14H22N4O9",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 54.99, "original_price": 65.99,
        "variants": [{"strength": "10mg", "price": 54.99}, {"strength": "40mg", "price": 99.99}],
        "description": "A synthetic tetrapeptide studied in telomerase and cellular-ageing research.",
        "research_notes": _pep_notes(
            "Molecular target: telomerase activity examined in in vitro cell-culture assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "foxo4-dri",
        "name": "FOXO4-DRI",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 179.99, "original_price": 215.99,
        "variants": [{"strength": "10mg", "price": 179.99}],
        "description": "A retro-inverso FOXO4 peptide used as a reference compound in cellular-senescence research.",
        "research_notes": _pep_notes(
            "Molecular target: the FOXO4\u2013p53 interaction studied in in vitro senescence models."),
        "in_stock": True, "badge": "New", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "ghk-cu",
        "name": "GHK-Cu",
        "category": "research-peptides",
        "cas_number": "89030-95-5",
        "molecular_formula": "C14H22CuN6O4",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 44.99, "original_price": 53.99,
        "variants": [{"strength": "50mg", "price": 44.99}, {"strength": "100mg", "price": 74.99}],
        "description": "A copper-binding tripeptide used widely as a reference compound in matrix and cosmetic research.",
        "research_notes": _pep_notes(
            "Molecular target: copper-peptide complex studied in in vitro collagen and matrix assays."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "glow",
        "name": "GLOW",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 100.00, "original_price": 120.00,
        "variants": [{"strength": "70mg", "price": 100.00}],
        "description": "A multi-component research blend supplied as a single lyophilized preparation for comparative in vitro work.",
        "research_notes": _pep_notes(
            "Composition: multi-peptide research blend. Handle as a single preparation; see the certificate for component identity."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "glp-1t",
        "name": "GLP-1T",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 59.99, "original_price": 71.99,
        "variants": [{"strength": "10mg", "price": 59.99}],
        "description": "A GLP-1 receptor agonist reference compound used in metabolic research.",
        "research_notes": _pep_notes(
            "Molecular target: GLP-1 receptor agonism in in vitro receptor studies."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "glp-2",
        "name": "GLP-2",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 49.99, "original_price": 82.99,
        "variants": [{"strength": "10mg", "price": 49.99}],
        "description": "A glucagon-like peptide-2 analog studied in intestinal epithelial and barrier-function research.",
        "research_notes": _pep_notes(
            "Molecular target: GLP-2 receptor signalling examined in in vitro epithelial models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "glp-3rt",
        "name": "GLP-3RT",
        "category": "research-peptides",
        "cas_number": "2381089-83-2",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 54.99, "original_price": 65.99,
        "variants": [{"strength": "5mg", "price": 54.99}, {"strength": "10mg", "price": 79.99}, {"strength": "20mg", "price": 129.99}, {"strength": "30mg", "price": 149.99}],
        "description": "A triple GIP/GLP-1/glucagon receptor agonist studied in metabolic and energy-homeostasis research.",
        "research_notes": _pep_notes(
            "Molecular target: agonism at GIP, GLP-1 and glucagon receptors in in vitro receptor studies."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "glutathione",
        "name": "Glutathione",
        "category": "research-peptides",
        "cas_number": "70-18-8",
        "molecular_formula": "C10H17N3O6S",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 40.00, "original_price": 48.00,
        "variants": [{"strength": "600mg", "price": 40.00}, {"strength": "1500mg", "price": 89.99}],
        "description": "A tripeptide thiol of glutamic acid, cysteine and glycine, used as a primary endogenous antioxidant reference in redox research.",
        "research_notes": _pep_notes(
            "Molecular target: cellular redox homeostasis and Phase II pathways in in vitro assays."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "igf1-lr3",
        "name": "IGF1-LR3",
        "category": "research-peptides",
        "cas_number": "946870-92-4",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 89.99, "original_price": 107.99,
        "variants": [{"strength": "1mg", "price": 89.99}],
        "description": "A long-arginine IGF-1 analog with reduced binding-protein affinity, used widely in cell-culture research.",
        "research_notes": _pep_notes(
            "Molecular target: IGF-1 receptor signalling in in vitro proliferation and differentiation assays."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "ipamorelin",
        "name": "Ipamorelin",
        "category": "research-peptides",
        "cas_number": "170851-70-4",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 74.99, "original_price": 89.99,
        "variants": [{"strength": "10mg", "price": 74.99}],
        "description": "A selective pentapeptide ghrelin-receptor agonist used in growth-hormone secretagogue research.",
        "research_notes": _pep_notes(
            "Molecular target: GHS-R1a agonism in in vitro pituitary-cell assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "kisspeptin",
        "name": "Kisspeptin",
        "category": "research-peptides",
        "cas_number": "374675-21-5",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 34.99, "original_price": 41.99,
        "variants": [{"strength": "10mg", "price": 34.99}],
        "description": "A decapeptide fragment used as a reference compound in reproductive neuroendocrinology research.",
        "research_notes": _pep_notes(
            "Molecular target: KISS1R (GPR54) signalling in in vitro receptor assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "klow",
        "name": "KLOW",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 112.00, "original_price": 126.00,
        "variants": [{"strength": "80mg", "price": 112.00}],
        "description": "A multi-component research blend supplied as a single lyophilized preparation for comparative in vitro work.",
        "research_notes": _pep_notes(
            "Composition: multi-peptide research blend. Handle as a single preparation; see the certificate for component identity."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "kpv",
        "name": "KPV",
        "category": "research-peptides",
        "cas_number": "67247-12-5",
        "molecular_formula": "C16H29N5O4",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 44.99, "original_price": 53.99,
        "variants": [{"strength": "10mg", "price": 44.99}, {"strength": "30mg", "price": 119.99}],
        "description": "A tripeptide alpha-MSH fragment studied in inflammatory-signalling and epithelial research.",
        "research_notes": _pep_notes(
            "Molecular target: NF-\u03baB-associated inflammatory signalling in in vitro epithelial models."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "kpv-mist-applicator",
        "name": "KPV \u2014 Mist Applicator",
        "category": "mist-applicators",
        "cas_number": "67247-12-5",
        "molecular_formula": "C16H29N5O4",
        "purity": _PURITY, "form": _FORM_SOLUTION, "storage": _STORE_COOL,
        "price": 79.99, "original_price": 95.99,
        "variants": [{"strength": "10mg", "price": 79.99}],
        "description": "A tripeptide alpha-MSH fragment studied in inflammatory-signalling and epithelial research, supplied in a metered mist applicator for laboratory handling.",
        "research_notes": _mist_notes(
            "Molecular target: NF-\u03baB-associated inflammatory signalling in in vitro epithelial models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "ll-37",
        "name": "LL-37",
        "category": "research-peptides",
        "cas_number": "154947-66-7",
        "molecular_formula": "C205H340N60O53",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 89.99, "original_price": 107.99,
        "variants": [{"strength": "5mg", "price": 89.99}],
        "description": "A human cathelicidin-derived antimicrobial peptide used as a reference standard in innate-immunity research.",
        "research_notes": _pep_notes(
            "Molecular target: cathelicidin/innate-immune pathways in in vitro antimicrobial assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "mots-c",
        "name": "MOTS-C",
        "category": "research-peptides",
        "cas_number": "1627580-64-6",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 54.99, "original_price": 77.99,
        "variants": [{"strength": "10mg", "price": 54.99}, {"strength": "40mg", "price": 139.99}],
        "description": "A mitochondrial-derived peptide studied in metabolic regulation and mitochondrial-signalling research.",
        "research_notes": _pep_notes(
            "Molecular target: AMPK-associated metabolic signalling in in vitro assays."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "mt-1",
        "name": "MT-1",
        "category": "research-peptides",
        "cas_number": "75921-69-6",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 49.99, "original_price": 83.99,
        "variants": [{"strength": "10mg", "price": 49.99}],
        "description": "A synthetic alpha-MSH analog used as a reference compound in melanocortin-pathway research.",
        "research_notes": _pep_notes(
            "Molecular target: MC1R melanocortin receptor agonism in in vitro pigmentation assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "mt-2",
        "name": "MT-2",
        "category": "research-peptides",
        "cas_number": "121062-08-6",
        "molecular_formula": "C50H69N15O9",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 40.99, "original_price": 49.99,
        "variants": [{"strength": "10mg", "price": 40.99}],
        "description": "A synthetic melanocortin analog used as a reference compound in melanocortin-pathway research.",
        "research_notes": _pep_notes(
            "Molecular target: melanocortin receptor agonism in in vitro pigmentation-pathway assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "mt-2-mist-applicator",
        "name": "MT-2 \u2014 Mist Applicator",
        "category": "mist-applicators",
        "cas_number": "121062-08-6",
        "molecular_formula": "C50H69N15O9",
        "purity": _PURITY, "form": _FORM_SOLUTION, "storage": _STORE_COOL,
        "price": 99.99, "original_price": 119.99,
        "variants": [{"strength": "10mg", "price": 99.99}],
        "description": "A synthetic melanocortin analog used as a reference compound in melanocortin-pathway research, supplied in a metered mist applicator for laboratory handling.",
        "research_notes": _mist_notes(
            "Molecular target: melanocortin receptor agonism in in vitro pigmentation-pathway assays."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "n-acetyl-epitalon",
        "name": "N-Acetyl Epitalon",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 64.99, "original_price": 77.99,
        "variants": [{"strength": "5mg", "price": 64.99}],
        "description": "An N-terminally acetylated Epitalon analog used in telomerase and cellular-ageing research.",
        "research_notes": _pep_notes(
            "Molecular target: telomerase activity examined in in vitro cell-culture assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "nad-plus",
        "name": "NAD+",
        "category": "research-peptides",
        "cas_number": "53-84-9",
        "molecular_formula": "C21H27N7O14P2",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 74.99, "original_price": 89.99,
        "variants": [{"strength": "500mg", "price": 74.99}, {"strength": "1000mg", "price": 129.99}],
        "description": "A pyridine dinucleotide coenzyme central to redox reactions and sirtuin research.",
        "research_notes": _pep_notes(
            "Molecular target: NAD+-dependent enzymes (sirtuins, PARPs) in in vitro assays."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "peg-mgf",
        "name": "PEG-MGF",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 99.99, "original_price": 132.99,
        "variants": [{"strength": "2mg", "price": 99.99}],
        "description": "A PEGylated mechano-growth-factor analog used in myogenic and tissue-repair signalling research.",
        "research_notes": _pep_notes(
            "Molecular target: IGF-1Ec splice-variant signalling in in vitro myoblast models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "pinealon",
        "name": "Pinealon",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 54.99, "original_price": 66.99,
        "variants": [{"strength": "10mg", "price": 54.99}],
        "description": "A synthetic tripeptide bioregulator used as a reference compound in neuroprotection research.",
        "research_notes": _pep_notes(
            "Molecular target: neuronal signalling pathways examined in in vitro models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "pt-141",
        "name": "PT-141",
        "category": "research-peptides",
        "cas_number": "189691-06-3",
        "molecular_formula": "C50H68N14O10",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 69.99, "original_price": 83.99,
        "variants": [{"strength": "10mg", "price": 69.99}],
        "description": "A melanocortin receptor agonist used as a reference compound in melanocortin-pathway research.",
        "research_notes": _pep_notes(
            "Molecular target: MC1R/MC4R melanocortin receptor agonism in in vitro receptor assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "pt-141-mist-applicator",
        "name": "PT-141 \u2014 Mist Applicator",
        "category": "mist-applicators",
        "cas_number": "189691-06-3",
        "molecular_formula": "C50H68N14O10",
        "purity": _PURITY, "form": _FORM_SOLUTION, "storage": _STORE_COOL,
        "price": 99.99, "original_price": 149.99,
        "variants": [{"strength": "10mg", "price": 99.99}],
        "description": "A melanocortin receptor agonist used as a reference compound in melanocortin-pathway research, supplied in a metered mist applicator for laboratory handling.",
        "research_notes": _mist_notes(
            "Molecular target: MC1R/MC4R melanocortin receptor agonism in in vitro receptor assays."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "selank",
        "name": "Selank",
        "category": "research-peptides",
        "cas_number": "129954-34-3",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 39.99, "original_price": 47.99,
        "variants": [{"strength": "10mg", "price": 39.99}],
        "description": "A synthetic heptapeptide tuftsin analog used as a reference compound in neuropeptide research.",
        "research_notes": _pep_notes(
            "Molecular target: neuropeptide and GABAergic signalling in in vitro models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "selank-mist-applicator",
        "name": "Selank \u2014 Mist Applicator",
        "category": "mist-applicators",
        "cas_number": "129954-34-3",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_SOLUTION, "storage": _STORE_COOL,
        "price": 64.99, "original_price": 77.99,
        "variants": [{"strength": "5mg", "price": 64.99}, {"strength": "10mg", "price": 109.99}],
        "description": "A synthetic heptapeptide tuftsin analog used as a reference compound in neuropeptide research, supplied in a metered mist applicator for laboratory handling.",
        "research_notes": _mist_notes(
            "Molecular target: neuropeptide and GABAergic signalling in in vitro models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "semax",
        "name": "Semax",
        "category": "research-peptides",
        "cas_number": "80714-61-0",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 39.99, "original_price": 47.99,
        "variants": [{"strength": "10mg", "price": 39.99}],
        "description": "A synthetic ACTH(4-10) fragment analog used as a reference compound in neuropeptide research.",
        "research_notes": _pep_notes(
            "Molecular target: BDNF-associated neurotrophic signalling in in vitro models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "semax-mist-applicator",
        "name": "Semax \u2014 Mist Applicator",
        "category": "mist-applicators",
        "cas_number": "80714-61-0",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_SOLUTION, "storage": _STORE_COOL,
        "price": 64.99, "original_price": 77.99,
        "variants": [{"strength": "5mg", "price": 64.99}, {"strength": "10mg", "price": 109.99}],
        "description": "A synthetic ACTH(4-10) fragment analog used as a reference compound in neuropeptide research, supplied in a metered mist applicator for laboratory handling.",
        "research_notes": _mist_notes(
            "Molecular target: BDNF-associated neurotrophic signalling in in vitro models."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "slu-pp-332",
        "name": "SLU-PP-332",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 134.99, "original_price": 167.90,
        "variants": [{"strength": "10mg", "price": 134.99}],
        "description": "An ERR (estrogen-related receptor) agonist studied in mitochondrial and exercise-mimetic metabolic research.",
        "research_notes": _pep_notes(
            "Molecular target: pan-ERR agonism in in vitro metabolic and mitochondrial-biogenesis assays."),
        "in_stock": True, "badge": "New", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "ss31",
        "name": "SS-31",
        "category": "research-peptides",
        "cas_number": "736992-21-5",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 55.99, "original_price": 65.99,
        "variants": [{"strength": "10mg", "price": 55.99}, {"strength": "50mg", "price": 159.99}],
        "description": "A mitochondria-targeting tetrapeptide studied in cardiolipin binding and bioenergetics research.",
        "research_notes": _pep_notes(
            "Molecular target: cardiolipin on the inner mitochondrial membrane, in in vitro bioenergetics assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "tb-500",
        "name": "TB-500",
        "category": "research-peptides",
        "cas_number": "77591-33-4",
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 44.99, "original_price": 53.99,
        "variants": [{"strength": "10mg", "price": 44.99}],
        "description": "A synthetic thymosin beta-4 fragment used widely in actin-binding and tissue-repair research.",
        "research_notes": _pep_notes(
            "Molecular target: actin sequestration and repair signalling in in vitro assays."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "tesamorelin",
        "name": "Tesamorelin",
        "category": "research-peptides",
        "cas_number": "218949-48-5",
        "molecular_formula": "C221H366N72O67S",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 50.00, "original_price": 60.00,
        "variants": [{"strength": "2mg", "price": 50.00}, {"strength": "5mg", "price": 65.00}, {"strength": "10mg", "price": 85.00}, {"strength": "20mg", "price": 139.00}],
        "description": "A stabilized growth-hormone-releasing hormone analog used in secretagogue research.",
        "research_notes": _pep_notes(
            "Molecular target: GHRH receptor agonism in in vitro pituitary-cell assays."),
        "in_stock": True, "badge": None, "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "thymosin-alpha-1",
        "name": "Thymosin Alpha-1",
        "category": "research-peptides",
        "cas_number": "62304-98-7",
        "molecular_formula": "C129H215N33O55",
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 119.99, "original_price": 191.99,
        "variants": [{"strength": "10mg", "price": 119.99}],
        "description": "A 28-amino-acid thymic peptide used as a reference compound in immunological signalling research.",
        "research_notes": _pep_notes(
            "Molecular target: thymic peptide signalling pathways in in vitro immunology models."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "wolverine-blend",
        "name": "Wolverine Blend",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 59.99, "original_price": 71.99,
        "variants": [{"strength": "5mg/5mg", "price": 59.99}, {"strength": "10mg/10mg", "price": 89.99}],
        "description": "A multi-component repair-research blend supplied as a single lyophilized preparation.",
        "research_notes": _pep_notes(
            "Composition: multi-peptide research blend. Handle as a single preparation; see the certificate for component identity."),
        "in_stock": True, "badge": "Best Seller", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
    {
        "slug": "hgh-kits",
        "name": "HGH Kits",
        "category": "research-peptides",
        "cas_number": None,
        "molecular_formula": None,
        "purity": _PURITY, "form": _FORM_PEPTIDE, "storage": _STORE_COLD,
        "price": 199.99, "original_price": 259.99,
        "variants": [{"strength": "100IU (10x10IU)", "price": 199.99}],
        "description": "A 191-amino-acid recombinant somatropin preparation "
                       "supplied as a 10-vial kit for laboratory reference use.",
        "research_notes": _pep_notes(
            "Molecular target: growth hormone receptor signalling examined in "
            "in vitro cell-culture assays."),
        "in_stock": True, "badge": "New", "image": _IMG,
        "coa_file": None, "coa_lab": None,
    },
]


# Point every product at its generated vial image (scripts/gen_vials.py).
# Falls back to the shared placeholder only if a vial PNG hasn't been generated.
for _p in PRODUCTS_SEED:
    _p["image"] = f"/static/images/vials/{_p['slug']}.png"


# Columns that are stored as JSON text in the DB.
_JSON_FIELDS = ("variants", "research_notes")

# Columns the admin owns via the panel (COA upload). These are NEVER overwritten
# on an EXISTING row by a restart/sync — otherwise an uploaded COA would be lost
# every time the catalog is re-synced.
_ADMIN_FIELDS = ("coa_file", "coa_lab")


def _normalize(row: dict) -> dict:
    """Return a copy of `row` with JSON fields serialized to text."""
    out = dict(row)
    for field in _JSON_FIELDS:
        val = out.get(field)
        if val is not None and not isinstance(val, str):
            out[field] = json.dumps(val)
    # normalize booleans → integer flags used by the model
    if "in_stock" in out:
        out["in_stock"] = 1 if out["in_stock"] else 0
    return out


def sync_products(db) -> None:
    """Idempotently sync PRODUCTS_SEED into the products table."""
    seed_by_slug = {r["slug"]: _normalize(r) for r in PRODUCTS_SEED}
    seed_slugs = set(seed_by_slug)

    existing = {p.slug: p for p in db.query(Product).all()}

    # delete rows no longer present in the seed
    for slug, product in existing.items():
        if slug not in seed_slugs:
            db.delete(product)

    # update existing / insert new
    for slug, data in seed_by_slug.items():
        if slug in existing:
            product = existing[slug]
            for key, value in data.items():
                if key in _ADMIN_FIELDS:
                    continue  # preserve admin-managed COA fields
                setattr(product, key, value)
        else:
            db.add(Product(**data))

    db.commit()


def sync_coupons(db) -> None:
    """Insert seed coupons that don't exist yet (by code).

    Unlike products, coupons are only INSERTED when missing — never updated or
    deleted here — so the owner can freely edit/disable codes in the admin panel
    without a restart clobbering or re-adding them.
    """
    existing = {c.code for c in db.query(Coupon.code).all()}
    changed = False
    for row in COUPONS_SEED:
        code = row["code"].strip().upper()
        if code in existing:
            continue
        data = dict(row)
        data["code"] = code
        data["active"] = 1 if data.get("active", 1) else 0
        db.add(Coupon(**data))
        changed = True
    if changed:
        db.commit()
