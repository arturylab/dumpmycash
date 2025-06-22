"""
Utility functions for the DumpMyCash application.
"""

def format_currency(amount):
    """
    Format a currency amount with proper formatting.
    
    Args:
        amount (float): The amount to format
        
    Returns:
        str: Formatted currency string (e.g., "$1,000.00")
    """
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"


def format_currency_no_symbol(amount):
    """
    Format a currency amount without the dollar symbol.
    
    Args:
        amount (float): The amount to format
        
    Returns:
        str: Formatted currency string without symbol (e.g., "1,000.00")
    """
    if amount is None:
        return "0.00"
    return f"{amount:,.2f}"
