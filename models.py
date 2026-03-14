from dataclasses import dataclass, field


@dataclass
class CompanyData:
    ticker: str
    name: str
    industry: str
    sector: str

    # Financials in billions (USD or local currency as noted)
    revenue_ttm: float
    fcf_ttm: float
    cash: float
    total_debt: float
    shares_outstanding: float  # billions
    current_price: float  # per share

    # Market
    market_cap: float  # billions
    beta: float

    # Historical
    historical_fcf_growth: float   # 3Y trailing avg FCF CAGR (decimal)

    # Company-specific defaults
    tax_rate: float

    # Mocked analyst estimates (decimal)
    analyst_fcf_growth_1y: float = 0.10   # consensus 1-year forward FCF growth
    analyst_fcf_growth_3y: float = 0.10   # consensus 3-year FCF CAGR

    # Derived metrics (decimal)
    fcf_margin_ttm: float = 0.15          # FCF / Revenue

    # Currency label
    currency: str = "USD"


# ── Industry-level assumption defaults (used to pre-fill sliders) ─────────────
INDUSTRY_DEFAULTS: dict[str, dict] = {
    "Technology": {
        "risk_free_rate": 4.5,
        "equity_risk_premium": 5.5,
        "pre_tax_cost_of_debt": 4.5,
        "terminal_growth_rate": 3.0,
        "fcf_growth_y1_3": 12.0,
        "fcf_growth_y4_5": 9.0,
        "fcf_growth_y6_10": 6.0,
    },
    "Semiconductors": {
        "risk_free_rate": 4.5,
        "equity_risk_premium": 5.5,
        "pre_tax_cost_of_debt": 4.5,
        "terminal_growth_rate": 3.0,
        "fcf_growth_y1_3": 20.0,
        "fcf_growth_y4_5": 14.0,
        "fcf_growth_y6_10": 8.0,
    },
    "E-Commerce / Cloud": {
        "risk_free_rate": 4.5,
        "equity_risk_premium": 5.5,
        "pre_tax_cost_of_debt": 4.5,
        "terminal_growth_rate": 3.0,
        "fcf_growth_y1_3": 15.0,
        "fcf_growth_y4_5": 11.0,
        "fcf_growth_y6_10": 7.0,
    },
    "Healthcare": {
        "risk_free_rate": 4.5,
        "equity_risk_premium": 5.5,
        "pre_tax_cost_of_debt": 4.0,
        "terminal_growth_rate": 2.5,
        "fcf_growth_y1_3": 6.0,
        "fcf_growth_y4_5": 5.0,
        "fcf_growth_y6_10": 4.0,
    },
    "Energy": {
        "risk_free_rate": 4.5,
        "equity_risk_premium": 5.5,
        "pre_tax_cost_of_debt": 5.5,
        "terminal_growth_rate": 1.5,
        "fcf_growth_y1_3": 3.0,
        "fcf_growth_y4_5": 2.0,
        "fcf_growth_y6_10": 1.0,
    },
    "Automotive / EV": {
        "risk_free_rate": 4.5,
        "equity_risk_premium": 5.5,
        "pre_tax_cost_of_debt": 5.5,
        "terminal_growth_rate": 2.5,
        "fcf_growth_y1_3": 18.0,
        "fcf_growth_y4_5": 13.0,
        "fcf_growth_y6_10": 8.0,
    },
    "Fintech": {
        "risk_free_rate": 4.5,
        "equity_risk_premium": 5.5,
        "pre_tax_cost_of_debt": 4.5,
        "terminal_growth_rate": 2.5,
        "fcf_growth_y1_3": 18.0,
        "fcf_growth_y4_5": 13.0,
        "fcf_growth_y6_10": 8.0,
    },
}


# ── Industry benchmark ranges (for inline hints and reference sheet) ───────────
@dataclass
class IndustryBenchmarks:
    # All % values as floats (e.g. 8.5 means 8.5%)
    wacc_range: tuple[float, float]          # typical WACC low–high
    beta_range: tuple[float, float]          # typical 5Y beta
    cost_of_debt_range: tuple[float, float]  # pre-tax KD
    tax_range: tuple[float, float]           # effective tax rate
    tgr_range: tuple[float, float]           # terminal growth rate
    fcf_growth_near: tuple[float, float]     # near-term (Y1-3) FCF growth
    fcf_growth_long: tuple[float, float]     # long-term (Y6-10) FCF growth
    notes: str                               # brief analyst context


