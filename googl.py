from dcf import dcf_valuation


free_cash_flows = [80, 88, 96.8, 106.5, 117.1]  # Billions USD
discount_rate = 0.08  # 8% WACC
terminal_growth_rate = 0.03  # 3%
years = len(free_cash_flows)

# Compute terminal value for the final projected year (2029)
terminal_value = free_cash_flows[-1] * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)

# Discounted cash flows
dcfs = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(free_cash_flows)]

# Discount terminal value to present
discounted_terminal = terminal_value / ((1 + discount_rate) ** years)

# Enterprise Value = sum of discounted cash flows + discounted terminal value
enterprise_value = sum(dcfs) + discounted_terminal

# Optional: Estimate per-share value
shares_outstanding = 5.82  # billions
equity_per_share = (enterprise_value * 1e9) / (shares_outstanding * 1e9)

print(f"Estimated enterprise value: ${enterprise_value:.2f} billion")
print(f"Estimated per share value: ${equity_per_share:.2f}")