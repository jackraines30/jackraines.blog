#!/usr/bin/env python3
"""
iOS Automation Template
A flexible template for automating iOS apps with screen reading capabilities
"""

import time
import random
import json
from typing import Tuple, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

# You'll need to install these:
# pip install appium-python-client opencv-python pillow pytesseract

from appium import webdriver
from appium.options.ios import XCUITestOptions
import cv2
import numpy as np
from PIL import Image
import pytesseract

@dataclass
class ScreenPoint:
    """Represents a point on the screen"""
    x: int
    y: int

@dataclass
class GameAction:
    """Represents an action to take in the game"""
    action_type: str  # 'tap', 'swipe', 'wait'
    point: Optional[ScreenPoint] = None
    end_point: Optional[ScreenPoint] = None  # For swipes
    duration: float = 0.1

class BaseGameAutomator(ABC):
    """Base class for game automation"""
    
    def __init__(self, device_udid: str = None):
        self.driver = None
        self.device_udid = device_udid
        self.screen_width = 0
        self.screen_height = 0
        
    def connect_to_device(self):
        """Connect to iOS device via Appium"""
        options = XCUITestOptions()
        options.device_name = "iPhone"  # Or your device name
        options.platform_version = "17.0"  # Your iOS version
        options.automation_name = "XCUITest"
        
        if self.device_udid:
            options.udid = self.device_udid
            
        # Connect to Appium server (need to start appium server first)
        self.driver = webdriver.Remote('http://localhost:4723', options=options)
        
        # Get screen dimensions
        size = self.driver.get_window_size()
        self.screen_width = size['width']
        self.screen_height = size['height']
        
    def capture_screen(self) -> np.ndarray:
        """Capture screenshot and return as OpenCV image"""
        screenshot = self.driver.get_screenshot_as_png()
        img = Image.open(io.BytesIO(screenshot))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    def tap(self, point: ScreenPoint, duration: float = 0.1):
        """Tap at specified coordinates with human-like variation"""
        # Add slight randomization to look more human
        x = point.x + random.randint(-2, 2)
        y = point.y + random.randint(-2, 2)
        
        self.driver.tap([(x, y)], duration * 1000)  # Appium expects milliseconds
        
        # Random delay after tap
        self.human_delay(0.1, 0.3)
    
    def swipe(self, start: ScreenPoint, end: ScreenPoint, duration: float = 0.5):
        """Swipe from start to end point"""
        self.driver.swipe(start.x, start.y, end.x, end.y, duration * 1000)
        self.human_delay(0.2, 0.5)
    
    def human_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add human-like delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def find_text_on_screen(self, screenshot: np.ndarray, text: str) -> List[ScreenPoint]:
        """Find text on screen using OCR"""
        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # Use Tesseract to get text locations
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
        
        found_points = []
        for i, detected_text in enumerate(data['text']):
            if text.lower() in detected_text.lower():
                x = data['left'][i] + data['width'][i] // 2
                y = data['top'][i] + data['height'][i] // 2
                found_points.append(ScreenPoint(x, y))
                
        return found_points
    
    def find_color_regions(self, screenshot: np.ndarray, target_color: Tuple[int, int, int], 
                          tolerance: int = 20) -> List[ScreenPoint]:
        """Find regions of a specific color"""
        # Convert BGR to HSV for better color matching
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
        target_hsv = cv2.cvtColor(np.uint8([[target_color]]), cv2.COLOR_BGR2HSV)[0][0]
        
        # Create mask for target color
        lower = np.array([target_hsv[0] - tolerance, 50, 50])
        upper = np.array([target_hsv[0] + tolerance, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        centers = []
        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centers.append(ScreenPoint(cx, cy))
                
        return centers
    
    @abstractmethod
    def analyze_game_state(self, screenshot: np.ndarray) -> dict:
        """Analyze current game state - implement in subclass"""
        pass
    
    @abstractmethod
    def decide_next_action(self, game_state: dict) -> GameAction:
        """Decide what action to take next - implement in subclass"""
        pass
    
    def run_automation_loop(self, max_iterations: int = 100):
        """Main automation loop"""
        if not self.driver:
            self.connect_to_device()
            
        for i in range(max_iterations):
            try:
                # Capture screen
                screenshot = self.capture_screen()
                
                # Analyze game state
                game_state = self.analyze_game_state(screenshot)
                print(f"Iteration {i+1}: Game state = {game_state}")
                
                # Decide next action
                action = self.decide_next_action(game_state)
                
                # Execute action
                if action.action_type == 'tap' and action.point:
                    print(f"Tapping at ({action.point.x}, {action.point.y})")
                    self.tap(action.point, action.duration)
                elif action.action_type == 'swipe' and action.point and action.end_point:
                    print(f"Swiping from ({action.point.x}, {action.point.y}) to ({action.end_point.x}, {action.end_point.y})")
                    self.swipe(action.point, action.end_point, action.duration)
                elif action.action_type == 'wait':
                    print(f"Waiting for {action.duration} seconds")
                    time.sleep(action.duration)
                
                # Random delay between iterations
                self.human_delay(1.0, 3.0)
                
            except Exception as e:
                print(f"Error in automation loop: {e}")
                self.human_delay(2.0, 5.0)
    
    def disconnect(self):
        """Clean up connection"""
        if self.driver:
            self.driver.quit()

# Example implementation for a simple game
class SudokuAutomator(BaseGameAutomator):
    """Example implementation for Sudoku automation"""
    
    def analyze_game_state(self, screenshot: np.ndarray) -> dict:
        """Analyze Sudoku grid state"""
        # This is where you'd implement Sudoku-specific logic
        # For now, just return empty state
        return {
            'grid': [],
            'empty_cells': [],
            'possible_moves': []
        }
    
    def decide_next_action(self, game_state: dict) -> GameAction:
        """Decide next Sudoku move"""
        # Simple example: just tap a random spot
        random_x = random.randint(100, self.screen_width - 100)
        random_y = random.randint(200, self.screen_height - 200)
        
        return GameAction(
            action_type='tap',
            point=ScreenPoint(random_x, random_y),
            duration=0.2
        )

class ChessAutomator(BaseGameAutomator):
    """Example implementation for Chess automation"""
    
    def analyze_game_state(self, screenshot: np.ndarray) -> dict:
        """Analyze chess board state"""
        # This is where you'd implement chess-specific logic
        return {
            'board': [],
            'my_turn': True,
            'possible_moves': []
        }
    
    def decide_next_action(self, game_state: dict) -> GameAction:
        """Decide next chess move"""
        # Example: random move
        start_x = random.randint(50, self.screen_width - 50)
        start_y = random.randint(300, 600)
        end_x = random.randint(50, self.screen_width - 50)
        end_y = random.randint(300, 600)
        
        return GameAction(
            action_type='swipe',
            point=ScreenPoint(start_x, start_y),
            end_point=ScreenPoint(end_x, end_y),
            duration=0.5
        )

if __name__ == "__main__":
    # Example usage
    print("iOS Automation Template")
    print("Make sure to:")
    print("1. Start Appium server: appium")
    print("2. Connect iOS device with developer mode enabled")
    print("3. Install required packages: pip install appium-python-client opencv-python pillow pytesseract")
    
    # Example usage:
    # automator = SudokuAutomator()
    # automator.run_automation_loop(max_iterations=10)
    # automator.disconnect()