INDUSTRY_BENCHMARKS: dict[str, IndustryBenchmarks] = {
    "Technology": IndustryBenchmarks(
        wacc_range=(8.5, 11.5),
        beta_range=(0.9, 1.5),
        cost_of_debt_range=(3.5, 5.5),
        tax_range=(12.0, 22.0),
        tgr_range=(2.5, 3.5),
        fcf_growth_near=(8.0, 18.0),
        fcf_growth_long=(4.0, 8.0),
        notes=(
            "High-growth sector. FCF margins expand as revenue scales. "
            "Cloud/SaaS companies often carry low debt and enjoy recurring revenue, "
            "supporting tighter WACCs. Use lower beta for large-cap, higher for small-cap."
        ),
    ),
    "Semiconductors": IndustryBenchmarks(
        wacc_range=(9.0, 12.5),
        beta_range=(1.2, 2.0),
        cost_of_debt_range=(3.5, 5.5),
        tax_range=(10.0, 18.0),
        tgr_range=(2.5, 3.5),
        fcf_growth_near=(15.0, 35.0),
        fcf_growth_long=(5.0, 10.0),
        notes=(
            "Highly cyclical. AI-driven chips (NVDA) command premium multiples and "
            "exceptional near-term growth. Use higher beta and WACC for pure-play vs "
            "diversified semi companies. Capex intensity reduces FCF margins."
        ),
    ),
    "E-Commerce / Cloud": IndustryBenchmarks(
        wacc_range=(8.5, 11.5),
        beta_range=(1.0, 1.6),
        cost_of_debt_range=(4.0, 5.5),
        tax_range=(12.0, 22.0),
        tgr_range=(2.5, 3.5),
        fcf_growth_near=(12.0, 28.0),
        fcf_growth_long=(5.0, 9.0),
        notes=(
            "Cloud (AWS, Azure) is high-margin and recurring; retail is low-margin but high-volume. "
            "FCF can swing dramatically with capex cycles. Logistic investments depress "
            "near-term FCF; normalise for mid-cycle capex."
        ),
    ),
    "Healthcare": IndustryBenchmarks(
        wacc_range=(7.5, 10.0),
        beta_range=(0.4, 0.9),
        cost_of_debt_range=(3.5, 5.0),
        tax_range=(14.0, 24.0),
        tgr_range=(2.0, 3.0),
        fcf_growth_near=(4.0, 10.0),
        fcf_growth_long=(3.0, 6.0),
        notes=(
            "Defensive sector with relatively stable cash flows. Large pharma face "
            "patent-cliff risk; biotech more volatile. Effective tax rates vary widely "
            "due to IP structures. Use beta <0.8 for diversified pharma, higher for biotech."
        ),
    ),
    "Energy": IndustryBenchmarks(
        wacc_range=(9.5, 13.5),
        beta_range=(0.8, 1.4),
        cost_of_debt_range=(4.5, 6.5),
        tax_range=(20.0, 30.0),
        tgr_range=(1.0, 2.0),
        fcf_growth_near=(-2.0, 8.0),
        fcf_growth_long=(0.0, 3.0),
        notes=(
            "Highly commodity-price sensitive. FCF varies with oil/gas prices; "
            "normalise to mid-cycle commodity price (~$70–80/bbl for oil). "
            "Capital-intensive with high maintenance capex. TGR should reflect "
            "energy transition risk — use 1–2% at most."
        ),
    ),
    "Automotive / EV": IndustryBenchmarks(
        wacc_range=(9.5, 13.5),
        beta_range=(1.5, 2.5),
        cost_of_debt_range=(4.5, 7.0),
        tax_range=(10.0, 22.0),
        tgr_range=(2.0, 3.0),
        fcf_growth_near=(10.0, 30.0),
        fcf_growth_long=(4.0, 8.0),
        notes=(
            "Capital-heavy with long product cycles. EV companies in growth phase "
            "often have thin/negative FCF; use conservative near-term growth. "
            "High beta reflects disruption risk. Use higher WACC for companies "
            "with unproven unit economics."
        ),
    ),
    "Fintech": IndustryBenchmarks(
        wacc_range=(9.0, 12.0),
        beta_range=(0.9, 1.5),
        cost_of_debt_range=(4.0, 6.0),
        tax_range=(18.0, 28.0),
        tgr_range=(2.0, 3.0),
        fcf_growth_near=(12.0, 28.0),
        fcf_growth_long=(5.0, 10.0),
        notes=(
            "High-growth with network-effect moats. Payment processors have very "
            "high FCF margins once scaled. Regulatory risk can compress valuations. "
            "Use effective tax rate (often lower due to international structures)."
        ),
    ),
}


