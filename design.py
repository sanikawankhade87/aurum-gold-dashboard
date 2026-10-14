"""Design tokens shared by the app (and mirrored in the notebook).

Three fixed mappings, enforced everywhere:
  entity -> hue          (one colour per country on every panel)
  epistemic status -> line style  (solid = reported, dashed = estimated)
  data class -> mark     (lines = levels, bars = period changes, areas = composition)
"""

# AURUM neon-noir palette (adapted from the original light "ledger" theme)
PAPER = "rgba(0,0,0,0)"   # charts sit on the page's dark gradient
INK   = "#f3ead2"
FAINT = "#a59c84"
GHOST = "#5c5240"
GOLD  = "#FFC93C"   # reserved for the price of gold itself

HUES = {
    "China":     "#FF4D5E",
    "China + HK":"#FF4D5E",
    "Russia":    "#4DA3FF",
    "Iran":      "#3DDC97",
    "India":     "#FF9F1C",
    "Turkey":    "#C77DFF",
    "UK + US":   "#8FA6BF",
    "West":      "#8FA6BF",
    "UAE + Gulf":"#6E6A60",
    "other":     "#4A4639",
}
REST = "#7A735F"          # rest-of-world grey (figure-ground)

def hue(entity: str) -> str:
    return HUES.get(entity, REST)

SOLID = None              # plotly default dash
DASH  = "dash"            # estimated / inferred series

# Discrete, political demand shocks -- drawn as vertical rules on every time axis
EVENTS = [
    ("2022-02-28", "freeze"),
    ("2022-06-26", "G7 ban"),
    ("2025-06-13", "Iran war"),
    ("2025-11-01", "CBR sells"),
    ("2026-05-15", "escalation"),
]

# Mine replenishment reference rates, tonnes per month (USGS-derived, hand-entered yearly)
MINE_TOTAL_TPM   = 300    # ~3,600 t/yr global mine supply
MINE_WESTERN_TPM = 200    # ~2,400 t/yr that enters the Western circuit
