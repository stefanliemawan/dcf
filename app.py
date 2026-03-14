"""
DCF Valuation Model — Streamlit App

Run with:
    streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dcf import DCFInputs, WACCInputs, run_dcf, sensitivity_table
from models import COMPANIES, INDUSTRY_BENCHMARKS, INDUSTRY_DEFAULTS

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DCF Valuation Model",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    .stMetric label { font-size: 0.78rem; color: #888; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _hint(val: float, lo: float, hi: float, extra: str = "") -> str:
    """
    Return a one-line markdown hint showing where val falls vs [lo, hi].
    val, lo, hi are all in % (e.g. 9.5, not 0.095).
    """
    margin = (hi - lo) * 0.15  # 15% grace zone at each end
    if val < lo - margin:
        icon, word = "⬇️", f"Below typical ({lo:.1f}–{hi:.1f}%)"
    elif val > hi + margin:
        icon, word = "⬆️", f"Above typical ({lo:.1f}–{hi:.1f}%)"
    else:
        icon, word = "✅", f"Within typical range ({lo:.1f}–{hi:.1f}%)"
    return f"{icon} {word}" + (f"  ·  {extra}" if extra else "")


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 DCF Model")
    st.markdown("*Discounted Cash Flow Valuation*")
    st.divider()

    ticker = st.selectbox(
        "Company",
        options=list(COMPANIES.keys()),
        format_func=lambda x: f"{x}  —  {COMPANIES[x].name}",
    )

    # Reset slider state when company changes
    if st.session_state.get("_prev_ticker") != ticker:
        for key in [
            "rf", "erp", "beta", "kd", "tax", "eq_w",
            "g1", "g2", "g3", "tgr", "base_fcf", "cash", "debt", "shares",
            "forecast_years",
        ]:
            st.session_state.pop(key, None)
        st.session_state["_prev_ticker"] = ticker

    company = COMPANIES[ticker]
    ind = INDUSTRY_DEFAULTS.get(company.industry, INDUSTRY_DEFAULTS["Technology"])
    bench = INDUSTRY_BENCHMARKS.get(company.industry, INDUSTRY_BENCHMARKS["Technology"])
    curr = company.currency

    st.markdown(f"**{company.name}**")
    st.caption(f"{company.sector}  ·  {company.industry}  ·  {curr}")
    st.divider()

    # Quick snapshot for the sidebar
    implied_ke = ind["risk_free_rate"] + company.beta * ind["equity_risk_premium"]
    st.markdown("**Industry WACC range**")
    st.caption(f"{bench.wacc_range[0]:.1f}% – {bench.wacc_range[1]:.1f}%")
    st.markdown("**Typical terminal growth**")
    st.caption(f"{bench.tgr_range[0]:.1f}% – {bench.tgr_range[1]:.1f}%")
    st.markdown("**Company beta**")
    st.caption(
        f"{company.beta:.2f}  (industry: {bench.beta_range[0]:.1f}–{bench.beta_range[1]:.1f})"
    )
    st.divider()
    st.caption("📌 Data is mocked for demonstration.\nFMP API integration coming soon.")


# ── Company overview ───────────────────────────────────────────────────────────
st.title(f"{company.name}  ({ticker})")
st.caption(f"{company.sector}  ·  {company.industry}  ·  {curr}")

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
c1.metric("Revenue TTM", f"{curr} {company.revenue_ttm:.1f}B")
c2.metric("FCF TTM", f"{curr} {company.fcf_ttm:.1f}B")
c3.metric(
    "FCF Margin",
    f"{company.fcf_margin_ttm:.1%}",
    help="Free Cash Flow / Revenue (TTM)",
)
c4.metric("Cash", f"{curr} {company.cash:.1f}B")
c5.metric("Total Debt", f"{curr} {company.total_debt:.1f}B")
c6.metric("Shares Out.", f"{company.shares_outstanding:.3f}B")
c7.metric("Market Price", f"{curr} {company.current_price:.2f}")

st.divider()

# ── Reference Sheet ────────────────────────────────────────────────────────────
with st.expander("📚  Assumption Reference Sheet — click to expand", expanded=False):
    ref_c1, ref_c2, ref_c3 = st.columns(3)

    with ref_c1:
        st.markdown("#### 🏦 Current Market Rates")
        st.caption("*As of Q1 2025 — update when using live data*")
        rates = pd.DataFrame(
            {
                "Rate": [
                    "10Y US Treasury",
                    "Fed Funds Rate",
                    "Damodaran US ERP (Jan 2025)",
                    "Historical ERP avg (1928–2024)",
                    "IG corporate spread (vs Treasury)",
                    "High-yield spread (vs Treasury)",
                    "US long-run GDP growth",
                    "Global long-run GDP growth",
                ],
                "Value": [
                    "4.4%",
                    "4.25–4.50%",
                    "4.6%",
                    "5.5%",
                    "1.0–1.5%",
                    "3.0–5.0%",
                    "~2.0–2.5%",
                    "~3.0%",
                ],
            }
        )
        st.dataframe(rates, hide_index=True, use_container_width=True)

        st.markdown("**Cost-of-debt rule of thumb**")
        st.caption(
            "Investment grade (BBB+): 10Y Treasury + 1.0–1.5%  \n"
            "Investment grade (BBB): 10Y Treasury + 1.5–2.5%  \n"
            "High yield (BB/B): 10Y Treasury + 3.0–5.5%+"
        )

    with ref_c2:
        st.markdown(f"#### 🏭 Industry Benchmarks — {company.industry}")
        st.caption(bench.notes)

        bench_df = pd.DataFrame(
            {
                "Metric": [
                    "WACC",
                    "Beta (5Y monthly)",
                    "Pre-tax cost of debt",
                    "Effective tax rate",
                    "Terminal growth rate",
                    "FCF growth Y1–3 (typical)",
                    "FCF growth Y6–10 (typical)",
                ],
                "Typical Range": [
                    f"{bench.wacc_range[0]:.1f}–{bench.wacc_range[1]:.1f}%",
                    f"{bench.beta_range[0]:.1f}–{bench.beta_range[1]:.1f}×",
                    f"{bench.cost_of_debt_range[0]:.1f}–{bench.cost_of_debt_range[1]:.1f}%",
                    f"{bench.tax_range[0]:.0f}–{bench.tax_range[1]:.0f}%",
                    f"{bench.tgr_range[0]:.1f}–{bench.tgr_range[1]:.1f}%",
                    f"{bench.fcf_growth_near[0]:.0f}–{bench.fcf_growth_near[1]:.0f}%",
                    f"{bench.fcf_growth_long[0]:.0f}–{bench.fcf_growth_long[1]:.0f}%",
                ],
            }
        )
        st.dataframe(bench_df, hide_index=True, use_container_width=True)

    with ref_c3:
        st.markdown(f"#### 📈 {ticker} Historical & Estimates")
        st.caption("*Based on mocked/public data. Replace with live FMP data.*")

        net_cash_or_debt = company.cash - company.total_debt
        net_debt_label = (
            f"{curr} {abs(net_cash_or_debt):.1f}B net {'cash' if net_cash_or_debt > 0 else 'debt'}"
        )
        net_debt_to_fcf = (company.total_debt - company.cash) / company.fcf_ttm if company.fcf_ttm else 0

        comp_df = pd.DataFrame(
            {
                "Metric": [
                    "Historical FCF CAGR (3Y)",
                    "FCF margin (TTM)",
                    "Effective tax rate",
                    "Beta (5Y monthly)",
                    "Net position",
                    "Net Debt / FCF",
                    "Analyst FCF growth (1Y est.)",
                    "Analyst FCF growth (3Y CAGR est.)",
                ],
                "Value": [
                    f"{company.historical_fcf_growth:.0%}",
                    f"{company.fcf_margin_ttm:.1%}",
                    f"{company.tax_rate:.0%}",
                    f"{company.beta:.2f}",
                    net_debt_label,
                    f"{net_debt_to_fcf:.1f}×" if net_debt_to_fcf > 0 else "Net cash",
                    f"{company.analyst_fcf_growth_1y:.0%}",
                    f"{company.analyst_fcf_growth_3y:.0%}",
                ],
            }
        )
        st.dataframe(comp_df, hide_index=True, use_container_width=True)

        st.markdown("**Interpretation guide**")
        st.caption(
            "Use analyst estimates as a cross-check on your growth assumptions.  \n"
            "Historical CAGR ≠ future growth — fade growth over time.  \n"
            "TGR must be < WACC, and ideally ≤ long-run GDP."
        )

st.divider()

# ── Assumptions: three columns ────────────────────────────────────────────────
col_wacc, col_growth, col_bs = st.columns([1.3, 1.3, 0.9])

# ── WACC Builder ──────────────────────────────────────────────────────────────
with col_wacc:
    st.subheader("⚙️ WACC Builder")

    default_eq_wt = min(
        0.99,
        round(company.market_cap / (company.market_cap + company.total_debt), 2),
    )

    rf_pct = st.slider(
        "Risk-Free Rate (10Y Treasury)",
        min_value=1.0, max_value=7.0,
        value=float(ind["risk_free_rate"]),
        step=0.1, format="%.1f%%", key="rf",
        help=(
            "The yield on a long-term government bond — the 'time value of money' baseline. "
            "Use the 10Y bond yield for the currency you are valuing in. "
            "US 10Y ≈ 4.4% (Q1 2025). Rises in a high-inflation / tightening cycle."
        ),
    )
    st.caption(_hint(rf_pct, 3.5, 5.5, "Current 10Y US Treasury ≈ 4.4%"))

    erp_pct = st.slider(
        "Equity Risk Premium (ERP)",
        min_value=3.0, max_value=10.0,
        value=float(ind["equity_risk_premium"]),
        step=0.1, format="%.1f%%", key="erp",
        help=(
            "The extra return investors demand for owning equities vs risk-free bonds. "
            "Damodaran US estimate (Jan 2025): 4.6%. Long-run historical avg: 5.5%. "
            "Use 5–6% for developed markets, 6–8% for emerging markets."
        ),
    )
    st.caption(_hint(erp_pct, 4.0, 7.0, "Damodaran US (Jan 2025) = 4.6% · LT avg = 5.5%"))

    beta_val = st.slider(
        "Beta (systematic risk)",
        min_value=0.2, max_value=3.5,
        value=float(round(company.beta, 2)),
        step=0.05, key="beta",
        help=(
            "Measures the stock's volatility relative to the market (β = 1 moves with market). "
            "β < 1: defensive (utilities, healthcare). β > 1: growth/cyclical (tech, EV). "
            "Use 5-year monthly regression vs S&P 500. Adjust up for smaller/riskier companies."
        ),
    )
    st.caption(
        _hint(
            beta_val,
            bench.beta_range[0],
            bench.beta_range[1],
            f"Industry: {bench.beta_range[0]:.1f}–{bench.beta_range[1]:.1f}×",
        )
    )

    rf = rf_pct / 100
    erp = erp_pct / 100
    ke = rf + beta_val * erp
    st.info(
        f"Cost of Equity (CAPM) = **{ke:.2%}**  \n"
        f"`Rf {rf_pct:.1f}% + β {beta_val:.2f} × ERP {erp_pct:.1f}%`"
    )

    kd_pct = st.slider(
        "Pre-Tax Cost of Debt",
        min_value=1.0, max_value=12.0,
        value=float(ind["pre_tax_cost_of_debt"]),
        step=0.1, format="%.1f%%", key="kd",
        help=(
            "The interest rate the company pays on its debt (before tax shield). "
            "Use the yield on the company's outstanding bonds, or: "
            "Risk-Free Rate + credit spread. Investment grade (BBB+): +1.0–1.5%. "
            "High yield (BB/B): +3.0–5.5%."
        ),
    )
    st.caption(
        _hint(
            kd_pct,
            bench.cost_of_debt_range[0],
            bench.cost_of_debt_range[1],
            f"IG range: {bench.cost_of_debt_range[0]:.1f}–{bench.cost_of_debt_range[1]:.1f}%",
        )
    )

    tax_pct = st.slider(
        "Effective Tax Rate",
        min_value=5.0, max_value=40.0,
        value=float(round(company.tax_rate * 100, 0)),
        step=1.0, format="%.0f%%", key="tax",
        help=(
            "Use the effective (actual) tax rate, not the statutory rate. "
            "US statutory = 21%. Tech/pharma often lower due to R&D credits & IP structures. "
            f"{ticker}'s 3-year effective avg: {company.tax_rate:.0%}. "
            "Find it on the income statement: Income Tax Expense / Pre-Tax Income."
        ),
    )
    st.caption(
        _hint(
            tax_pct,
            bench.tax_range[0],
            bench.tax_range[1],
            f"US statutory = 21% · {ticker} historical = {company.tax_rate:.0%}",
        )
    )

    kd = kd_pct / 100
    tax = tax_pct / 100
    kd_at = kd * (1 - tax)
    st.info(
        f"After-Tax Cost of Debt = **{kd_at:.2%}**  \n"
        f"`Kd {kd_pct:.1f}% × (1 − {tax_pct:.0f}%)`"
    )

    eq_w_pct = st.slider(
        "Equity Weight (% of total capital)",
        min_value=10.0, max_value=100.0,
        value=float(round(default_eq_wt * 100, 0)),
        step=1.0, format="%.0f%%", key="eq_w",
        help=(
            "Equity / (Equity + Debt) by market value. "
            "Auto-suggested from market cap and total debt. "
            "Most large-cap tech companies are >90% equity-financed. "
            "High debt companies (leveraged buyouts, utilities) may be 40–60%."
        ),
    )
    eq_w = eq_w_pct / 100
    dbt_w = 1.0 - eq_w
    st.caption(
        f"Auto-calculated from market data: {default_eq_wt * 100:.0f}% equity  ·  "
        f"Market cap {curr} {company.market_cap:.0f}B / Total cap {curr} {company.market_cap + company.total_debt:.0f}B"
    )

    wacc_inputs = WACCInputs(
        risk_free_rate=rf,
        equity_risk_premium=erp,
        beta=beta_val,
        pre_tax_cost_of_debt=kd,
        tax_rate=tax,
        equity_weight=eq_w,
    )
    wacc = wacc_inputs.wacc

    in_range = bench.wacc_range[0] <= wacc * 100 <= bench.wacc_range[1]
    wacc_range_note = (
        f"Industry typical: {bench.wacc_range[0]:.1f}–{bench.wacc_range[1]:.1f}%"
    )
    st.success(
        f"**WACC = {wacc:.2%}**  {'✅' if in_range else '⚠️ outside typical range'}  \n"
        f"`{ke:.2%} × {eq_w_pct:.0f}% + {kd_at:.2%} × {dbt_w*100:.0f}%`  \n"
        f"*{wacc_range_note}*"
    )


# ── Growth Assumptions ────────────────────────────────────────────────────────
with col_growth:
    st.subheader("📈 Growth Assumptions")

    forecast_years = st.radio(
        "Forecast Period", [5, 10], index=1, horizontal=True, key="forecast_years",
        help="5 years for mature companies; 10 years for high-growth companies still in expansion.",
    )

    st.markdown("**FCF Growth Rates**")

    g1_pct = st.slider(
        "Years 1–3 (near-term)",
        min_value=-10.0, max_value=60.0,
        value=float(ind["fcf_growth_y1_3"]),
        step=0.5, format="%.1f%%", key="g1",
        help=(
            "Near-term FCF growth — the phase you have most visibility on. "
            "Anchor to analyst consensus, company guidance, and recent trajectory. "
            "High-growth companies can sustain 20–40%+; mature companies 3–8%."
        ),
    )
    st.caption(
        _hint(
            g1_pct,
            bench.fcf_growth_near[0],
            bench.fcf_growth_near[1],
            f"Analyst est. 1Y: {company.analyst_fcf_growth_1y:.0%}  "
            f"· Hist. CAGR: {company.historical_fcf_growth:.0%}",
        )
    )

    g2_pct = st.slider(
        "Years 4–5 (mid-term)",
        min_value=-10.0, max_value=50.0,
        value=float(ind["fcf_growth_y4_5"]),
        step=0.5, format="%.1f%%", key="g2",
        help=(
            "Growth starts to moderate as competition increases and the business matures. "
            "Typically 60–80% of your near-term rate. "
            "Should fade toward the long-term rate."
        ),
    )
    st.caption(
        _hint(
            g2_pct,
            bench.fcf_growth_near[0] * 0.7,
            bench.fcf_growth_near[1] * 0.8,
            f"Analyst 3Y CAGR est.: {company.analyst_fcf_growth_3y:.0%}",
        )
    )

    if forecast_years == 10:
        g3_pct = st.slider(
            "Years 6–10 (long-term fade)",
            min_value=-10.0, max_value=40.0,
            value=float(ind["fcf_growth_y6_10"]),
            step=0.5, format="%.1f%%", key="g3",
            help=(
                "The fade period — growth converging toward the terminal rate. "
                "For most companies this is 4–10%. "
                "Should be meaningfully lower than Y1–3 and above the terminal growth rate."
            ),
        )
        st.caption(
            _hint(
                g3_pct,
                bench.fcf_growth_long[0],
                bench.fcf_growth_long[1],
                f"Industry long-term: {bench.fcf_growth_long[0]:.0f}–{bench.fcf_growth_long[1]:.0f}%",
            )
        )
    else:
        g3_pct = g2_pct

    tgr_pct = st.slider(
        "Terminal Growth Rate (perpetuity)",
        min_value=0.0, max_value=5.0,
        value=float(ind["terminal_growth_rate"]),
        step=0.25, format="%.2f%%", key="tgr",
        help=(
            "The growth rate applied forever after the forecast period. "
            "MUST be < WACC and ideally ≤ long-run GDP growth. "
            "US long-run GDP: ~2.0–2.5%. Global: ~3.0%. "
            "Using >3.5% implies the company will eventually be larger than the economy."
        ),
    )
    st.caption(
        _hint(
            tgr_pct,
            bench.tgr_range[0],
            bench.tgr_range[1],
            "US long-run GDP ≈ 2.0–2.5%  ·  Global ≈ 3.0%",
        )
    )

    g1 = g1_pct / 100
    g2 = g2_pct / 100
    g3 = g3_pct / 100
    tgr = tgr_pct / 100

    # Growth decay check
    if g1_pct > 0 and g2_pct > g1_pct:
        st.warning("⚠️ Years 4–5 growth is higher than Years 1–3. Growth should typically decline over time.")
    if forecast_years == 10 and g3_pct > g2_pct:
        st.warning("⚠️ Years 6–10 growth is higher than Years 4–5. The fade period should be lower.")

    # WACC vs TGR guard
    if wacc <= tgr:
        st.error(
            f"🚫 WACC ({wacc:.2%}) must be strictly above terminal growth ({tgr:.2%}). "
            "Increase WACC or lower the terminal growth rate."
        )


# ── Balance Sheet ─────────────────────────────────────────────────────────────
with col_bs:
    st.subheader("🏦 Balance Sheet")

    base_fcf = st.number_input(
        f"Base FCF ({curr} B)",
        min_value=0.01, max_value=1000.0,
        value=float(company.fcf_ttm), step=0.5, key="base_fcf",
        help=(
            "The starting FCF value from which projections grow. "
            "Use TTM (trailing 12-month) FCF. "
            "Consider normalising for one-off items or unusually high/low capex."
        ),
    )
    st.caption(
        f"TTM FCF: {curr} {company.fcf_ttm:.1f}B  ·  "
        f"FCF margin: {company.fcf_margin_ttm:.1%}"
    )

    cash_val = st.number_input(
        f"Cash & Equivalents ({curr} B)",
        min_value=0.0, max_value=1000.0,
        value=float(company.cash), step=0.5, key="cash",
        help=(
            "Cash and short-term investments on the balance sheet. "
            "Added to enterprise value to get equity value. "
            "Use the most recent quarter-end balance."
        ),
    )

    debt_val = st.number_input(
        f"Total Debt ({curr} B)",
        min_value=0.0, max_value=1000.0,
        value=float(company.total_debt), step=0.5, key="debt",
        help=(
            "Total financial debt (short-term + long-term debt, excluding operating liabilities). "
            "Subtracted from enterprise value to get equity value."
        ),
    )

    shares_val = st.number_input(
        "Shares Outstanding (B)",
        min_value=0.001, max_value=100.0,
        value=float(company.shares_outstanding), step=0.01, key="shares",
        help="Diluted shares outstanding (include options and convertibles).",
    )

    net_pos = cash_val - debt_val
    st.caption(
        f"**Net {'Cash' if net_pos > 0 else 'Debt'}**: {curr} {abs(net_pos):.1f}B  \n"
        f"Net Debt/FCF: {(debt_val - cash_val) / base_fcf:.1f}×"
        if base_fcf > 0 else ""
    )

st.divider()

# ── Run DCF ───────────────────────────────────────────────────────────────────
dcf_inputs = DCFInputs(
    base_fcf=base_fcf,
    fcf_growth_y1_3=g1,
    fcf_growth_y4_5=g2,
    fcf_growth_y6_10=g3,
    terminal_growth_rate=tgr,
    forecast_years=forecast_years,
    wacc=wacc,
    cash=cash_val,
    total_debt=debt_val,
    shares_outstanding=shares_val,
)

if wacc <= tgr:
    st.warning("Fix WACC / Terminal Growth Rate before viewing results.")
    st.stop()

results = run_dcf(dcf_inputs)
upside = (results.fair_value_per_share - company.current_price) / company.current_price

# ── Results Banner ────────────────────────────────────────────────────────────
r1, r2, r3, r4, r5, r6 = st.columns(6)
r1.metric("PV of FCFs", f"{curr} {results.pv_fcf_sum:.1f}B")
r2.metric(
    "PV of Terminal Value",
    f"{curr} {results.discounted_terminal_value:.1f}B",
    help=f"Terminal value is {results.tv_pct:.0f}% of enterprise value. "
         "Values >70–75% signal the valuation is very sensitive to terminal assumptions.",
)
r3.metric("Enterprise Value", f"{curr} {results.enterprise_value:.1f}B")
r4.metric("Equity Value", f"{curr} {results.equity_value:.1f}B")
r5.metric(
    "Fair Value / Share",
    f"{curr} {results.fair_value_per_share:.2f}",
    delta=f"vs market {curr} {company.current_price:.2f}",
)
r6.metric(
    "Upside / Downside",
    f"{upside:+.1%}",
    delta=f"{upside:+.1%}",
    delta_color="normal",
)

# TV concentration warning
if results.tv_pct > 70:
    st.warning(
        f"⚠️ Terminal Value is **{results.tv_pct:.0f}%** of Enterprise Value. "
        "This is high — small changes in WACC or TGR will move the fair value significantly. "
        "Review the Sensitivity tab."
    )

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_proj, tab_bridge, tab_sens = st.tabs(
    ["📋 FCF Projections", "🌉 Value Bridge", "🔬 Sensitivity Analysis"]
)

# ── Tab 1: FCF Projections ────────────────────────────────────────────────────
with tab_proj:
    year_labels = [f"Yr {i}" for i in results.years]

    df_proj = pd.DataFrame(
        {
            "Year": year_labels,
            f"Projected FCF ({curr} B)": [round(v, 2) for v in results.projected_fcfs],
            f"Discounted FCF ({curr} B)": [round(v, 2) for v in results.discounted_fcfs],
            "Growth Applied": (
                [f"{g1:.1%}"] * min(3, forecast_years)
                + [f"{g2:.1%}"] * min(2, max(0, forecast_years - 3))
                + [f"{g3:.1%}"] * max(0, forecast_years - 5)
            ),
            "Discount Factor": [f"{1 / (1 + wacc) ** (i+1):.4f}" for i in range(forecast_years)],
        }
    )

    fig_fcf = go.Figure()
    fig_fcf.add_bar(
        x=year_labels,
        y=results.projected_fcfs,
        name="Projected FCF",
        marker_color="#4C78A8",
    )
    fig_fcf.add_bar(
        x=year_labels,
        y=results.discounted_fcfs,
        name="Discounted FCF (PV)",
        marker_color="#F58518",
    )
    fig_fcf.update_layout(
        title=f"Free Cash Flow Projections — {forecast_years}-Year Forecast",
        barmode="group",
        yaxis_title=f"{curr} Billions",
        legend=dict(orientation="h", y=1.1),
        template="plotly_white",
        height=380,
    )
    st.plotly_chart(fig_fcf, use_container_width=True)

    st.dataframe(
        df_proj.style.format(
            {
                f"Projected FCF ({curr} B)": "{:.2f}",
                f"Discounted FCF ({curr} B)": "{:.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ── Tab 2: Value Bridge ───────────────────────────────────────────────────────
with tab_bridge:
    left, right = st.columns([1.6, 1])

    with left:
        fig_wf = go.Figure(
            go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "total", "relative", "relative", "total"],
                x=[
                    f"PV of FCFs\n({curr} {results.pv_fcf_sum:.1f}B)",
                    f"PV of Terminal Value\n({curr} {results.discounted_terminal_value:.1f}B)",
                    "Enterprise Value",
                    f"+ Cash\n({curr} {cash_val:.1f}B)",
                    f"− Debt\n({curr} {debt_val:.1f}B)",
                    "Equity Value",
                ],
                y=[
                    results.pv_fcf_sum,
                    results.discounted_terminal_value,
                    0,
                    cash_val,
                    -debt_val,
                    0,
                ],
                text=[
                    f"{curr} {results.pv_fcf_sum:.1f}B",
                    f"{curr} {results.discounted_terminal_value:.1f}B",
                    f"{curr} {results.enterprise_value:.1f}B",
                    f"+{curr} {cash_val:.1f}B",
                    f"−{curr} {debt_val:.1f}B",
                    f"{curr} {results.equity_value:.1f}B",
                ],
                textposition="outside",
                connector={"line": {"color": "#aaa"}},
                increasing={"marker": {"color": "#3D9970"}},
                decreasing={"marker": {"color": "#E74C3C"}},
                totals={"marker": {"color": "#2980B9"}},
            )
        )
        fig_wf.update_layout(
            title="Enterprise Value → Equity Value Bridge",
            yaxis_title=f"{curr} Billions",
            template="plotly_white",
            height=430,
        )
        st.plotly_chart(fig_wf, use_container_width=True)

    with right:
        fig_pie = go.Figure(
            go.Pie(
                labels=["PV of FCFs", "PV of Terminal Value"],
                values=[results.pv_fcf_sum, results.discounted_terminal_value],
                hole=0.5,
                marker_colors=["#4C78A8", "#F58518"],
                textinfo="label+percent",
            )
        )
        fig_pie.update_layout(
            title=f"EV Composition  (TV = {results.tv_pct:.0f}%)",
            template="plotly_white",
            height=280,
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        summary = pd.DataFrame(
            {
                "Component": [
                    "PV of FCFs",
                    "PV of Terminal Value",
                    "Enterprise Value",
                    "Add: Cash",
                    "Less: Debt",
                    "Equity Value",
                    "÷ Shares Out.",
                    "Fair Value / Share",
                    "Market Price",
                    "Upside / Downside",
                ],
                "Value": [
                    f"{curr} {results.pv_fcf_sum:.2f}B",
                    f"{curr} {results.discounted_terminal_value:.2f}B",
                    f"{curr} {results.enterprise_value:.2f}B",
                    f"+{curr} {cash_val:.2f}B",
                    f"−{curr} {debt_val:.2f}B",
                    f"{curr} {results.equity_value:.2f}B",
                    f"{shares_val:.3f}B",
                    f"{curr} {results.fair_value_per_share:.2f}",
                    f"{curr} {company.current_price:.2f}",
                    f"{upside:+.1%}",
                ],
            }
        )
        st.dataframe(summary, hide_index=True, use_container_width=True)


# ── Tab 3: Sensitivity Analysis ───────────────────────────────────────────────
with tab_sens:
    st.markdown("### Fair Value / Share — WACC vs Terminal Growth Rate")
    st.caption(
        "Each cell shows the implied fair value per share. "
        "All other assumptions are held constant. "
        "The black border marks your base-case inputs."
    )

    wacc_steps = np.round(
        np.arange(max(0.04, wacc - 0.025), wacc + 0.030, 0.005), 4
    ).tolist()
    tgr_steps = np.round(
        np.arange(max(0.005, tgr - 0.015), min(wacc - 0.005, tgr + 0.020), 0.005), 4
    ).tolist()

    if len(wacc_steps) < 2 or len(tgr_steps) < 2:
        st.warning("Adjust sliders to widen the WACC / TGR spread for sensitivity analysis.")
    else:
        table = sensitivity_table(dcf_inputs, wacc_steps, tgr_steps)

        row_labels = [f"{w:.1%}" for w in wacc_steps]
        col_labels = [f"{t:.1%}" for t in tgr_steps]
        df_sens = pd.DataFrame(table, index=row_labels, columns=col_labels)
        df_sens.index.name = "WACC ↓  /  TGR →"

        z = df_sens.values.astype(float)

        fig_heat = go.Figure(
            go.Heatmap(
                z=z,
                x=col_labels,
                y=row_labels,
                colorscale="RdYlGn",
                text=np.where(
                    np.isnan(z), "N/A", np.vectorize(lambda v: f"{curr} {v:.0f}")(z)
                ),
                texttemplate="%{text}",
                textfont={"size": 11},
                colorbar=dict(title=f"Fair Value ({curr})"),
            )
        )

        base_wacc_label = f"{wacc:.1%}"
        base_tgr_label = f"{tgr:.1%}"
        if base_wacc_label in row_labels and base_tgr_label in col_labels:
            wi = row_labels.index(base_wacc_label)
            ti = col_labels.index(base_tgr_label)
            fig_heat.add_shape(
                type="rect",
                x0=ti - 0.5, x1=ti + 0.5,
                y0=wi - 0.5, y1=wi + 0.5,
                line=dict(color="black", width=3),
            )
            fig_heat.add_annotation(
                x=ti, y=wi, text="BASE",
                showarrow=False,
                font=dict(size=9, color="black", family="Arial Black"),
                yshift=16,
            )

        fig_heat.update_layout(
            title=(
                f"Sensitivity: Fair Value / Share ({curr})  ·  "
                f"Base = {curr} {results.fair_value_per_share:.2f}  ·  "
                f"Market = {curr} {company.current_price:.2f}"
            ),
            xaxis_title="Terminal Growth Rate",
            yaxis_title="WACC",
            template="plotly_white",
            height=420,
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        def _color_cell(val):
            if pd.isna(val):
                return "background-color: #f0f0f0; color: #aaa"
            ratio = val / company.current_price
            if ratio >= 1.20:
                return "background-color: #27ae60; color: white"
            elif ratio >= 1.05:
                return "background-color: #82e0aa"
            elif ratio >= 0.95:
                return "background-color: #f9e79f"
            elif ratio >= 0.80:
                return "background-color: #f0b27a"
            else:
                return "background-color: #e74c3c; color: white"

        styled = df_sens.style.applymap(_color_cell).format(
            lambda v: "N/A" if pd.isna(v) else f"{curr} {v:.2f}"
        )
        st.markdown(
            f"**Colour legend vs market price ({curr} {company.current_price:.2f}):** "
            "🟢 >+20% upside  ·  🟩 +5–20%  ·  🟨 ±5%  ·  🟧 −5–20%  ·  🔴 >−20% downside"
        )
        st.dataframe(styled, use_container_width=True)

    # ── Scenario Comparison ───────────────────────────────────────────────────
    st.divider()
    st.markdown("### Bull / Base / Bear Scenario Comparison")
    st.caption(
        "Bear: growth × 0.55, WACC × 1.15, TGR − 1%.  "
        "Bull: growth × 1.35, WACC × 0.88, TGR + 1%.  "
        "Edit base-case sliders to shift all three scenarios."
    )

    scenarios = {
        "🐻 Bear": DCFInputs(
            base_fcf=base_fcf,
            fcf_growth_y1_3=g1 * 0.55,
            fcf_growth_y4_5=g2 * 0.55,
            fcf_growth_y6_10=g3 * 0.55,
            terminal_growth_rate=max(0.005, tgr - 0.01),
            forecast_years=forecast_years,
            wacc=min(wacc * 1.15, 0.25),
            cash=cash_val,
            total_debt=debt_val,
            shares_outstanding=shares_val,
        ),
        "📊 Base": dcf_inputs,
        "🐂 Bull": DCFInputs(
            base_fcf=base_fcf,
            fcf_growth_y1_3=g1 * 1.35,
            fcf_growth_y4_5=g2 * 1.35,
            fcf_growth_y6_10=g3 * 1.35,
            terminal_growth_rate=min(tgr + 0.01, 0.05),
            forecast_years=forecast_years,
            wacc=max(wacc * 0.88, 0.04),
            cash=cash_val,
            total_debt=debt_val,
            shares_outstanding=shares_val,
        ),
    }

    scenario_rows = []
    for name, inp in scenarios.items():
        try:
            r = run_dcf(inp)
            up = (r.fair_value_per_share - company.current_price) / company.current_price
            scenario_rows.append(
                {
                    "Scenario": name,
                    "WACC": f"{inp.wacc:.2%}",
                    "FCF Growth Y1–3": f"{inp.fcf_growth_y1_3:.1%}",
                    "FCF Growth Y4–5": f"{inp.fcf_growth_y4_5:.1%}",
                    "Terminal Growth": f"{inp.terminal_growth_rate:.2%}",
                    "EV": f"{curr} {r.enterprise_value:.1f}B",
                    "Fair Value / Share": f"{curr} {r.fair_value_per_share:.2f}",
                    "Upside / Downside": f"{up:+.1%}",
                }
            )
        except ValueError:
            scenario_rows.append(
                {"Scenario": name, "WACC": "—", "Fair Value / Share": "Invalid (WACC ≤ TGR)"}
            )

    st.dataframe(
        pd.DataFrame(scenario_rows).set_index("Scenario"),
        use_container_width=True,
    )
