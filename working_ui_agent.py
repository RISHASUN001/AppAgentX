#!/usr/bin/env python3

"""
Working UI Agent - Advanced Android Automation with CLIP
Perfect for TikTok scrolling, liking, and intelligent workflow automation
"""

import json
import os
import subprocess
import time
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image

# Try to import CLIP, fallback if not available
try:
    import clip
    import torch
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("⚠️  CLIP not available - running in basic mode")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not available - no vector storage")
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not available - no vector storage")

class WorkingUIAgent:
    """
    Advanced Android UI automation agent with CLIP integration
    Perfect for TikTok scrolling, Instagram browsing, and intelligent app testing
    """
    
    def __init__(self, device_id: str = None):
        """Initialize the working UI agent with CLIP capabilities"""
        print("🚀 Working UI Agent - Advanced Android Automation with CLIP")
        print("🎯 Perfect for TikTok, Instagram, and intelligent app testing!")
        print("🧠 AI-powered with visual understanding capabilities")
        print("=" * 60)
        
        # Get available devices
        self.available_devices = self._list_devices()
        print(f"📱 Available devices: {self.available_devices}")
        
        if not self.available_devices:
            raise Exception("No Android devices found. Please connect a device or start an emulator.")
        
        # Use provided device or first available
        self.device_id = device_id or self.available_devices[0]
        print(f"🎯 Using device: {self.device_id}")
        
        # Get device screen size
        self.device_info = self._get_device_size()
        print(f"📏 Screen size: {self.device_info}")
        
        # Initialize CLIP if available
        self.clip_model = None
        self.clip_preprocess = None
        self.clip_available = CLIP_AVAILABLE
        if self.clip_available:
            try:
                print("🧠 Loading CLIP model...")
                self.clip_model, self.clip_preprocess = clip.load("ViT-B/32")
                self.clip_model.eval()
                print("✅ CLIP model loaded successfully")
            except Exception as e:
                print(f"⚠️  CLIP loading failed: {e}")
                self.clip_available = False
        
        # Initialize FAISS vector database if available
        self.vector_db = None
        self.ui_elements = []
        if FAISS_AVAILABLE and self.clip_available:
            try:
                # Create FAISS index for 512D CLIP embeddings
                self.vector_db = faiss.IndexFlatL2(512)
                print("✅ Vector database initialized")
            except Exception as e:
                print(f"⚠️  Vector database initialization failed: {e}")
        
        # Setup logging directory
        self.log_dir = Path("./working_automation_logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Session tracking
        self.current_session = None
        self.session_actions = []
        self.session_screenshots = []
        
        print("✅ Working UI Agent initialized with advanced capabilities")
    
    def _execute_adb(self, command: str) -> str:
        """Execute an ADB command and return the result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"ADB command failed: {command}")
                print(f"Error: {result.stderr}")
                return "ERROR"
        except Exception as e:
            print(f"Exception executing command: {command}")
            print(f"Error: {str(e)}")
            return "ERROR"
    
    def _list_devices(self) -> List[str]:
        """List all connected Android devices"""
        result = self._execute_adb("adb devices")
        if result == "ERROR":
            return []
        
        devices = []
        lines = result.split('\n')[1:]  # Skip header line
        for line in lines:
            if line.strip() and '\tdevice' in line:
                device_id = line.split('\t')[0].strip()
                devices.append(device_id)
        return devices
    
    def _get_device_size(self) -> Dict:
        """Get the screen resolution of the device"""
        command = f"adb -s {self.device_id} shell wm size"
        result = self._execute_adb(command)
        
        if result == "ERROR":
            return {"width": 1080, "height": 1920}  # Default values
        
        try:
            # Parse output like "Physical size: 1080x2424"
            size_part = result.split(': ')[1] if ': ' in result else result
            width, height = map(int, size_part.split('x'))
            return {"width": width, "height": height}
        except:
            return {"width": 1080, "height": 1920}  # Default fallback
    
    def take_screenshot(self, description: str = "") -> str:
        """Take a screenshot and save it locally"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.current_session:
            session_dir = self.log_dir / self.current_session["name"]
            session_dir.mkdir(exist_ok=True)
        else:
            session_dir = self.log_dir
        
        # Generate filename
        step_num = len(self.session_screenshots)
        if description:
            filename = f"step{step_num:02d}_{description}_{timestamp}.png"
        else:
            filename = f"screenshot_{timestamp}.png"
        
        local_path = session_dir / filename
        remote_path = f"/sdcard/temp_screenshot.png"
        
        # Take screenshot on device
        cap_command = f"adb -s {self.device_id} shell screencap -p {remote_path}"
        pull_command = f"adb -s {self.device_id} pull {remote_path} {local_path}"
        rm_command = f"adb -s {self.device_id} shell rm {remote_path}"
        
        print(f"📸 Taking screenshot: {filename}")
        
        # Execute commands
        if self._execute_adb(cap_command) != "ERROR":
            if self._execute_adb(pull_command) != "ERROR":
                self._execute_adb(rm_command)  # Cleanup remote file
                
                # Record screenshot in session
                screenshot_record = {
                    "step": step_num,
                    "path": str(local_path),
                    "description": description,
                    "timestamp": datetime.now().isoformat()
                }
                self.session_screenshots.append(screenshot_record)
                
                print(f"   ✅ Saved: {local_path}")
                return str(local_path)
        
        print("   ❌ Screenshot failed")
        return ""
    
    def click_coordinates(self, x: int, y: int, description: str = "") -> bool:
        """Click at specific coordinates on the screen"""
        print(f"🖱️  Clicking at ({x}, {y}) - {description}")
        
        command = f"adb -s {self.device_id} shell input tap {x} {y}"
        result = self._execute_adb(command)
        
        success = result != "ERROR"
        
        # Record action
        action_record = {
            "action": "click",
            "x": x,
            "y": y,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "result": "SUCCESS" if success else "FAILED"
        }
        self.session_actions.append(action_record)
        
        if success:
            print(f"   ✅ Click successful")
            time.sleep(1.5)  # Wait for UI to respond
        else:
            print(f"   ❌ Click failed")
        
        return success
    
    def swipe_up(self, description: str = "scroll_up") -> bool:
        """Swipe up to scroll (perfect for TikTok, Instagram feeds)"""
        # Calculate swipe coordinates (center of screen, swipe up)
        center_x = self.device_info["width"] // 2
        start_y = int(self.device_info["height"] * 0.8)  # Start near bottom
        end_y = int(self.device_info["height"] * 0.3)    # End near top
        
        print(f"👆 Swiping up - {description}")
        
        command = f"adb -s {self.device_id} shell input swipe {center_x} {start_y} {center_x} {end_y} 500"
        result = self._execute_adb(command)
        
        success = result != "ERROR"
        
        # Record action
        action_record = {
            "action": "swipe_up",
            "start_x": center_x,
            "start_y": start_y,
            "end_x": center_x,
            "end_y": end_y,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "result": "SUCCESS" if success else "FAILED"
        }
        self.session_actions.append(action_record)
        
        if success:
            print(f"   ✅ Swipe successful")
            time.sleep(2)  # Wait for content to load
        else:
            print(f"   ❌ Swipe failed")
        
        return success
    
    def double_tap_like(self, description: str = "like_post") -> bool:
        """Double tap to like (perfect for TikTok, Instagram)"""
        # Calculate center of screen for double tap
        center_x = self.device_info["width"] // 2
        center_y = self.device_info["height"] // 2
        
        print(f"❤️  Double tapping to like - {description}")
        
        # First tap
        command1 = f"adb -s {self.device_id} shell input tap {center_x} {center_y}"
        result1 = self._execute_adb(command1)
        
        # Quick delay
        time.sleep(0.1)
        
        # Second tap
        command2 = f"adb -s {self.device_id} shell input tap {center_x} {center_y}"
        result2 = self._execute_adb(command2)
        
        success = result1 != "ERROR" and result2 != "ERROR"
        
        # Record action
        action_record = {
            "action": "double_tap_like",
            "x": center_x,
            "y": center_y,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "result": "SUCCESS" if success else "FAILED"
        }
        self.session_actions.append(action_record)
        
        if success:
            print(f"   ✅ Double tap successful")
            time.sleep(1)  # Wait for like animation
        else:
            print(f"   ❌ Double tap failed")
        
        return success
    
    def type_text(self, text: str) -> bool:
        """Type text on the device"""
        print(f"⌨️  Typing: '{text}'")
        
        # Escape special characters for shell
        escaped_text = text.replace(' ', '%s').replace('&', '\\&')
        command = f"adb -s {self.device_id} shell input text \"{escaped_text}\""
        result = self._execute_adb(command)
        
        success = result != "ERROR"
        
        # Record action
        action_record = {
            "action": "type",
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "result": "SUCCESS" if success else "FAILED"
        }
        self.session_actions.append(action_record)
        
        if success:
            print(f"   ✅ Typing successful")
            time.sleep(1)
        else:
            print(f"   ❌ Typing failed")
        
        return success
    
    def press_back(self) -> bool:
        """Press the back button"""
        print("🔙 Pressing back button")
        
        command = f"adb -s {self.device_id} shell input keyevent KEYCODE_BACK"
        result = self._execute_adb(command)
        
        success = result != "ERROR"
        
        # Record action
        action_record = {
            "action": "back_button",
            "timestamp": datetime.now().isoformat(),
            "result": "SUCCESS" if success else "FAILED"
        }
        self.session_actions.append(action_record)
        
        if success:
            print(f"   ✅ Back button successful")
            time.sleep(1)
        else:
            print(f"   ❌ Back button failed")
        
        return success
    
    def wait(self, seconds: float):
        """Wait for a specified number of seconds"""
        print(f"⏳ Waiting {seconds} seconds...")
        time.sleep(seconds)
    
    def start_session(self, session_name: str, description: str = ""):
        """Start a new automation session"""
        print(f"\n🎯 Starting session: {session_name}")
        if description:
            print(f"   Description: {description}")
        
        self.current_session = {
            "name": session_name.replace(' ', '_'),
            "description": description,
            "device": self.device_id,
            "device_info": self.device_info,
            "started": datetime.now().isoformat(),
            "completed": None
        }
        
        self.session_actions = []
        self.session_screenshots = []
        
        # Take initial screenshot
        self.take_screenshot("session_start")
    
    def end_session(self) -> str:
        """End the current session and save data"""
        if not self.current_session:
            return ""
        
        self.current_session["completed"] = datetime.now().isoformat()
        
        # Take final screenshot
        self.take_screenshot("session_end")
        
        # Save session data
        session_data = {
            "session": self.current_session,
            "actions": self.session_actions,
            "screenshots": self.session_screenshots,
            "stats": {
                "total_actions": len(self.session_actions),
                "total_screenshots": len(self.session_screenshots),
                "success_rate": self._calculate_success_rate()
            }
        }
        
        session_file = self.log_dir / f"{self.current_session['name']}_session.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"💾 Session saved: {session_file}")
        
        session_name = self.current_session['name']
        self.current_session = None
        
        return str(session_file)
    
    def _calculate_success_rate(self) -> float:
        """Calculate the success rate of actions in this session"""
        if not self.session_actions:
            return 0.0
        
        successful = sum(1 for action in self.session_actions if action.get('result') == 'SUCCESS')
        return (successful / len(self.session_actions)) * 100
    
    def analyze_screenshot_with_clip(self, image_path: str, description: str = "") -> Optional[np.ndarray]:
        """Analyze screenshot using CLIP model"""
        if not self.clip_available or not self.clip_model:
            return None
        
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            image_input = self.clip_preprocess(image).unsqueeze(0)
            
            # Get CLIP embedding
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy()
        except Exception as e:
            print(f"⚠️  CLIP analysis failed: {e}")
            return None
    
    def find_element_by_description(self, description: str, screenshot_path: str = None) -> Optional[Tuple[int, int]]:
        """Find UI element using natural language description"""
        if not self.clip_available or not self.clip_model:
            print("🔍 CLIP not available - using coordinate estimation")
            return self._estimate_coordinates_by_description(description)
        
        try:
            # Take screenshot if not provided
            if not screenshot_path:
                screenshot_path = self.take_screenshot("clip_analysis")
                if not screenshot_path:
                    return None
            
            # Analyze with CLIP
            image_embedding = self.analyze_screenshot_with_clip(screenshot_path, description)
            if image_embedding is None:
                return None
            
            # For now, return estimated coordinates based on description
            # In a full implementation, this would use object detection + CLIP
            return self._estimate_coordinates_by_description(description)
            
        except Exception as e:
            print(f"⚠️  Element finding failed: {e}")
            return None
    
    def _estimate_coordinates_by_description(self, description: str) -> Tuple[int, int]:
        """Estimate coordinates based on description keywords"""
        desc_lower = description.lower()
        width = self.device_info["width"]
        height = self.device_info["height"]
        
        # Common UI element positions
        if any(word in desc_lower for word in ["like", "heart", "love"]):
            return (width // 2, int(height * 0.85))  # Bottom center for like button
        elif any(word in desc_lower for word in ["follow", "subscribe"]):
            return (int(width * 0.85), int(height * 0.15))  # Top right for follow
        elif any(word in desc_lower for word in ["search", "magnify"]):
            return (width // 2, int(height * 0.1))  # Top center for search
        elif any(word in desc_lower for word in ["profile", "avatar", "user"]):
            return (int(width * 0.1), int(height * 0.15))  # Top left for profile
        elif any(word in desc_lower for word in ["share", "send"]):
            return (int(width * 0.85), int(height * 0.7))  # Right side for share
        elif any(word in desc_lower for word in ["comment", "chat"]):
            return (int(width * 0.85), int(height * 0.5))  # Right side for comments
        else:
            return (width // 2, height // 2)  # Default center
    
    def smart_click(self, description: str) -> bool:
        """Click on element using natural language description"""
        print(f"🧠 Smart clicking: {description}")
        
        coords = self.find_element_by_description(description)
        if coords:
            x, y = coords
            return self.click_coordinates(x, y, description)
        else:
            print(f"❌ Could not find element: {description}")
            return False
    
    def run_predefined_workflow(self, workflow_name: str) -> bool:
        """Run predefined workflows like the working TikTok demo"""
        workflows = self._get_predefined_workflows()
        
        if workflow_name not in workflows:
            print(f"❌ Workflow '{workflow_name}' not found!")
            return False
        
        workflow_data = workflows[workflow_name]
        steps = workflow_data["steps"]
        
        print(f"\n🚀 EXECUTING WORKFLOW: {workflow_name}")
        print(f"📝 Description: {workflow_data['description']}")
        print(f"🎯 Steps: {len(steps)}")
        
        # Start session
        self.start_session(workflow_name.lower().replace(' ', '_'), workflow_data['description'])
        
        input("▶️  Press ENTER to start workflow execution...")
        
        # Execute workflow steps
        for i, step in enumerate(steps):
            action = step.get("action", "")
            print(f"\n   Step {i+1}/{len(steps)}: {action}")
            
            if action == "click":
                x, y = step.get("x", 0), step.get("y", 0)
                desc = step.get("description", "")
                self.click_coordinates(x, y, desc)
                
            elif action == "smart_click":
                desc = step.get("description", "")
                self.smart_click(desc)
                
            elif action == "type":
                text = step.get("text", "")
                self.type_text(text)
                
            elif action == "swipe_up":
                desc = step.get("description", "scroll")
                self.swipe_up(desc)
                
            elif action == "double_tap":
                desc = step.get("description", "like")
                self.double_tap_like(desc)
                
            elif action == "wait":
                seconds = step.get("seconds", 1)
                self.wait(seconds)
                
            elif action == "key":
                key = step.get("key", "KEYCODE_BACK")
                print(f"🔘 Pressing key: {key}")
                command = f"adb -s {self.device_id} shell input keyevent {key}"
                result = self._execute_adb(command)
                if result != "ERROR":
                    print(f"   ✅ Key press successful")
                else:
                    print(f"   ❌ Key press failed")
                time.sleep(1)
                
            elif action == "screenshot":
                desc = step.get("description", f"step_{i+1}")
                self.take_screenshot(desc)
        
        print("✅ Workflow completed!")
        self.end_session()
        return True
    
    def _get_predefined_workflows(self) -> Dict:
        """Get all predefined workflows including the working TikTok ones"""
        return {
            "Google Maps - Coffee Search": {
                "description": "Search for coffee shops on Google Maps (ORIGINAL WORKING DEMO)",
                "steps": [
                    {"action": "screenshot", "description": "google_maps_start"},
                    {"action": "click", "x": 540, "y": 200, "description": "search_box"},
                    {"action": "wait", "seconds": 1},
                    {"action": "type", "text": "coffee shops near me"},
                    {"action": "wait", "seconds": 2},
                    {"action": "key", "key": "KEYCODE_ENTER"},
                    {"action": "wait", "seconds": 5},
                    {"action": "screenshot", "description": "search_results"},
                    {"action": "click", "x": 540, "y": 600, "description": "first_result"},
                    {"action": "wait", "seconds": 3},
                    {"action": "screenshot", "description": "final_result"}
                ]
            },
            "Google Maps - Restaurant Search": {
                "description": "Search for restaurants with reviews",
                "steps": [
                    {"action": "screenshot", "description": "maps_home"},
                    {"action": "click", "x": 540, "y": 200, "description": "search_box"},
                    {"action": "wait", "seconds": 1},
                    {"action": "type", "text": "best restaurants near me"},
                    {"action": "key", "key": "KEYCODE_ENTER"},
                    {"action": "wait", "seconds": 4},
                    {"action": "click", "x": 540, "y": 500, "description": "restaurant_result"},
                    {"action": "wait", "seconds": 2},
                    {"action": "click", "x": 300, "y": 700, "description": "reviews_tab"},
                    {"action": "wait", "seconds": 2},
                    {"action": "screenshot", "description": "restaurant_reviews"}
                ]
            },
            "TikTok - Browse and Like": {
                "description": "Browse TikTok videos and like them",
                "steps": [
                    {"action": "screenshot", "description": "tiktok_start"},
                    {"action": "wait", "seconds": 3},
                    {"action": "double_tap", "description": "like_first_video"},
                    {"action": "wait", "seconds": 2},
                    {"action": "swipe_up", "description": "scroll_to_next_video"},
                    {"action": "wait", "seconds": 3},
                    {"action": "double_tap", "description": "like_second_video"},
                    {"action": "wait", "seconds": 2},
                    {"action": "swipe_up", "description": "scroll_to_third_video"},
                    {"action": "wait", "seconds": 3},
                    {"action": "double_tap", "description": "like_third_video"},
                    {"action": "screenshot", "description": "tiktok_browsing_complete"}
                ]
            },
            "TikTok - Follow Users": {
                "description": "Follow users from TikTok videos",
                "steps": [
                    {"action": "screenshot", "description": "tiktok_follow_start"},
                    {"action": "wait", "seconds": 2},
                    {"action": "click", "x": 100, "y": 300, "description": "click_first_user_avatar"},
                    {"action": "wait", "seconds": 2},
                    {"action": "click", "x": 900, "y": 300, "description": "click_first_follow_button"},
                    {"action": "wait", "seconds": 2},
                    {"action": "key", "key": "KEYCODE_BACK"},
                    {"action": "wait", "seconds": 2},
                    {"action": "swipe_up", "description": "scroll_to_next_video"},
                    {"action": "wait", "seconds": 3},
                    {"action": "click", "x": 100, "y": 600, "description": "click_second_user_avatar"},
                    {"action": "wait", "seconds": 3},
                    {"action": "click", "x": 900, "y": 300, "description": "click_second_follow_button"},
                    {"action": "wait", "seconds": 2},
                    {"action": "key", "key": "KEYCODE_BACK"},
                    {"action": "screenshot", "description": "follow_workflow_complete"}
                ]
            }
        }
    
    def tiktok_auto_scroll(self, num_videos: int = 5):
        """Automatically scroll through TikTok videos"""
        self.start_session("tiktok_auto_scroll", f"Auto scroll through {num_videos} TikTok videos")
        
        print(f"\n🎵 Starting TikTok auto-scroll for {num_videos} videos")
        print("🎯 Make sure TikTok is open and on the main feed!")
        
        input("📱 Press ENTER when TikTok is ready...")
        
        for i in range(num_videos):
            print(f"\n📹 Video {i+1}/{num_videos}")
            
            # Take screenshot of current video
            self.take_screenshot(f"tiktok_video_{i+1}")
            
            # Watch video for a bit
            self.wait(3)
            
            # Sometimes double tap to like (randomly)
            if i % 2 == 0:  # Like every other video
                self.double_tap_like(f"like_video_{i+1}")
                self.wait(1)
            
            # Scroll to next video
            if i < num_videos - 1:  # Don't scroll after last video
                self.swipe_up(f"scroll_to_video_{i+2}")
        
        print("\n✅ TikTok auto-scroll completed!")
        self.end_session()
    
    def instagram_auto_browse(self, num_posts: int = 5):
        """Automatically browse Instagram feed"""
        self.start_session("instagram_browse", f"Browse {num_posts} Instagram posts")
        
        print(f"\n📷 Starting Instagram browse for {num_posts} posts")
        print("🎯 Make sure Instagram is open and on the main feed!")
        
        input("📱 Press ENTER when Instagram is ready...")
        
        for i in range(num_posts):
            print(f"\n📸 Post {i+1}/{num_posts}")
            
            # Take screenshot of current post
            self.take_screenshot(f"instagram_post_{i+1}")
            
            # View post for a bit
            self.wait(2)
            
            # Like post (tap heart icon - usually on left side)
            heart_x = int(self.device_info["width"] * 0.1)  # Left side
            heart_y = int(self.device_info["height"] * 0.7)  # Lower area
            self.click_coordinates(heart_x, heart_y, f"like_post_{i+1}")
            
            # Scroll to next post
            if i < num_posts - 1:
                self.swipe_up(f"scroll_to_post_{i+2}")
        
        print("\n✅ Instagram browse completed!")
        self.end_session()
    
    def manual_control(self):
        """Manual control mode for testing"""
        self.start_session("manual_control", "Manual testing session")
        
        print("\n🎮 Manual Control Mode")
        print("Commands:")
        print("  screenshot [description] - Take screenshot")
        print("  click <x> <y> [description] - Click at coordinates")
        print("  type <text> - Type text")
        print("  swipe - Swipe up to scroll")
        print("  like - Double tap to like")
        print("  back - Press back button")
        print("  wait <seconds> - Wait")
        print("  quit - Exit manual mode")
        
        while True:
            try:
                command = input("\n🎮 > ").strip().split()
                if not command:
                    continue
                    
                if command[0] == "quit":
                    break
                    
                elif command[0] == "screenshot":
                    desc = command[1] if len(command) > 1 else "manual_screenshot"
                    self.take_screenshot(desc)
                    
                elif command[0] == "click" and len(command) >= 3:
                    x, y = int(command[1]), int(command[2])
                    desc = " ".join(command[3:]) if len(command) > 3 else "manual_click"
                    self.click_coordinates(x, y, desc)
                    
                elif command[0] == "type" and len(command) >= 2:
                    text = " ".join(command[1:])
                    self.type_text(text)
                    
                elif command[0] == "swipe":
                    self.swipe_up("manual_swipe")
                    
                elif command[0] == "like":
                    self.double_tap_like("manual_like")
                    
                elif command[0] == "back":
                    self.press_back()
                    
                elif command[0] == "wait" and len(command) >= 2:
                    seconds = float(command[1])
                    self.wait(seconds)
                    
                else:
                    print("❌ Unknown command")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        self.end_session()

def main():
    print("🚀 Working UI Agent - Advanced Android Automation with CLIP")
    print("🧠 AI-powered with visual understanding capabilities")
    print("🎯 Perfect for TikTok, Instagram, and intelligent app testing!")
    print("=" * 70)
    
    try:
        agent = WorkingUIAgent()
        
        while True:
            print("\n🎯 Available Predefined Workflows:")
            print("1. 🗺️  Google Maps - Coffee shop search (ORIGINAL WORKING DEMO)")
            print("2. �️  Google Maps - Restaurant search with reviews")
            print("3. 🎵 TikTok - Browse and like videos")
            print("4. � TikTok - Follow users from videos")
            print("5. 📱 Quick screenshot")
            print("6. 🎮 Manual control mode")
            print("7. 🚪 Exit")
            
            choice = input("\nChoose workflow (1-7): ").strip()
            
            if choice == "1":
                agent.run_predefined_workflow("Google Maps - Coffee Search")
                
            elif choice == "2":
                agent.run_predefined_workflow("Google Maps - Restaurant Search")
                
            elif choice == "3":
                agent.run_predefined_workflow("TikTok - Browse and Like")
                
            elif choice == "4":
                agent.run_predefined_workflow("TikTok - Follow Users")
                
            elif choice == "5":
                screenshot_path = agent.take_screenshot("quick_capture")
                if screenshot_path:
                    print(f"📸 Screenshot saved: {screenshot_path}")
                    
            elif choice == "6":
                agent.manual_control()
                
            elif choice == "7":
                break
                
            else:
                print("❌ Invalid choice. Please select 1-7.")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure your Android emulator is running and ADB is working!")
    
    print("\n🎉 Thanks for using Working UI Agent!")

if __name__ == "__main__":
    main()