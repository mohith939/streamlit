"""
Tests for the formatter module.
"""
import pytest
import json
from modules.formatter import Formatter

def test_format_modules():
    """Test the format_modules method."""
    formatter = Formatter()
    
    # Test with empty modules
    assert formatter.format_modules([]) == []
    
    # Test with a single module
    modules = [
        {
            "module": "Test Module",
            "description": "Test description",
            "submodules": {
                "Submodule 1": "Description 1",
                "Submodule 2": "Description 2"
            }
        }
    ]
    
    formatted = formatter.format_modules(modules)
    assert len(formatted) == 1
    assert formatted[0]["module"] == "Test Module"
    assert formatted[0]["Description"] == "Test description"
    assert len(formatted[0]["Submodules"]) == 2
    assert formatted[0]["Submodules"]["Submodule 1"] == "Description 1"
    assert formatted[0]["Submodules"]["Submodule 2"] == "Description 2"

def test_to_json():
    """Test the to_json method."""
    formatter = Formatter()
    
    # Test with empty modules
    json_str = formatter.to_json([])
    assert json.loads(json_str) == []
    
    # Test with a single module
    modules = [
        {
            "module": "Test Module",
            "description": "Test description",
            "submodules": {
                "Submodule 1": "Description 1",
                "Submodule 2": "Description 2"
            }
        }
    ]
    
    json_str = formatter.to_json(modules)
    parsed = json.loads(json_str)
    assert len(parsed) == 1
    assert parsed[0]["module"] == "Test Module"
    assert parsed[0]["Description"] == "Test description"
    assert len(parsed[0]["Submodules"]) == 2
    assert parsed[0]["Submodules"]["Submodule 1"] == "Description 1"
    assert parsed[0]["Submodules"]["Submodule 2"] == "Description 2"
