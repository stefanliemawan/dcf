free_cash_flows = [
    3.38,
    3.62,
    3.88,
    4.16,
    4.45,
]  # In billions USD, forward estimates per year (example)
discount_rate = 0.072  # 7.2% WACC
terminal_growth_rate = 0.02  # 2%
years = len(free_cash_flows)

# Compute terminal value for the final projected year
terminal_value = (
    free_cash_flows[-1]
    * (1 + terminal_growth_rate)
    / (discount_rate - terminal_growth_rate)
)

# Discounted cash flows
dcfs = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(free_cash_flows)]

# Discount terminal value to present
discounted_terminal = terminal_value / ((1 + discount_rate) ** years)

# Enterprise Value = sum of discounted cash flows + discounted terminal value
enterprise_value = sum(dcfs) + discounted_terminal

# Shares outstanding for FRCOY (3.07 billion)
shares_outstanding = 3.07  # billions
equity_per_share = (enterprise_value * 1e9) / (shares_outstanding * 1e9)

print(f"Estimated enterprise value: ${enterprise_value:.2f} billion")
print(f"Estimated per share value: ${equity_per_share:.2f}")
