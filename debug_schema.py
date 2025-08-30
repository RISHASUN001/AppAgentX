#!/usr/bin/env python3

from typing import Tuple, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import json

@tool
def test_screen_action(
    start: Optional[Tuple[int, int]] = None,
    end: Optional[Tuple[int, int]] = None,
) -> str:
    """Test tool with tuple parameters."""
    return "test"

# Get the tool's schema
if hasattr(test_screen_action, 'args_schema'):
    schema = test_screen_action.args_schema.model_json_schema()
    print("Tool schema:")
    print(json.dumps(schema, indent=2))
    
    # Check specific properties
    if 'properties' in schema:
        for prop_name, prop_schema in schema['properties'].items():
            print(f"\nProperty '{prop_name}':")
            print(json.dumps(prop_schema, indent=2))
