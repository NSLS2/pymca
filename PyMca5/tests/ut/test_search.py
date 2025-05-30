import pytest

from tiled.client.base import BaseClient
from tiled.queries import FullText, Key, Regex


# working tiled searches
def test_key_value_search(tiled_client: BaseClient):
    """Some docstring here."""
    # populate key and value textboxes
    input_key = "apple"
    input_value = "red"
    expected_search_results = ["a"]
    results = tiled_client.search(Key(input_key) == input_value)
    assert expected_search_results == list(results)


def test_key_regex_value_search(tiled_client: BaseClient):
    """Some docstring here."""
    # populate key and value (use regex) textboxes
    use_regex = True
    input_key = "animal"
    input_value = ".t"
    expected_search_results = ["c", "d", "e", "f", "structured_data"]
    results = tiled_client.search(Regex(input_key, input_value))
    assert expected_search_results == list(results)


def test_full_text_search(tiled_client: BaseClient):
    """Some docstring here."""
    # populate value textbox
    use_fulltext = True
    input_value = "cat"
    expected_search_results = ["c", "e", "f", "structured_data"]
    results = tiled_client.search(FullText(input_value))
    assert expected_search_results == list(results)
