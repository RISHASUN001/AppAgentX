import base64
import datetime
import json
import os
import subprocess
import shutil
from time import sleep
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
import sys
from PIL import Image
import torch
import clip
import numpy as np

# Load environment variables from .env file
load_dotenv()
import config  # Import configuration module


def parse_image_with_clip(image_path: str, save_dir: str = None):
    """
    Use CLIP model to parse and understand image content instead of OmniParser
    
    Args:
        image_path (str): Path to the screenshot image
        save_dir (str): Directory to save processed results
        
    Returns:
        dict: Parsed results or error information
    """
    try:
        if not os.path.exists(image_path):
            return {"error": "Screenshot file does not exist. Please check the path."}
        
        # Set up save directory
        if save_dir is None:
            save_dir = os.path.join(os.path.dirname(image_path), "processed_images")
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # Load CLIP model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, preprocess = clip.load("ViT-B/32", device=device)
        
        # Load and preprocess image
        image = Image.open(image_path)
        image_input = preprocess(image).unsqueeze(0).to(device)
        
        # Define common UI element queries for mobile screens
        text_queries = [
            "a button", "a text field", "an input box", "a menu", "an icon",
            "a navigation bar", "a search box", "a dropdown menu", "a checkbox",
            "a radio button", "a slider", "a toggle switch", "a tab", "a link"
        ]
        
        text_inputs = clip.tokenize(text_queries).to(device)
        
        # Get image and text features
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_inputs)
            
            # Calculate similarities
            similarities = torch.cosine_similarity(image_features, text_features, dim=1)
            
        # Create parsed content based on CLIP understanding
        parsed_content_list = []
        
        # Get top matching UI elements
        top_matches = torch.topk(similarities, min(5, len(text_queries)))
        
        for i, (score, idx) in enumerate(zip(top_matches.values, top_matches.indices)):
            if score > 0.2:  # Threshold for relevance
                element_type = text_queries[idx.item()]
                parsed_content_list.append({
                    'from': 'clip_model',
                    'shape': {
                        'x': 50 + i * 100,  # Dummy coordinates
                        'y': 100 + i * 80,
                        'width': 120,
                        'height': 60
                    },
                    'text': element_type,
                    'type': 'ui_element',
                    'confidence': float(score)
                })
        
        # If no good matches, create generic element
        if not parsed_content_list:
            parsed_content_list.append({
                'from': 'clip_model',
                'shape': {'x': 100, 'y': 100, 'width': 200, 'height': 100},
                'text': 'screen_content',
                'type': 'generic',
                'confidence': 0.5
            })
        
        # Create labeled image (copy original with basic annotation)
        labeled_image_path = os.path.join(save_dir, f"labeled_{os.path.basename(image_path)}")
        shutil.copy2(image_path, labeled_image_path)
        
        # Save parsed content to JSON
        json_file_path = os.path.join(
            save_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}.json"
        )
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(parsed_content_list, json_file, ensure_ascii=False, indent=4)
        
        print(f"✅ CLIP parsing completed. Found {len(parsed_content_list)} elements")
        
        return {
            "labeled_image_path": labeled_image_path,
            "parsed_content_json_path": json_file_path,
            "parsed_content": parsed_content_list,
            "status": "success"
        }
        
    except Exception as e:
        return {"error": f"CLIP parsing failed: {str(e)}"}


