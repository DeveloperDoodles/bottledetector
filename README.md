# Water Bottle Detector 💧

A hydration reminder that **actually makes you prove you're drinking water**. Every 30 minutes, an alarm sounds and won't stop until you hold a water bottle in front of your camera for 15 continuous seconds.

## How It Works

1. App runs quietly in the background
2. Every **30 minutes**, an alarm goes off 🔔
3. Your webcam opens — show your water bottle to the camera
4. Hold it steady for **15 seconds** — a progress bar tracks your hold
5. Alarm stops ✅ — cycle repeats

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate the alarm sound
python generate_alarm.py

# Run it!
python main.py
```

## Usage

```bash
# Normal mode — 30-minute intervals
python main.py

# Test mode — alarm in ~10 seconds (for quick testing)
python main.py --test

# Custom interval (e.g., every 15 minutes)
python main.py --interval 15

# Adjust hold duration (e.g., 10 seconds)
python main.py --hold 10

# Adjust detection sensitivity (0-1, lower = more sensitive)
python main.py --confidence 0.3

# Headless mode (no camera window, just alarm)
python main.py --no-display
```

## Controls

| Key | Action |
|-----|--------|
| `Q` | Quit the program |
| `ESC` | Quit the program |

## Tech Stack

- **Detection**: YOLOv8 (nano) — uses COCO's built-in "bottle" class (index 39)
- **Camera**: OpenCV
- **Alarm**: pygame.mixer
- **No training needed** — works out of the box

## Requirements

- Python 3.8+
- Webcam
- Speakers (for the alarm)
