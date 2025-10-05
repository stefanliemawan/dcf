def dcf_valuation(free_cash_flows, discount_rate, terminal_growth_rate, years):
    """
    Calculate the intrinsic value using DCF model.
    
    Parameters:
    - free_cash_flows: list of free cash flow values for forecast years
    - discount_rate: discount rate as a decimal (e.g., 0.10 for 10%)
    - terminal_growth_rate: perpetuity growth rate after forecast period
    - years: number of forecast years
    
    Returns:
    - intrinsic_value: present value of all future cash flows including terminal value
    """
    # Discount the forecasted cash flows
    discounted_cash_flows = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(free_cash_flows)]
    
    # Calculate terminal value using perpetuity growth formula
    terminal_value = free_cash_flows[-1] * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
    
    # Discount the terminal value back to present value
    discounted_terminal_value = terminal_value / ((1 + discount_rate) ** years)
    
    # Sum all discounted cash flows and terminal value
    intrinsic_value = sum(discounted_cash_flows) + discounted_terminal_value
    
    return intrinsic_value