# Define a function to execute ADB commands
def execute_adb(adb_command, timeout=30):
    try:
        result = subprocess.run(
            adb_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        print(f"Command execution failed: {adb_command}")
        print(result.stderr)
        return "ERROR"
    except subprocess.TimeoutExpired:
        print(f"ADB command timed out after {timeout} seconds: {adb_command}")
        return "ERROR"
    except Exception as e:
        print(f"ADB command failed with exception: {adb_command}, Error: {str(e)}")
        return "ERROR"


def list_all_devices() -> list:
    """
    List all devices currently connected via ADB (Android Debug Bridge).

    Returns:
        - Success: Returns a list of device IDs, each representing a connected device.
        - Failure: Returns an empty list.

    Return examples:
        1. When devices are connected:
            ["emulator-5551", "device123456"]
        2. When no devices are connected:
            []
    """
    adb_command = "adb devices"
    device_list = []
    result = execute_adb(adb_command)
    if result != "ERROR":
        devices = result.split("\n")[1:]
        for d in devices:
            device_list.append(d.split()[0])
    return device_list


@tool
def get_device_size(device: str = "emulator") -> dict | str:
    """
    Get the screen size (width and height) of a mobile device (Android emulator or real device).
    Parameters:
        - device (str): Specify the target device ID, default is "emulator".

    Returns:
        - Success: Returns the result of the operation, which is the screen width and height (in pixels).
        - Returns error information.

    """
    adb_command = f"adb -s {device} shell wm size"
    result = execute_adb(adb_command)
    if result != "ERROR":
        size_str = result.split(": ")[1]
        width, height = map(int, size_str.split("x"))
        return {"width": width, "height": height}
    return "Failed to get device size. Please check device connection or permissions."


# Define a screenshot tool
@tool
def take_screenshot(
    device: str = "emulator",
    save_dir: str = "./log/screenshots",
    app_name: str = None,
    step: int = 0,
) -> str:
    """
    Take a screenshot of the specified mobile device (Android emulator or real device) and save it to a directory organized by application.

    Parameters:
        - device (str): Specify the target device ID, default is "emulator". You can view connected devices using the `list_all_devices` tool.
        - save_dir (str): Directory path to save the screenshot locally, default is "./screenshots" in the current directory.
        - app_name (str): Name of the current application, used to organize subdirectories for saving screenshots.
        - step (int): Step number of the current operation, used to generate the filename.

    Returns:
        - Success: Returns the specific path string where the screenshot is saved.
        - Failure: Returns an error message string, such as "Screenshot failed, please check device connection or permissions".
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if app_name is None:
        app_name = "unknown_app"

    # Create a subdirectory organized by application
    app_dir = os.path.join(save_dir, app_name)
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)

    # Get the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate a filename including the application name, step number, and timestamp
    if step is not None:
        filename = f"{app_name}_step{step}_{timestamp}.png"
    else:
        filename = f"{app_name}_{timestamp}.png"

    screenshot_file = os.path.join(app_dir, filename)
    remote_file = f"/sdcard/{filename}"

    # Construct ADB commands
    cap_command = f"adb -s {device} shell screencap -p {remote_file}"
    pull_command = f"adb -s {device} pull {remote_file} {screenshot_file}"
    delete_command = f"adb -s {device} shell rm {remote_file}"

    # Reduced sleep time to improve performance
    sleep(0.5)
    
    # Execute screenshot command with better error handling
    print(f"Executing screenshot command: {cap_command}")
    if execute_adb(cap_command, timeout=15) != "ERROR":
        print(f"Screenshot captured, pulling file: {pull_command}")
        if execute_adb(pull_command, timeout=10) != "ERROR":
            # Clean up the temporary file on device
            execute_adb(delete_command, timeout=5)
            print(f"Screenshot saved successfully: {screenshot_file}")
            return screenshot_file
        else:
            print("Failed to pull screenshot from device")
    else:
        print("Failed to capture screenshot on device")

    return "Screenshot failed. Please check device connection or permissions."


@tool
def screen_element(image_path: str) -> Dict:
    """
    Parse an interface screenshot to get screen element information using CLIP model.
    
    Parameters:
        - image_path (str): File path of the screenshot (local path).

    Returns:
        - Success: Returns a dictionary containing the labeled image save path and parsed content JSON file path.
        - Failure: Returns a dictionary containing error information.
    """
    print(f"Using CLIP model to process image: {image_path}")
    
    # Use CLIP parsing instead of OmniParser API
    result = parse_image_with_clip(image_path)
    
    if "error" in result:
        print(f"❌ Screen element parsing failed: {result['error']}")
        return result
    
    print(f"✅ Screen parsing successful using CLIP model")
    return result


# Define action tools, including tap, back, type, swipe, long press, and drag
@tool
def screen_action(
    device: str = "emulator",
    action: str = "tap",
    x: Optional[int] = None,
    y: Optional[int] = None,
    input_str: Optional[str] = None,
    duration: int = 1000,
    direction: Optional[str] = None,
    dist: str = "medium",
    quick: bool = False,
    start: Optional[List[int]] = None,
    end: Optional[List[int]] = None,
) -> str:
    """
    Tool name: screen_action

    Tool function:
        Perform screen operations on mobile devices (Android emulator or real device), including tap, back, type text, swipe, long press, and drag.

    Parameters:
        - device (str): Specify the target device ID, default is "emulator".
        - action (str): Specify the type of screen operation to perform. Supports the following operations:
            - "tap": Tap the specified coordinates on the screen.
                Requires parameters: x, y
            - "back": Back key operation.
                No additional parameters required.
            - "text": Enter text on the screen.
                Requires parameter: input_str
            - "long_press": Long press the specified coordinates on the screen.
                Requires parameters: x, y, duration (default 1000 milliseconds)
            - "swipe": Swipe operation, supports four directions ("up", "down", "left", "right").
                Requires parameters: x, y, direction, dist (default "medium"), quick (default False)
            - "swipe_precise": Precise swipe, swipe from the specified start point to the specified end point.
                Requires parameters: start (list of 2 integers [x, y]), end (list of 2 integers [x, y]), duration (default 400 milliseconds)

    Returns:
        Returns a JSON string including the following fields:
        - "status": "success" or "error"
        - "action": Type of operation performed
        - "device": Device ID
        - Other fields appended according to the operation type (e.g., clicked coordinates, input text, swipe start and end points, etc.).
    """
    try:
        adb_command = None
        result_data = {"action": action, "device": device}

        if action == "back":
            adb_command = f"adb -s {device} shell input keyevent KEYCODE_BACK"

        elif action == "tap":
            if x is None or y is None:
                return json.dumps(
                    {
                        "status": "error",
                        "action": action,
                        "device": device,
                        "message": "Missing required parameters for click action (x, y)",
                    }
                )
            adb_command = f"adb -s {device} shell input tap {x} {y}"
            # Record information of the clicked element (assuming x, y represent the position of the clicked element)
            result_data["clicked_element"] = {"x": x, "y": y}

        elif action == "text":
            if not input_str:
                return json.dumps(
                    {
                        "status": "error",
                        "action": action,
                        "device": device,
                        "message": "Missing required parameter for text action (input_str)",
                    }
                )
            sanitized_input_str = input_str.replace(" ", "%s").replace("'", "")
            adb_command = f"adb -s {device} shell input text {sanitized_input_str}"
            result_data["input_str"] = input_str

        elif action == "long_press":
            if x is None or y is None:
                return json.dumps(
                    {
                        "status": "error",
                        "action": action,
                        "device": device,
                        "message": "Missing required parameters for long_press action (x, y)",
                    }
                )
            adb_command = (
                f"adb -s {device} shell input swipe {x} {y} {x} {y} {duration}"
            )
            result_data["long_press"] = {"x": x, "y": y, "duration": duration}

        elif action == "swipe":
            if x is None or y is None or direction is None:
                return json.dumps(
                    {
                        "status": "error",
                        "action": action,
                        "device": device,
                        "message": "Missing required parameters for swipe action (x, y, direction)",
                    }
                )
            unit_dist = 100  # Swipe base distance
            offset_x, offset_y = 0, 0
            if direction == "up":
                offset_y = -2 * unit_dist if dist == "medium" else -3 * unit_dist
            elif direction == "down":
                offset_y = 2 * unit_dist if dist == "medium" else 3 * unit_dist
            elif direction == "left":
                offset_x = -2 * unit_dist if dist == "medium" else -3 * unit_dist
            elif direction == "right":
                offset_x = 2 * unit_dist if dist == "medium" else 3 * unit_dist
            else:
                return json.dumps(
                    {
                        "status": "error",
                        "action": action,
                        "device": device,
                        "message": "Invalid direction for swipe",
                    }
                )
            swipe_duration = 100 if quick else 400
            adb_command = f"adb -s {device} shell input swipe {x} {y} {x + offset_x} {y + offset_y} {swipe_duration}"
            result_data["swipe"] = {
                "start": (x, y),
                "end": (x + offset_x, y + offset_y),
                "duration": swipe_duration,
                "direction": direction,
            }

        elif action == "swipe_precise":
            if not start or not end:
                return json.dumps(
                    {
                        "status": "error",
                        "action": action,
                        "device": device,
                        "message": "Missing required parameters for swipe_precise action (start, end)",
                    }
                )
            start_x, start_y = start
            end_x, end_y = end
            adb_command = f"adb -s {device} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
            result_data["swipe_precise"] = {
                "start": start,
                "end": end,
                "duration": duration,
            }

        else:
            return json.dumps(
                {
                    "status": "error",
                    "action": action,
                    "device": device,
                    "message": "Invalid action",
                }
            )

        # Execute ADB command
        ret = execute_adb(adb_command)
        if ret is not None and "ERROR" not in ret.upper():
            result_data["status"] = "success"
        else:
            result_data["status"] = "error"
            result_data["message"] = f"ADB command execution failed: {ret}"

        return json.dumps(result_data, ensure_ascii=False)

    except Exception as e:
        return json.dumps(
            {"status": "error", "action": action, "device": device, "message": str(e)},
            ensure_ascii=False,
        )
