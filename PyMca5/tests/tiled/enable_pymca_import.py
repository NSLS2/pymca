#!/usr/bin/env python

"""enable_pymca_import.py

    Enable tests to import PyMca5 modules.

    By default PyMca5 cannot be imported when called from a source directory.
    Import _this_ module before importing PyMca5 or one of its submodules
    to bypass that limitation, or override this behavior
    by setting the environment varriable ALLOW_PYMCA_IMPORT.

    Examples:

    ```python
    import enable_pymca_import  # noqa: F401

    # These imports will now succeed!
    import PyMca5
    from PyMca5.PyMcaCore.DataObject import DataObject
    ```

    ```shell
    # These tests will fail to import PyMca5
    ALLOW_PYMCA_IMPORT=0 python -m pytest
    ALLOW_PYMCA_IMPORT=false python -m pytest
    ALLOW_PYMCA_IMPORT=FALSE python -m pytest

    # These tests will successfully import PyMca5
    ALLOW_PYMCA_IMPORT=1 python -m pytest
    ALLOW_PYMCA_IMPORT=true python -m pytest
    ALLOW_PYMCA_IMPORT=TRUE python -m pytest
    ```

    Tests that want to import PyMca5 must be in a directory
    that does NOT contain an __init__.py file. Otherwise, pytest
    will attempt to import PyMca5 before the tests are collected.
"""

import os


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


@returns_bool
def get_bool_env_var(name: str, value: bool):
    """Get the named boolean environment variable; else return 'value'."""
    return os.environ.get(name, value)


# Set ALLOW_PYMCA_IMPORT = True to enable tests that immport PyMca5
ALLOW_PYMCA_IMPORT = get_bool_env_var("ALLOW_PYMCA_IMPORT", True)

# "import PyMca5" fails unless this environment variable is set to "True"
os.environ["ALLOW_PYMCA_IMPORT"] = str(ALLOW_PYMCA_IMPORT)
