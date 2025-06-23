#!/usr/bin/env python3
"""
Script para probar el manejo de fechas en transactions.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.transactions import parse_datetime_local
from datetime import datetime

def test_datetime_parsing():
    """Test the datetime parsing function"""
    print("Testing datetime parsing function...")
    
    # Test cases
    test_cases = [
        "2025-06-22T14:30",  # Normal datetime-local format
        "2025-06-22T14:30:00",  # With seconds
        "2025-06-22",  # Date only
        "2025-06-22T14:30Z",  # With Z suffix
        "",  # Empty string
        None,  # None value
        "invalid",  # Invalid format
    ]
    
    for test_case in test_cases:
        try:
            result = parse_datetime_local(test_case)
            print(f"✅ Input: '{test_case}' -> Output: {result}")
        except Exception as e:
            print(f"❌ Input: '{test_case}' -> Error: {e}")
    
    print("\n✅ Datetime parsing test completed!")

if __name__ == "__main__":
    test_datetime_parsing()
