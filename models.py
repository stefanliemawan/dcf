from dataclasses import dataclass


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

    # Defaults
    historical_fcf_growth: float  # trailing avg annual FCF growth
    tax_rate: float

    # Currency label for display
    currency: str = "USD"


# ── Industry-level assumption defaults ────────────────────────────────────────
INDUSTRY_DEFAULTS: dict[str, dict] = {
    "Technology": {
        "risk_free_rate": 4.5,        # %
        "equity_risk_premium": 5.5,   # %
        "pre_tax_cost_of_debt": 4.5,  # %
        "terminal_growth_rate": 3.0,  # %
        "fcf_growth_y1_3": 12.0,      # %
        "fcf_growth_y4_5": 9.0,       # %
        "fcf_growth_y6_10": 6.0,      # %
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
    ),
    "WISE": CompanyData(
        ticker="WISE",
        name="Wise plc",
        industry="Fintech",
        sector="Payments",
        revenue_ttm=1.2,        # £ billions
        fcf_ttm=0.55,
        cash=0.65,
        total_debt=0.10,
        shares_outstanding=1.016,
        current_price=9.20,     # £ per share
        market_cap=9.34,
        beta=1.10,
        historical_fcf_growth=0.30,
        tax_rate=0.20,
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
    ),
}
