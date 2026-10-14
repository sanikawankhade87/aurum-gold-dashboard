"""Gold stock-transfer monitor — desktop build.

Run:  python ingest.py --synthetic   (once, or --all for live data)
      streamlit run app.py

Design contract (reasoning in the companion notebook):
  - solid = reported, dashed = estimated; one colour per country everywhere
  - the same event rules on every time axis; labels only on the dominant charts
  - one bordered region (the KPI strip); whitespace does all other grouping
  - one dominant chart per tab: P1 carries Declared, P4 carries Inferred
"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

import design as dz

DATA = Path(__file__).parent / "data"
if not DATA.exists():                      # CSVs uploaded flat, next to app.py
    DATA = Path(__file__).parent

st.set_page_config(page_title="AURUM | Gold stock-transfer monitor", page_icon="🪙",
                   layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- chrome/css --
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Archivo:wght@400;500;600&display=swap');
html, body, [class*="css"], .stMarkdown, p, li {
  font-family: 'Archivo', system-ui, sans-serif; font-variant-numeric: tabular-nums; }
.stApp {
  background:
    radial-gradient(1100px 560px at 12% -8%, rgba(255,201,60,.16), transparent 60%),
    radial-gradient(900px 520px at 100% 15%, rgba(255,120,40,.10), transparent 60%),
    radial-gradient(800px 500px at 50% 120%, rgba(120,80,255,.10), transparent 60%),
    #07060a;
  color: #f3ead2; }
.stApp::before { content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image: radial-gradient(rgba(255,201,60,.18) 1px, transparent 1px);
  background-size: 34px 34px; mask-image: linear-gradient(to bottom, transparent, black 30%, transparent); }
.block-container { max-width: 1220px; padding-top: 1.4rem; padding-bottom: 3rem; position: relative; z-index: 1; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }
h1, h3 { font-family: 'Cinzel', serif !important; letter-spacing: .03em; }
h3 { font-size: 1.3rem; margin-bottom: 0; color: #ffe39a; text-shadow: 0 0 14px rgba(255,201,60,.35); }
.stCaption, [data-testid="stCaptionContainer"] { color: #a59c84; }
/* brand bar */
.brandbar { display:flex; align-items:center; justify-content:space-between; gap: 16px;
  padding: 14px 22px; border-radius: 18px; margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(40,30,8,.75), rgba(12,10,6,.75)); backdrop-filter: blur(8px);
  border: 1px solid rgba(255,201,60,.45);
  box-shadow: 0 0 26px rgba(255,201,60,.22), inset 0 0 22px rgba(255,201,60,.08); }
.brand { display:flex; align-items:center; gap: 14px; }
.coin { animation: flip 6s ease-in-out infinite; transform-style: preserve-3d;
  filter: drop-shadow(0 0 10px rgba(255,201,60,.8)); }
@keyframes flip { 0%,100% { transform: rotateY(0deg); } 50% { transform: rotateY(180deg); } }
.bname { font-family: 'Cinzel', serif; font-weight: 800; font-size: 30px; letter-spacing: .28em;
  background: linear-gradient(90deg, #fff1c1, #FFC93C 40%, #ff9d2e); -webkit-background-clip: text; color: transparent;
  filter: drop-shadow(0 0 12px rgba(255,201,60,.45)); }
.bsub { font-size: 11.5px; letter-spacing: .2em; text-transform: uppercase; color: #a59c84; }
.bdate { color: #ffe39a; font-size: 13px; text-align: right; }
.sample { display:inline-block; margin-top: 4px; padding: 3px 10px; border-radius: 999px; font-size: 11px;
  border: 1px solid rgba(255,77,94,.6); color: #ffb3bb; background: rgba(255,77,94,.08); }
.hero { font-family:'Cinzel', serif; font-size: 2.3rem; font-weight: 800; margin: 2px 0 0;
  background: linear-gradient(90deg, #fff, #FFC93C 55%, #ff9d2e); -webkit-background-clip:text; color: transparent; }
/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 12px; border-bottom: 1px solid rgba(255,201,60,.18); }
.stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; color: #a59c84; padding: 8px 16px;
  border-radius: 12px 12px 0 0; background: rgba(30,24,10,.45); }
.stTabs [aria-selected="true"] { color: #fff1c1; box-shadow: 0 0 16px rgba(255,201,60,.35); }
.stTabs [data-baseweb="tab-highlight"] { background-color: #FFC93C; height: 3px; box-shadow: 0 0 10px #FFC93C; }
.stTabs [data-baseweb="tab-border"] { background-color: transparent; }
/* KPI strip: glass tiles with a 3D tilt on hover */
.kpis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin: 8px 0 6px; perspective: 900px; }
.kpi { padding: 12px 14px 10px; border-radius: 16px; background: rgba(22,18,8,.72);
  border: 1px solid rgba(255,201,60,.35); box-shadow: 0 8px 24px rgba(0,0,0,.5), 0 0 14px rgba(255,201,60,.12);
  transition: transform .35s ease, box-shadow .35s ease, border-color .35s ease; transform-style: preserve-3d; }
.kpi:hover { transform: rotateX(9deg) rotateY(-10deg) translateZ(16px); border-color: #FFC93C;
  box-shadow: 0 16px 34px rgba(0,0,0,.6), 0 0 26px rgba(255,201,60,.5); }
.kpi .l { font-size: 11px; color: #a59c84; line-height: 1.25; text-transform: uppercase; letter-spacing: .08em; }
.kpi .v { font-size: 20px; font-weight: 600; margin-top: 3px; color: #fff1c1; }
.kpi .v small { font-size: 11.5px; font-weight: 500; color: #a59c84; margin-left: 4px; }
.kpi svg { display: block; margin-top: 5px; }
[data-testid="stPlotlyChart"] { border-radius: 18px; padding: 6px; background: rgba(18,14,6,.5);
  border: 1px solid rgba(255,201,60,.18); }
.grammar { font-size: 12.5px; color: #a59c84; margin: 4px 0 12px; }
.grammar b { color: #fff1c1; font-weight: 600; }
@media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, 1fr); } }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------- plotly theme --
pio.templates["ledger"] = go.layout.Template(layout=dict(
    paper_bgcolor=dz.PAPER, plot_bgcolor=dz.PAPER,
    font=dict(family="Archivo, system-ui, sans-serif", color=dz.INK, size=13),
    margin=dict(l=10, r=64, t=34, b=10), showlegend=False,
    xaxis=dict(showgrid=False, ticks="outside", tickcolor=dz.GHOST,
               linecolor=dz.GHOST),
    yaxis=dict(gridcolor="rgba(255,201,60,.09)", zeroline=False, side="right",
               tickformat=","),
    hoverlabel=dict(bgcolor="#17130a", bordercolor="#FFC93C",
                    font=dict(family="Archivo, system-ui, sans-serif",
                              color=dz.INK, size=12)),
))
pio.templates.default = "ledger"

# ------------------------------------------------------------------ loading --
@st.cache_data(ttl=3600)
def load(name: str, dates=("date",)) -> pd.DataFrame:
    return pd.read_csv(DATA / f"{name}.csv", parse_dates=list(dates))

try:
    price = load("price")
    etf = load("etf")
    declared = load("declared")
    gap = load("gap", dates=("quarter_end",))
    swiss = load("swiss")
except FileNotFoundError:
    st.error("No data found. Run `python ingest.py --synthetic` first.")
    st.stop()

asof = {"price": price.date.max(), "etf": etf.date.max(),
        "declared": declared.date.max(), "gap": gap.quarter_end.max(),
        "swiss": swiss.date.max()}
fmt = lambda t: pd.Timestamp(t).strftime("%b %y")

# --------------------------------------------------------------- helpers -----
def events(fig, label: bool):
    for i, (d, t) in enumerate(dz.EVENTS):
        fig.add_vline(x=d, line_color=dz.GHOST, line_width=1)
        if label:
            fig.add_annotation(x=d, y=1.03 + 0.075 * (i % 2), yref="paper",
                               text=t, showarrow=False,
                               font=dict(size=11, color=dz.FAINT))

def endlabel(fig, x, y, text, color=dz.FAINT):
    fig.add_annotation(x=x, y=y, text=text, showarrow=False, xanchor="left",
                       xshift=8, font=dict(size=12, color=color))

def chart(fig, h):
    fig.update_layout(height=h, template="plotly_dark+ledger",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch", theme=None,
                    config={"displayModeBar": False})

def spark(vals, color, w=76, h=20):
    lo, hi = min(vals), max(vals) + 1e-9
    pts = " ".join(f"{2 + (w-4)*i/(len(vals)-1):.1f},"
                   f"{h-2 - (h-4)*(v-lo)/(hi-lo):.1f}" for i, v in enumerate(vals))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="1.6" stroke-linejoin="round"/></svg>')

# ------------------------------------------------------------- derived nums --
t12 = (declared[declared.date > asof["declared"] - pd.DateOffset(months=12)]
       .groupby("country").net_purchases_t.sum().sort_values(ascending=False))
top_buy, top_sell = t12.index[0], t12.index[-1]
east_m = (swiss[swiss.destination.isin(["China + HK", "India", "Turkey"])]
          .groupby("date").tonnes.sum())
all_last = swiss[swiss.date == asof["swiss"]].tonnes.sum()
gap_res = (gap.wgc_estimate_t - gap.imf_reported_t)
p_now, p_prev = price.price_usd_oz.iloc[-1], price.price_usd_oz.iloc[-2]
e_now, e_prev = etf.tonnes.iloc[-1], etf.tonnes.iloc[-2]
china12 = declared[declared.country == top_buy].net_purchases_t.tail(12)
russia12 = declared[declared.country == top_sell].net_purchases_t.tail(12)

# ----------------------------------------------------------------- masthead --
COIN = """<svg class="coin" width="50" height="50" viewBox="0 0 64 64">
 <defs><radialGradient id="au" cx="35%" cy="30%"><stop offset="0" stop-color="#fff6cf"/>
 <stop offset=".5" stop-color="#FFC93C"/><stop offset="1" stop-color="#a86b00"/></radialGradient></defs>
 <circle cx="32" cy="32" r="28" fill="url(#au)" stroke="#fff1c1" stroke-width="1.5"/>
 <circle cx="32" cy="32" r="21" fill="none" stroke="#a86b00" stroke-width="1.5" stroke-dasharray="2 3"/>
 <text x="32" y="39" text-anchor="middle" font-family="Cinzel, serif" font-weight="800"
  font-size="19" fill="#5a3a00">Au</text></svg>"""
st.markdown(f"""
<div class="brandbar"><div class="brand">{COIN}
  <div><div class="bname">AURUM</div><div class="bsub">Gold stock-transfer monitor</div></div></div>
  <div class="bdate">{pd.Timestamp(asof['price']).strftime('%A %d %B %Y')}<br>
  <span class="sample">sample data for practice</span></div></div>
