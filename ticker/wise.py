free_cash_flows = [615, 550, 600, 640, 680]  # Millions GBP
discount_rate = 0.08
terminal_growth_rate = 0.02
years = len(free_cash_flows)

terminal_value = (
    free_cash_flows[-1]
    * (1 + terminal_growth_rate)
    / (discount_rate - terminal_growth_rate)
)

dcfs = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(free_cash_flows)]

discounted_terminal = terminal_value / ((1 + discount_rate) ** years)

enterprise_value = sum(dcfs) + discounted_terminal

shares_outstanding = 1016  # millions
equity_per_share = (enterprise_value * 1e6) / (shares_outstanding * 1e6)

print(f"Estimated enterprise value: £{enterprise_value:,.2f} million")
print(f"Estimated per share value: £{equity_per_share:.2f}")
