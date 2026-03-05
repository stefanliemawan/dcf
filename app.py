"""
DCF Valuation Model — Streamlit App

Run with:
    streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from dcf import DCFInputs, WACCInputs, run_dcf, sensitivity_table
from models import COMPANIES, INDUSTRY_DEFAULTS

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DCF Valuation Model",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal custom CSS
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    .stMetric label { font-size: 0.78rem; color: #888; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar: company selector ──────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 DCF Model")
    st.markdown("*Discounted Cash Flow Valuation*")
    st.divider()

    ticker = st.selectbox(
        "Company",
        options=list(COMPANIES.keys()),
        format_func=lambda x: f"{x}  —  {COMPANIES[x].name}",
    )

    # Detect company change → reset all widget keys so sliders revert to defaults
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

    st.markdown(f"**{company.name}**")
    st.caption(f"{company.sector}  ·  {company.industry}")
    st.divider()

    st.markdown("**Industry Benchmarks**")
    st.caption(
        f"Default WACC ≈ {(ind['risk_free_rate'] + company.beta * ind['equity_risk_premium']):.1f}%  \n"
        f"Terminal growth ≈ {ind['terminal_growth_rate']:.1f}%"
    )
    st.divider()
    st.caption("📌 Data is mocked for demonstration. FMP API integration coming soon.")

# ── Company overview ───────────────────────────────────────────────────────────
curr = company.currency
st.title(f"{company.name}  ({ticker})")
st.caption(f"{company.sector}  ·  {company.industry}  ·  currency: {curr}")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Revenue TTM", f"{curr} {company.revenue_ttm:.1f}B")
c2.metric("FCF TTM", f"{curr} {company.fcf_ttm:.1f}B")
c3.metric("Cash", f"{curr} {company.cash:.1f}B")
c4.metric("Total Debt", f"{curr} {company.total_debt:.1f}B")
c5.metric("Shares Out.", f"{company.shares_outstanding:.3f}B")
c6.metric("Market Price", f"{curr} {company.current_price:.2f}")

st.divider()

# ── Assumptions: three columns ────────────────────────────────────────────────
col_wacc, col_growth, col_bs = st.columns([1.3, 1.3, 0.9])

# ── WACC Builder ──────────────────────────────────────────────────────────────
with col_wacc:
    st.subheader("⚙️ WACC Builder")

    # Capital structure defaults based on market data
    default_eq_wt = min(
        0.99,
        round(company.market_cap / (company.market_cap + company.total_debt), 2),
    )

    rf_pct = st.slider(
        "Risk-Free Rate (10Y Treasury)",
        min_value=1.0, max_value=7.0,
        value=float(ind["risk_free_rate"]),
        step=0.1, format="%.1f%%", key="rf",
    )
    erp_pct = st.slider(
        "Equity Risk Premium",
        min_value=3.0, max_value=10.0,
        value=float(ind["equity_risk_premium"]),
        step=0.1, format="%.1f%%", key="erp",
    )
    beta_val = st.slider(
        "Beta",
        min_value=0.2, max_value=3.5,
        value=float(round(company.beta, 2)),
        step=0.05, key="beta",
    )

    rf = rf_pct / 100
    erp = erp_pct / 100
    ke = rf + beta_val * erp
    st.info(f"Cost of Equity (CAPM) = **{ke:.2%}**  \n`Rf {rf_pct:.1f}% + β {beta_val:.2f} × ERP {erp_pct:.1f}%`")

    kd_pct = st.slider(
        "Pre-Tax Cost of Debt",
        min_value=1.0, max_value=12.0,
        value=float(ind["pre_tax_cost_of_debt"]),
        step=0.1, format="%.1f%%", key="kd",
    )
    tax_pct = st.slider(
        "Effective Tax Rate",
        min_value=5.0, max_value=40.0,
        value=float(round(company.tax_rate * 100, 0)),
        step=1.0, format="%.0f%%", key="tax",
    )

    kd = kd_pct / 100
    tax = tax_pct / 100
    kd_at = kd * (1 - tax)
    st.info(f"After-Tax Cost of Debt = **{kd_at:.2%}**  \n`Kd {kd_pct:.1f}% × (1 − {tax_pct:.0f}%)`")

    eq_w_pct = st.slider(
        "Equity Weight (capital structure)",
        min_value=10.0, max_value=100.0,
        value=float(round(default_eq_wt * 100, 0)),
        step=1.0, format="%.0f%%", key="eq_w",
    )
    eq_w = eq_w_pct / 100
    dbt_w = 1.0 - eq_w

    wacc_inputs = WACCInputs(
        risk_free_rate=rf,
        equity_risk_premium=erp,
        beta=beta_val,
        pre_tax_cost_of_debt=kd,
        tax_rate=tax,
        equity_weight=eq_w,
    )
    wacc = wacc_inputs.wacc

    st.success(
        f"**WACC = {wacc:.2%}**  \n"
        f"`{ke:.2%} × {eq_w_pct:.0f}% + {kd_at:.2%} × {dbt_w*100:.0f}%`"
    )

# ── Growth Assumptions ────────────────────────────────────────────────────────
with col_growth:
    st.subheader("📈 Growth Assumptions")

    forecast_years = st.radio(
        "Forecast Period", [5, 10], index=1, horizontal=True, key="forecast_years"
    )

    g1_pct = st.slider(
        "FCF Growth — Years 1–3",
        min_value=-10.0, max_value=60.0,
        value=float(ind["fcf_growth_y1_3"]),
        step=0.5, format="%.1f%%", key="g1",
    )
    g2_pct = st.slider(
        "FCF Growth — Years 4–5",
        min_value=-10.0, max_value=50.0,
        value=float(ind["fcf_growth_y4_5"]),
        step=0.5, format="%.1f%%", key="g2",
    )
    if forecast_years == 10:
        g3_pct = st.slider(
            "FCF Growth — Years 6–10",
            min_value=-10.0, max_value=40.0,
            value=float(ind["fcf_growth_y6_10"]),
            step=0.5, format="%.1f%%", key="g3",
        )
    else:
        g3_pct = g2_pct  # not used for 5-year model

    tgr_pct = st.slider(
        "Terminal Growth Rate",
        min_value=0.0, max_value=5.0,
        value=float(ind["terminal_growth_rate"]),
        step=0.25, format="%.2f%%", key="tgr",
    )

    g1 = g1_pct / 100
    g2 = g2_pct / 100
    g3 = g3_pct / 100
    tgr = tgr_pct / 100

    st.caption(
        f"3-yr hist. FCF growth: **{company.historical_fcf_growth:.0%}**  \n"
        f"Terminal growth ≤ long-run GDP (~2–3%) is recommended."
    )

    # Guard: WACC must exceed TGR
    if wacc <= tgr:
        st.error(
            f"WACC ({wacc:.2%}) must be above terminal growth ({tgr:.2%}). "
            "Adjust sliders."
        )

# ── Balance Sheet ─────────────────────────────────────────────────────────────
with col_bs:
    st.subheader("🏦 Balance Sheet")

    base_fcf = st.number_input(
        f"Base FCF ({curr} B)", min_value=0.01, max_value=1000.0,
        value=float(company.fcf_ttm), step=0.5, key="base_fcf",
    )
    cash_val = st.number_input(
        f"Cash & Equivalents ({curr} B)", min_value=0.0, max_value=1000.0,
        value=float(company.cash), step=0.5, key="cash",
    )
    debt_val = st.number_input(
        f"Total Debt ({curr} B)", min_value=0.0, max_value=1000.0,
        value=float(company.total_debt), step=0.5, key="debt",
    )
    shares_val = st.number_input(
        "Shares Outstanding (B)", min_value=0.001, max_value=100.0,
        value=float(company.shares_outstanding), step=0.01, key="shares",
    )

    net_debt = debt_val - cash_val
    st.caption(
        f"Net Debt: **{curr} {net_debt:.1f}B**  \n"
        f"({'Net Cash' if net_debt < 0 else 'Net Debt'} position)"
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
r2.metric("PV of Terminal Value", f"{curr} {results.discounted_terminal_value:.1f}B")
r3.metric("Enterprise Value", f"{curr} {results.enterprise_value:.1f}B")
r4.metric("Equity Value", f"{curr} {results.equity_value:.1f}B")
r5.metric(
    "Fair Value / Share",
    f"{curr} {results.fair_value_per_share:.2f}",
    delta=f"Market: {curr} {company.current_price:.2f}",
)
r6.metric(
    "Upside / Downside",
    f"{upside:+.1%}",
    delta=f"{upside:+.1%}",
    delta_color="normal",
)

st.divider()

# ── Tabs: Projections | Value Bridge | Sensitivity ────────────────────────────
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
                measure=[
                    "relative", "relative", "total",
                    "relative", "relative", "total",
                ],
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
        # EV composition donut
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

        # Summary table
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
        "Each cell shows the implied fair value per share under that combination of "
        "WACC and terminal growth rate, holding all other assumptions constant."
    )

    # Build ranges: ±2.5% around current WACC, ±1.5% around current TGR
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

        # Build DataFrame  (rows = WACC, cols = TGR)
        row_labels = [f"{w:.1%}" for w in wacc_steps]
        col_labels = [f"{t:.1%}" for t in tgr_steps]
        df_sens = pd.DataFrame(table, index=row_labels, columns=col_labels)
        df_sens.index.name = "WACC ↓  /  TGR →"

        # Replace None with NaN for Plotly
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

        # Highlight the current base case cell
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
                x=ti, y=wi,
                text="BASE",
                showarrow=False,
                font=dict(size=9, color="black", family="Arial Black"),
                yshift=16,
            )

        fig_heat.add_hline(
            y=base_wacc_label if base_wacc_label in row_labels else row_labels[len(row_labels) // 2],
            line_dash="dash", line_color="black", line_width=1, opacity=0.4,
        )
        fig_heat.update_layout(
            title=f"Sensitivity: Fair Value / Share ({curr})  ·  Base = {curr} {results.fair_value_per_share:.2f}  ·  Market = {curr} {company.current_price:.2f}",
            xaxis_title="Terminal Growth Rate",
            yaxis_title="WACC",
            template="plotly_white",
            height=420,
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # Colour-coded table view
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
            f"**Legend:** 🟢 >+20% | 🟩 +5–20% | 🟨 ±5% of market ({curr} {company.current_price:.2f}) | 🟧 −5–20% | 🔴 <−20%"
        )
        st.dataframe(styled, use_container_width=True)

    # ── Scenario Comparison ──────────────────────────────────────────────────
    st.divider()
    st.markdown("### Bull / Base / Bear Scenario Comparison")

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
            scenario_rows.append({"Scenario": name, "WACC": "—", "Fair Value / Share": "Invalid"})

    st.dataframe(
        pd.DataFrame(scenario_rows).set_index("Scenario"),
        use_container_width=True,
    )