<div class="hero">Who holds the gold, and which way is it moving?</div>
""", unsafe_allow_html=True)
st.caption("Adapted from the 36104 gold dashboard: same five sources and design grammar, "
           "a neon-noir look, and a new Explore tab for one country at a time.")

KPIS = [
    ("price, $/oz", f"{p_now:,.0f}", f"{p_now/p_prev-1:+.1%} m/m",
     spark(price.price_usd_oz.tail(12).tolist(), dz.GOLD)),
    ("GLD + IAU", f"{e_now:,.0f} t", f"{e_now-e_prev:+.0f} t m/m",
     spark(etf.tonnes.tail(12).tolist(), dz.hue("West"))),
    ("gap, latest qtr", f"+{gap_res.iloc[-1]:,.0f} t", "unreported",
     spark(gap_res.tail(8).tolist(), dz.GOLD)),
    ("top buyer, 12m", top_buy, f"+{t12.iloc[0]:,.0f} t",
     spark(china12.tolist(), dz.hue(top_buy))),
    ("top seller, 12m", top_sell, f"{t12.iloc[-1]:,.0f} t",
     spark(russia12.tolist(), dz.hue(top_sell))),
    (f"Swiss → east, {fmt(asof['swiss'])}", f"{east_m.iloc[-1]:,.0f} t",
     f"of {all_last:,.0f} t out",
     spark(east_m.tail(12).tolist(), dz.hue("China"))),
]
tiles = "".join(f'<div class="kpi"><div class="l">{l}</div>'
                f'<div class="v">{v}<small>{s}</small></div>{sp}</div>'
                for l, v, s, sp in KPIS)
st.markdown(f'<div class="kpis">{tiles}</div>', unsafe_allow_html=True)
st.markdown('<p class="grammar"><b>Solid</b> marks reported series, '
            '<b>dashed</b> marks estimates. Each country keeps one colour on '
            'every panel.</p>', unsafe_allow_html=True)

tabD, tabI, tabX = st.tabs(["🏛️ Declared", "🔍 Inferred", "🧭 Explore"])

# ============================================================== DECLARED =====
with tabD:
    st.subheader("Price and its opportunity cost")
    st.caption(f"Has the price detached from real yields, and by how much? — "
               f"as of {fmt(asof['price'])}")
    f = go.Figure()
    f.add_trace(go.Scatter(x=price.date, y=price.yield_implied_usd_oz,
        name="yield-implied", mode="lines",
        line=dict(color=dz.INK, width=1.3, dash=dz.DASH)))
    f.add_trace(go.Scatter(x=price.date, y=price.price_usd_oz, name="price",
        mode="lines", line=dict(color=dz.GOLD, width=2.6),
        fill="tonexty", fillcolor="rgba(255,201,60,.14)"))
    events(f, label=True)
    endlabel(f, price.date.iloc[-1], p_now, f"<b>{p_now:,.0f}</b> $/oz", dz.GOLD)
    endlabel(f, price.date.iloc[-1], price.yield_implied_usd_oz.iloc[-1], "implied")
    f.update_layout(hovermode="x unified")
    chart(f, 430)
    st.caption("Shaded wedge: actual price over the pre-2022 yield-implied "
               "level — the premium a yield-indifferent buyer pays.")

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("Western investor holdings")
        st.caption(f"Is the yield-sensitive holder buying this move or "
                   f"selling into it? — as of {fmt(asof['etf'])}")
        f = go.Figure(go.Scatter(x=etf.date, y=etf.tonnes, mode="lines",
            line=dict(color=dz.hue("West"), width=2.4)))
        events(f, label=False)
        endlabel(f, etf.date.iloc[-1], e_now, f"<b>{e_now:,.0f}</b> t",
                 dz.hue("West"))
        chart(f, 330)
    with right:
        st.subheader("Declared official sector")
        st.caption(f"Trailing 12-month reported change — IMF, "
                   f"{fmt(asof['declared'])}")
        s = t12.sort_values()
        f = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h",
            marker_color=[dz.hue(c) for c in s.index],
            text=[f"{v:+,.0f}" for v in s.values], textposition="outside",
            textfont=dict(size=11, color=dz.FAINT), cliponaxis=False))
        f.update_xaxes(title="tonnes", showgrid=False)
        f.update_yaxes(side="left", gridcolor="rgba(0,0,0,0)", automargin=True)
        f.update_layout(margin=dict(l=90))
        chart(f, 330)

    with st.expander("12-month detail per bank"):
        d12 = declared[declared.date > asof["declared"] -
                       pd.DateOffset(months=12)].copy()
        order = t12.index.tolist()
        fig = px.bar(d12, x="date", y="net_purchases_t", facet_col="country",
                     facet_col_wrap=5, category_orders={"country": order},
                     color="country",
                     color_discrete_map={c: dz.hue(c) for c in order},
                     facet_row_spacing=.10, facet_col_spacing=.03)
        fig.update_yaxes(matches=None, title=None, side="left")
        fig.update_xaxes(title=None, showticklabels=False)
        fig.for_each_annotation(lambda a:
            a.update(text=a.text.split("=")[-1], font=dict(size=12)))
        chart(fig, 520)

# ============================================================== INFERRED =====
with tabI:
    st.subheader("The gap")
    st.caption(f"How much official buying goes unreported each quarter? — "
               f"{gap.quarter_end.iloc[-1].to_period('Q')}")
    f = go.Figure()
    f.add_trace(go.Scatter(x=gap.quarter_end, y=gap.imf_reported_t,
        mode="lines", line=dict(width=0), hoverinfo="skip"))
    f.add_trace(go.Scatter(x=gap.quarter_end, y=gap.wgc_estimate_t,
        name="WGC estimate", mode="lines",
        line=dict(color=dz.INK, width=1.6, dash=dz.DASH),
        fill="tonexty", fillcolor="rgba(255,201,60,.18)"))
    f.add_trace(go.Bar(x=gap.quarter_end, y=gap.imf_reported_t,
        name="reported to IMF", marker_color=dz.INK, opacity=.85))
    events(f, label=True)
    endlabel(f, gap.quarter_end.iloc[-1], gap.wgc_estimate_t.iloc[-1],
             f"WGC <b>{gap.wgc_estimate_t.iloc[-1]:,.0f}</b> t")
    endlabel(f, gap.quarter_end.iloc[-1], gap.imf_reported_t.iloc[-1],
             f"IMF <b>{gap.imf_reported_t.iloc[-1]:,.0f}</b> t")
    f.update_yaxes(title="tonnes / quarter")
    chart(f, 430)
    st.caption("Bars: purchases reported to the IMF. Dashed: World Gold "
               "Council estimate of actual official demand. Shaded: the "
               "unreported residual.")

    st.subheader("Physical flow west to east")
    st.caption(f"Where are the bars going, and is the float being "
               f"replenished? — Swiss customs, {fmt(asof['swiss'])}")
    f = go.Figure()
    for dest in ["other", "UAE + Gulf", "UK + US", "Turkey", "India",
                 "China + HK"]:
        d = swiss[swiss.destination == dest]
        f.add_trace(go.Scatter(x=d.date, y=d.tonnes, name=dest,
            stackgroup="flow", mode="none", fillcolor=dz.hue(dest),
            hovertemplate=f"{dest}: %{{y:.0f}} t<extra></extra>"))
    events(f, label=False)
    show_repl = st.toggle("show mine replenishment")
    if show_repl:
        f.add_hline(y=dz.MINE_TOTAL_TPM,
            line=dict(color=dz.INK, width=1.2, dash="dash"),
            annotation_text="all mine supply ≈ 300 t/mo",
            annotation_position="top left")
        f.add_hline(y=dz.MINE_WESTERN_TPM,
            line=dict(color=dz.INK, width=1.2, dash="dot"),
            annotation_text="enters Western circuit ≈ 200 t/mo",
            annotation_position="bottom left")
    f.update_yaxes(title="tonnes / month", range=[0, 330])
    f.update_layout(showlegend=True, legend=dict(orientation="h", y=1.06,
        x=0, font=dict(size=12)), hovermode="x unified")
    chart(f, 400)
    if show_repl:
        st.caption("Output above the lower line drains the Western float "
                   "faster than the ground refills it. The space between the "
                   "lines is mine supply born outside the circuit (China, "
                   "Russia, Uzbekistan, Kazakhstan).")

# ================================================================ EXPLORE ====
with tabX:
    st.subheader("Explore one country")
    st.caption("The ranking in Declared answers *who* bought or sold most over 12 months. "
               "This view answers *when*: pick a country, a period and up to three rivals. "
               "All values are the sample data supplied with the app.")
    countries = sorted(declared["country"].unique())
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        country = st.selectbox("Choose a country", countries,
                               index=countries.index("China") if "China" in countries else 0)
    with c2:
        rivals = st.multiselect("Compare with (up to 3)",
                                [c for c in countries if c != country],
                                default=[c for c in ["Russia", "India"] if c != country][:2],
                                max_selections=3)
    dmin, dmax = declared.date.min().date(), declared.date.max().date()
    start, end = st.slider("Period", min_value=dmin, max_value=dmax, value=(dmin, dmax),
                           format="MMM YYYY")
    window = declared[(declared.date.dt.date >= start) & (declared.date.dt.date <= end)]
    one = window[window.country == country]

    k1, k2, k3 = st.columns(3)
    k1.metric(f"{country}: net change in period", f"{one.net_purchases_t.sum():+,.0f} t")
    k2.metric("Months of net buying", f"{(one.net_purchases_t > 0).sum()} of {len(one)}")
    biggest = one.loc[one.net_purchases_t.abs().idxmax()] if len(one) else None
    k3.metric("Largest single month",
              f"{biggest.net_purchases_t:+,.0f} t" if biggest is not None else "n/a",
              biggest.date.strftime("%b %Y") if biggest is not None else None, delta_color="off")

    fig = px.bar(one, x="date", y="net_purchases_t",
                 labels={"date": "Month", "net_purchases_t": "Tonnes"},
                 title=f"{country}: monthly purchases and sales (sample data)")
    fig.update_traces(marker_color=[dz.hue(country) if v >= 0 else "#6E6A60"
                                    for v in one.net_purchases_t])
    events(fig, label=True)
    fig.update_yaxes(title="tonnes per month", side="left")
    chart(fig, 380)
    st.caption("Bars above zero: net buying that month; grey bars below zero: net selling. "
               "Vertical rules mark the same political events as the other tabs.")

    st.subheader("Cumulative position since the start of the period")
    comp = window[window.country.isin([country] + rivals)].sort_values("date").copy()
    comp["cumulative_t"] = comp.groupby("country").net_purchases_t.cumsum()
    f = go.Figure()
    for c in [country] + rivals:
        d = comp[comp.country == c]
        if d.empty:
            continue
        f.add_trace(go.Scatter(x=d.date, y=d.cumulative_t, mode="lines", name=c,
                               line=dict(color=dz.hue(c), width=3.2 if c == country else 1.8)))
        endlabel(f, d.date.iloc[-1], d.cumulative_t.iloc[-1],
                 f"<b>{c}</b> {d.cumulative_t.iloc[-1]:+,.0f} t", dz.hue(c))
    events(f, label=False)
    f.update_yaxes(title="tonnes, cumulative", side="left")
    f.update_layout(hovermode="x unified")
    chart(f, 360)

    st.subheader("3D landscape: every country, every month")
    st.caption("Height and colour show monthly net purchases (gold peaks) and sales (dark troughs) "
               "for the eight most active countries in the period. Drag to rotate, scroll to zoom.")
    top = (window.groupby("country").net_purchases_t.apply(lambda v: v.abs().sum())
           .sort_values(ascending=False).head(8).index.tolist())
    grid = (window[window.country.isin(top)]
            .pivot_table(index="country", columns="date", values="net_purchases_t")
            .reindex(top))
    surf = go.Figure(go.Surface(
        z=grid.values, x=list(grid.columns), y=list(range(len(top))),
        colorscale=[[0, "#2a1b4a"], [0.45, "#3b3426"], [0.5, "#5a4a1a"],
                    [0.75, "#FFC93C"], [1, "#fff1c1"]],
        cmid=0, showscale=True, colorbar=dict(title="t / month", len=0.6),
        hovertemplate="%{x|%b %Y}<br>%{z:+.1f} t<extra></extra>",
        contours=dict(z=dict(show=True, usecolormap=True, project_z=True, width=1))))
    axis3 = dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,201,60,.15)",
                 color="#d8cfb4", showbackground=True)
    surf.update_layout(height=620, paper_bgcolor="rgba(0,0,0,0)",
                       margin=dict(l=0, r=0, t=10, b=0), font=dict(color="#f3ead2"),
                       scene=dict(xaxis=dict(title="month", **axis3),
                                  yaxis=dict(title="", tickvals=list(range(len(top))),
                                             ticktext=top, **axis3),
                                  zaxis=dict(title="tonnes", **axis3),
                                  camera=dict(eye=dict(x=1.7, y=-1.6, z=0.9)),
                                  aspectratio=dict(x=1.6, y=1.1, z=0.6)))
    surf.update_layout(template="plotly_dark")
    surf.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(surf, width="stretch", theme=None)

st.caption("Sources when live: COMEX front-month futures (GC=F), FRED DFII10, "
           "GLD and IAU daily bar lists, IMF International Financial "
           "Statistics, World Gold Council Gold Demand Trends, Swiss-Impex "
           "tariff heading 7108. Event rules: Feb 22 reserve freeze, Jun 22 "
           "G7 import ban, Jun 25 Iran war, Nov 25 CBR sales begin, May 26 "
           "escalation.")