# ── Mocked company data ────────────────────────────────────────────────────────
COMPANIES: dict[str, CompanyData] = {
    "GOOGL": CompanyData(
        ticker="GOOGL",
        name="Alphabet Inc.",
        industry="Technology",
        sector="Internet / Search",
        revenue_ttm=350.0,
        fcf_ttm=52.0,
        cash=95.0,
        total_debt=28.0,
        shares_outstanding=12.3,
        current_price=172.0,
        market_cap=2115.0,
        beta=1.05,
        historical_fcf_growth=0.14,
        tax_rate=0.15,
        analyst_fcf_growth_1y=0.10,
        analyst_fcf_growth_3y=0.13,
        fcf_margin_ttm=0.149,
    ),
    "AAPL": CompanyData(
        ticker="AAPL",
        name="Apple Inc.",
        industry="Technology",
        sector="Consumer Electronics",
        revenue_ttm=391.0,
        fcf_ttm=108.0,
        cash=65.0,
        total_debt=101.0,
        shares_outstanding=15.2,
        current_price=227.0,
        market_cap=3450.0,
        beta=1.24,
        historical_fcf_growth=0.08,
        tax_rate=0.15,
        analyst_fcf_growth_1y=0.05,
        analyst_fcf_growth_3y=0.07,
        fcf_margin_ttm=0.276,
    ),
    "MSFT": CompanyData(
        ticker="MSFT",
        name="Microsoft Corporation",
        industry="Technology",
        sector="Software / Cloud",
        revenue_ttm=245.0,
        fcf_ttm=74.0,
        cash=75.0,
        total_debt=45.0,
        shares_outstanding=7.43,
        current_price=415.0,
        market_cap=3083.0,
        beta=0.90,
        historical_fcf_growth=0.18,
        tax_rate=0.18,
        analyst_fcf_growth_1y=0.14,
        analyst_fcf_growth_3y=0.15,
        fcf_margin_ttm=0.302,
    ),
    "AMZN": CompanyData(
        ticker="AMZN",
        name="Amazon.com Inc.",
        industry="E-Commerce / Cloud",
        sector="E-Commerce / Cloud",
        revenue_ttm=638.0,
        fcf_ttm=53.0,
        cash=86.0,
        total_debt=58.0,
        shares_outstanding=10.5,
        current_price=222.0,
        market_cap=2331.0,
        beta=1.15,
        historical_fcf_growth=0.40,
        tax_rate=0.14,
        analyst_fcf_growth_1y=0.22,
        analyst_fcf_growth_3y=0.26,
        fcf_margin_ttm=0.083,
    ),
    "META": CompanyData(
        ticker="META",
        name="Meta Platforms Inc.",
        industry="Technology",
        sector="Social Media",
        revenue_ttm=164.0,
        fcf_ttm=53.0,
        cash=77.0,
        total_debt=29.0,
        shares_outstanding=2.55,
        current_price=607.0,
        market_cap=1548.0,
        beta=1.25,
        historical_fcf_growth=0.35,
        tax_rate=0.13,
        analyst_fcf_growth_1y=0.20,
        analyst_fcf_growth_3y=0.18,
        fcf_margin_ttm=0.323,
    ),
    "NVDA": CompanyData(
        ticker="NVDA",
        name="NVIDIA Corporation",
        industry="Semiconductors",
        sector="Semiconductors / AI",
        revenue_ttm=130.0,
        fcf_ttm=60.0,
        cash=43.0,
        total_debt=8.5,
        shares_outstanding=24.4,
        current_price=134.0,
        market_cap=3270.0,
        beta=1.65,
        historical_fcf_growth=0.80,
        tax_rate=0.13,
        analyst_fcf_growth_1y=0.32,
        analyst_fcf_growth_3y=0.28,
        fcf_margin_ttm=0.462,
    ),
    "TSLA": CompanyData(
        ticker="TSLA",
        name="Tesla Inc.",
        industry="Automotive / EV",
        sector="Automotive / EV",
        revenue_ttm=97.0,
        fcf_ttm=3.6,
        cash=36.0,
        total_debt=7.2,
        shares_outstanding=3.2,
        current_price=280.0,
        market_cap=896.0,
        beta=2.30,
        historical_fcf_growth=0.25,
        tax_rate=0.12,
        analyst_fcf_growth_1y=0.22,
        analyst_fcf_growth_3y=0.30,
        fcf_margin_ttm=0.037,
    ),
    "JNJ": CompanyData(
        ticker="JNJ",
        name="Johnson & Johnson",
        industry="Healthcare",
        sector="Pharmaceuticals",
        revenue_ttm=88.0,
        fcf_ttm=16.0,
        cash=28.0,
        total_debt=40.0,
        shares_outstanding=2.4,
        current_price=155.0,
        market_cap=372.0,
        beta=0.60,
        historical_fcf_growth=0.03,
        tax_rate=0.17,
        analyst_fcf_growth_1y=0.04,
        analyst_fcf_growth_3y=0.05,
        fcf_margin_ttm=0.182,
    ),
    "WISE": CompanyData(
        ticker="WISE",
        name="Wise plc",
        industry="Fintech",
        sector="Payments",
        revenue_ttm=1.2,
        fcf_ttm=0.55,
        cash=0.65,
        total_debt=0.10,
        shares_outstanding=1.016,
        current_price=9.20,
        market_cap=9.34,
        beta=1.10,
        historical_fcf_growth=0.30,
        tax_rate=0.20,
        analyst_fcf_growth_1y=0.22,
        analyst_fcf_growth_3y=0.24,
        fcf_margin_ttm=0.458,
        currency="GBP",
    ),
    "FRCOY": CompanyData(
        ticker="FRCOY",
        name="Fairfax India Holdings",
        industry="Fintech",
        sector="Diversified Financials",
        revenue_ttm=0.85,
        fcf_ttm=0.30,
        cash=0.40,
        total_debt=0.20,
        shares_outstanding=0.082,
        current_price=14.50,
        market_cap=1.19,
        beta=0.95,
        historical_fcf_growth=0.12,
        tax_rate=0.21,
        analyst_fcf_growth_1y=0.10,
        analyst_fcf_growth_3y=0.12,
        fcf_margin_ttm=0.353,
    ),
}
