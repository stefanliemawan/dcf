"""
DCF calculation engine.

All monetary values are in billions of the company's currency.
Rates are stored as decimals (e.g. 0.08 for 8%).
"""
from dataclasses import dataclass


# ── WACC ──────────────────────────────────────────────────────────────────────

@dataclass
class WACCInputs:
    risk_free_rate: float        # decimal
    equity_risk_premium: float   # decimal
    beta: float
    pre_tax_cost_of_debt: float  # decimal
    tax_rate: float              # decimal
    equity_weight: float         # decimal  (debt_weight = 1 - equity_weight)

    @property
    def debt_weight(self) -> float:
        return 1.0 - self.equity_weight

    @property
    def cost_of_equity(self) -> float:
        return self.risk_free_rate + self.beta * self.equity_risk_premium

    @property
    def after_tax_cost_of_debt(self) -> float:
        return self.pre_tax_cost_of_debt * (1.0 - self.tax_rate)

    @property
    def wacc(self) -> float:
        return (
            self.cost_of_equity * self.equity_weight
            + self.after_tax_cost_of_debt * self.debt_weight
        )


# ── DCF inputs / outputs ───────────────────────────────────────────────────────

@dataclass
class DCFInputs:
    base_fcf: float             # starting FCF (most recent year)
    fcf_growth_y1_3: float      # decimal growth rate for years 1-3
    fcf_growth_y4_5: float      # decimal growth rate for years 4-5
    fcf_growth_y6_10: float     # decimal growth rate for years 6-10 (only used if forecast_years == 10)
    terminal_growth_rate: float # perpetuity growth rate
    forecast_years: int         # 5 or 10
    wacc: float                 # decimal
    cash: float                 # billions
    total_debt: float           # billions
    shares_outstanding: float   # billions


@dataclass
class DCFResults:
    years: list[int]
    projected_fcfs: list[float]
    discounted_fcfs: list[float]
    terminal_value: float
    discounted_terminal_value: float
    pv_fcf_sum: float
    enterprise_value: float
    equity_value: float
    fair_value_per_share: float
    tv_pct: float               # % of EV from terminal value


# ── Core calculation ───────────────────────────────────────────────────────────

def _project_fcfs(
    base_fcf: float,
    g1_3: float,
    g4_5: float,
    g6_10: float,
    years: int,
) -> list[float]:
    fcfs = []
    fcf = base_fcf
    for i in range(1, years + 1):
        if i <= 3:
            g = g1_3
        elif i <= 5:
            g = g4_5
        else:
            g = g6_10
        fcf = fcf * (1.0 + g)
        fcfs.append(fcf)
    return fcfs


def run_dcf(inputs: DCFInputs) -> DCFResults:
    wacc = inputs.wacc
    tgr = inputs.terminal_growth_rate

    if wacc <= tgr:
        raise ValueError(
            f"WACC ({wacc:.2%}) must be greater than terminal growth rate ({tgr:.2%})."
        )

    fcfs = _project_fcfs(
        inputs.base_fcf,
        inputs.fcf_growth_y1_3,
        inputs.fcf_growth_y4_5,
        inputs.fcf_growth_y6_10,
        inputs.forecast_years,
    )

    discounted_fcfs = [
        fcf / (1.0 + wacc) ** (i + 1) for i, fcf in enumerate(fcfs)
    ]
    pv_fcf_sum = sum(discounted_fcfs)

    terminal_value = fcfs[-1] * (1.0 + tgr) / (wacc - tgr)
    discounted_tv = terminal_value / (1.0 + wacc) ** inputs.forecast_years

    ev = pv_fcf_sum + discounted_tv
    equity_value = ev + inputs.cash - inputs.total_debt
    fair_value = (equity_value * 1e9) / (inputs.shares_outstanding * 1e9)

    return DCFResults(
        years=list(range(1, inputs.forecast_years + 1)),
        projected_fcfs=fcfs,
        discounted_fcfs=discounted_fcfs,
        terminal_value=terminal_value,
        discounted_terminal_value=discounted_tv,
        pv_fcf_sum=pv_fcf_sum,
        enterprise_value=ev,
        equity_value=equity_value,
        fair_value_per_share=fair_value,
        tv_pct=discounted_tv / ev * 100.0 if ev > 0 else 0.0,
    )


def sensitivity_table(
    inputs: DCFInputs,
    wacc_values: list[float],
    tgr_values: list[float],
) -> list[list[float | None]]:
    """
    Returns a 2-D list [wacc_idx][tgr_idx] of fair value per share.
    None is used when WACC <= TGR (invalid).
    """
    table = []
    for w in wacc_values:
        row = []
        for t in tgr_values:
            if w <= t:
                row.append(None)
            else:
                try:
                    r = run_dcf(
                        DCFInputs(
                            base_fcf=inputs.base_fcf,
                            fcf_growth_y1_3=inputs.fcf_growth_y1_3,
                            fcf_growth_y4_5=inputs.fcf_growth_y4_5,
                            fcf_growth_y6_10=inputs.fcf_growth_y6_10,
                            terminal_growth_rate=t,
                            forecast_years=inputs.forecast_years,
                            wacc=w,
                            cash=inputs.cash,
                            total_debt=inputs.total_debt,
                            shares_outstanding=inputs.shares_outstanding,
                        )
                    )
                    row.append(r.fair_value_per_share)
                except Exception:
                    row.append(None)
            row_val = row[-1]
            _ = row_val  # suppress unused warning
        table.append(row)
    return table


# ── Legacy function (used by ticker/*.py scripts) ─────────────────────────────

def dcf_valuation(free_cash_flows, discount_rate, terminal_growth_rate, years):
    """
    Calculate intrinsic value using a simple DCF model.

    Parameters
    ----------
    free_cash_flows : list[float]
        Pre-projected FCF values for each forecast year.
    discount_rate : float
        WACC as a decimal (e.g. 0.10 for 10%).
    terminal_growth_rate : float
        Perpetuity growth rate after the forecast period.
    years : int
        Number of forecast years.

    Returns
    -------
    float
        Present value of all future cash flows including terminal value.
    """
    discounted_fcfs = [
        fcf / (1.0 + discount_rate) ** (i + 1)
        for i, fcf in enumerate(free_cash_flows)
    ]
    terminal_value = (
        free_cash_flows[-1] * (1.0 + terminal_growth_rate)
        / (discount_rate - terminal_growth_rate)
    )
    discounted_tv = terminal_value / (1.0 + discount_rate) ** years
    return sum(discounted_fcfs) + discounted_tv
