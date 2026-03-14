# iOS Automation Setup Guide

## Prerequisites
1. **macOS machine** (required for iOS development)
2. **Xcode** installed from App Store
3. **iPhone/iPad** with developer mode enabled
4. **Python 3.8+**

## Installation Steps

### 1. Install Appium
```bash
# Install Node.js first (if not installed)
brew install node

# Install Appium globally
npm install -g appium

# Install iOS driver
appium driver install xcuitest
```

### 2. Install Python Dependencies
```bash
pip install appium-python-client opencv-python pillow pytesseract
```

### 3. Install Tesseract (for OCR)
```bash
brew install tesseract
```

### 4. Setup iOS Device
1. Enable **Developer Mode** in Settings > Privacy & Security
2. Connect device to Mac via USB
3. Trust the computer when prompted
4. In Xcode, go to Window > Devices and Simulators
5. Make sure your device appears and is trusted

### 5. Build WebDriverAgent (First time setup)
```bash
# Clone WebDriverAgent
git clone https://github.com/appium/WebDriverAgent.git
cd WebDriverAgent

# Open in Xcode
open WebDriverAgent.xcodeproj

# In Xcode:
# 1. Select WebDriverAgentRunner target
# 2. Go to Signing & Capabilities
# 3. Add your Apple ID team
# 4. Change bundle identifier (e.g. com.yourname.WebDriverAgentRunner)
# 5. Build and run on your device
```

## Running the Automation

### 1. Start Appium Server
```bash
appium --allow-insecure chromedriver_autodownload
```

### 2. Run Your Script
```bash
python ios_automation_template.py
```

## Configuration Notes

### Device Setup
- Update `device_name` and `platform_version` in the script to match your device
- Get your device UDID: `xcrun simctl list` or in Xcode > Devices

### Common Issues
1. **"Could not find WebDriverAgent"**: Make sure WebDriverAgent is built and installed on device
2. **Permission denied**: Enable developer mode and trust computer
3. **OCR not working**: Make sure Tesseract is installed correctly

### Anti-Detection Tips
- Use random delays between actions (already built in)
- Vary tap coordinates slightly (already implemented)
- Don't run too frequently
- Take breaks between sessions

## Customizing for Different Games

### For Sudoku:
1. Implement `analyze_game_state()` to read the grid using OCR
2. Add Sudoku solving logic in `decide_next_action()`
3. Define tap coordinates for each grid cell

### For Chess:
1. Use computer vision to detect pieces
2. Implement chess engine or use existing one
3. Map board coordinates to screen coordinates

### For Other Games:
1. Study the game's UI patterns
2. Implement specific analysis logic
3. Define appropriate actions (taps, swipes, etc.)

## Example Usage

```python
# For Sudoku
sudoku_bot = SudokuAutomator(device_udid="your-device-udid")
sudoku_bot.run_automation_loop(max_iterations=20)
sudoku_bot.disconnect()

# For Chess  
chess_bot = ChessAutomator()
chess_bot.run_automation_loop(max_iterations=50)
chess_bot.disconnect()
```

## Legal/Ethical Notes
- Only use on games you own/have permission to automate
- Respect terms of service
- Don't use for cheating in competitive games
- This is for educational/personal use only