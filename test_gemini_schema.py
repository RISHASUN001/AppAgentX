#!/usr/bin/env python3
"""
Test script to verify Gemini schema compatibility with our tools.
"""

import os
import sys
from tool.screen_content import screen_action

def test_gemini_tool_schema():
    """Test if the screen_action tool has a valid schema for Gemini."""
    print("🔍 Testing Gemini tool schema compatibility...")
    
    try:
        # Check if the tool has proper schema
        if hasattr(screen_action, 'args_schema'):
            schema = screen_action.args_schema.model_json_schema()
            print("✅ Tool schema generated successfully")
            
            # Check for problematic fields
            properties = schema.get('properties', {})
            problematic_fields = []
            
            for field_name, field_schema in properties.items():
                # Check for tuple types or missing items in arrays
                if field_schema.get('type') == 'array' and 'items' not in field_schema:
                    problematic_fields.append(f"{field_name}: array missing items")
                elif 'prefixItems' in field_schema:
                    problematic_fields.append(f"{field_name}: uses prefixItems (tuple)")
            
            if problematic_fields:
                print("❌ Found problematic schema fields:")
                for issue in problematic_fields:
                    print(f"  - {issue}")
                return False
            else:
                print("✅ No problematic schema fields found")
                return True
        else:
            print("❌ Tool missing args_schema")
            return False
            
    except Exception as e:
        print(f"❌ Schema test failed: {str(e)}")
        return False

def test_basic_tool_call():
    """Test a basic tool call to ensure it works."""
    print("🎯 Testing basic tool functionality...")
    
    try:
        # Test with back action (safe, no coordinates needed)
        result = screen_action.invoke({
            "device": "emulator-5554",
            "action": "back"
        })
        
        if result and "success" in result:
            print("✅ Basic tool call successful")
            return True
        else:
            print(f"❌ Tool call failed or returned unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Tool call test failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🚀 Testing Gemini schema compatibility...\n")
    
    # Test 1: Schema compatibility
    schema_ok = test_gemini_tool_schema()
    
    # Test 2: Basic functionality  
    function_ok = test_basic_tool_call()
    
    if schema_ok and function_ok:
        print("\n🎉 All Gemini compatibility tests passed!")
        print("✨ Your tools should now work with Gemini API")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
