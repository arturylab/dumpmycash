"""
Utility functions for the DumpMyCash application.
"""

from datetime import datetime
import pytz
from flask import session


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


def get_user_timezone():
    """
    Get the user's timezone from session or default to system timezone.
    
    Returns:
        pytz.timezone: User's timezone object
    """
    timezone_name = session.get('user_timezone')
    if timezone_name:
        try:
            return pytz.timezone(timezone_name)
        except pytz.UnknownTimeZoneError:
            pass
    
    # Fallback to system timezone or UTC
    try:
        import time
        local_tz = time.tzname[0]
        return pytz.timezone(local_tz)
    except:
        return pytz.UTC


def get_local_now():
    """
    Get current datetime in user's local timezone.
    
    Returns:
        datetime: Current datetime in user's timezone
    """
    user_tz = get_user_timezone()
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    return utc_now.astimezone(user_tz)


def localize_datetime(dt, from_tz='UTC'):
    """
    Convert a naive datetime to user's local timezone.
    
    Args:
        dt (datetime): Naive datetime object
        from_tz (str): Source timezone (default: 'UTC')
        
    Returns:
        datetime: Localized datetime in user's timezone
    """
    if dt is None:
        return None
        
    user_tz = get_user_timezone()
    
    # If datetime is naive, assume it's in from_tz
    if dt.tzinfo is None:
        source_tz = pytz.timezone(from_tz)
        dt = source_tz.localize(dt)
    
    return dt.astimezone(user_tz)


def format_local_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Format datetime in user's local timezone.
    
    Args:
        dt (datetime): Datetime to format
        format_str (str): Format string
        
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        return ''
        
    localized_dt = localize_datetime(dt)
    return localized_dt.strftime(format_str)


def format_local_date(dt, format_str='%Y-%m-%d'):
    """
    Format date in user's local timezone.
    
    Args:
        dt (datetime): Datetime to format
        format_str (str): Format string
        
    Returns:
        str: Formatted date string
    """
    return format_local_datetime(dt, format_str)
