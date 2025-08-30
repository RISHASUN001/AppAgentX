#!/usr/bin/env python3
"""
Test script to verify that the fixes for action execution are working properly.
This script tests:
1. ADB connectivity and device detection
2. Screenshot functionality
3. OmniParser integration
4. Action execution
"""

import os
import sys
import json
import time
from tool.screen_content import list_all_devices, get_device_size, take_screenshot, screen_element, screen_action

def test_adb_connectivity():
    """Test if ADB is working and devices are connected"""
    print("🔍 Testing ADB connectivity...")
    
    devices = list_all_devices()
    if not devices:
        print("❌ No devices found. Please ensure your emulator is running and connected.")
        return False
    
    print(f"✅ Found {len(devices)} device(s): {devices}")
    
    # Test device size detection
    for device in devices:
        try:
            size = get_device_size.invoke(device)
            if isinstance(size, dict) and 'width' in size and 'height' in size:
                print(f"✅ Device {device} size: {size['width']}x{size['height']}")
            else:
                print(f"❌ Failed to get size for device {device}: {size}")
                return False
        except Exception as e:
            print(f"❌ Error getting device size: {str(e)}")
            return False
    
    return True

def test_screenshot_functionality(device):
    """Test screenshot capture"""
    print("📸 Testing screenshot functionality...")
    
    try:
        screenshot_path = take_screenshot.invoke({
            "device": device,
            "app_name": "test",
            "step": 1
        })
        
        if os.path.exists(screenshot_path):
            print(f"✅ Screenshot captured successfully: {screenshot_path}")
            return screenshot_path
        else:
            print(f"❌ Screenshot file not found: {screenshot_path}")
            return None
    except Exception as e:
        print(f"❌ Screenshot capture failed: {str(e)}")
        return None

def test_omni_parser(screenshot_path):
    """Test OmniParser integration"""
    print("🧠 Testing OmniParser integration...")
    
    try:
        result = screen_element.invoke({"image_path": screenshot_path})
        
        if "error" in result:
            print(f"❌ OmniParser failed: {result['error']}")
            return None
        
        if "parsed_content_json_path" in result:
            json_path = result["parsed_content_json_path"]
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    elements = json.load(f)
                print(f"✅ OmniParser success: Found {len(elements)} elements")
                print(f"✅ Parsed JSON saved to: {json_path}")
                return json_path
            else:
                print(f"❌ Parsed JSON file not found: {json_path}")
                return None
        else:
            print("❌ OmniParser result missing parsed_content_json_path")
            return None
    except Exception as e:
        print(f"❌ OmniParser test failed: {str(e)}")
        return None

def test_action_execution(device):
    """Test basic action execution"""
    print("🎯 Testing action execution...")
    
    # Test back button (safe action that won't interfere with UI)
    try:
        result = screen_action.invoke({
            "device": device,
            "action": "back"
        })
        
        result_data = json.loads(result)
        if result_data.get("status") == "success":
            print("✅ Action execution test passed (back button)")
            return True
        else:
            print(f"❌ Action execution failed: {result_data.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Action execution test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting AppAgentX fix verification tests...\n")
    
    # Test 1: ADB Connectivity
    if not test_adb_connectivity():
        print("\n❌ ADB connectivity test failed. Please check your setup.")
        sys.exit(1)
    
    # Get the first available device
    devices = list_all_devices()
    test_device = devices[0]
    print(f"\n🎯 Using device: {test_device}")
    
    # Test 2: Screenshot functionality
    screenshot_path = test_screenshot_functionality(test_device)
    if not screenshot_path:
        print("\n❌ Screenshot test failed.")
        sys.exit(1)
    
    # Test 3: OmniParser integration
    json_path = test_omni_parser(screenshot_path)
    if not json_path:
        print("\n❌ OmniParser test failed.")
        sys.exit(1)
    
    # Test 4: Action execution
    if not test_action_execution(test_device):
        print("\n❌ Action execution test failed.")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Your AppAgentX setup is working correctly.")
    print(f"📱 Device: {test_device}")
    print(f"📸 Last screenshot: {screenshot_path}")
    print(f"📋 Parsed elements: {json_path}")
    print("\n✨ You can now run your AppAgentX tasks with confidence!")

if __name__ == "__main__":
    main()
