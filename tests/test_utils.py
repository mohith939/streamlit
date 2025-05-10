"""
Tests for the utils module.
"""
import pytest
from modules.utils import is_valid_url, normalize_url, clean_text

def test_is_valid_url():
    """Test the is_valid_url function."""
    # Valid URLs
    assert is_valid_url("https://docs.python.org/3/tutorial/") is True
    assert is_valid_url("http://example.com") is True
    
    # Invalid URLs
    assert is_valid_url("not a url") is False
    assert is_valid_url("") is False
    assert is_valid_url(None) is False

def test_normalize_url():
    """Test the normalize_url function."""
    # URLs with trailing slash
    assert normalize_url("https://docs.python.org/3/tutorial/") == "https://docs.python.org/3/tutorial/"
    
    # URLs without trailing slash
    assert normalize_url("https://docs.python.org/3/tutorial") == "https://docs.python.org/3/tutorial/"
    
    # URLs with query parameters
    assert normalize_url("https://docs.python.org/3/tutorial/?q=test") == "https://docs.python.org/3/tutorial/?q=test"
    
    # URLs with fragments
    assert normalize_url("https://docs.python.org/3/tutorial/#section") == "https://docs.python.org/3/tutorial/#section"

def test_clean_text():
    """Test the clean_text function."""
    # Text with extra whitespace
    assert clean_text("  Hello  World  ") == "Hello World"
    
    # Text with newlines
    assert clean_text("Hello\nWorld") == "Hello World"
    
    # Text with tabs
    assert clean_text("Hello\tWorld") == "Hello World"
    
    # Empty text
    assert clean_text("") == ""
    assert clean_text(None) == ""
