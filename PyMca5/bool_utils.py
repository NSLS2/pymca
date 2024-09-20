#!/usr/bin/env python

"""bool_utils.py

    Helpers to convert strings (such as environment variables) to booleans.
"""

def enforce_bool(value) -> bool:
    """Convert truthy/falsey to True/False (or None)."""
    empty_values = {"none", "null", "undefined", ''}
    false_values = {"false", "no", "n", "0"}
    true_values = {"true", "yes", "y"}

    str_value = str(value).lower().strip()
    if str_value in empty_values:
        return None
    if str_value in false_values:
        return False
    if str_value in true_values:
        return True

    return bool(value)


def returns_bool(func):
    """Force the return value of 'func' to be a boolean."""
    def inner_func(*args, **kwargs):
        return enforce_bool(
            func(*args, **kwargs)
        )
    
    return inner_func
