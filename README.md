# Water Bottle Detector 💧

A hydration reminder that **actually makes you prove you're drinking water**. Every 30 minutes, an alarm sounds and won't stop until you hold a water bottle in front of your camera for 3 continuous seconds (configurable with `--hold`).

## How It Works

1. App runs quietly in the background
2. Every **30 minutes**, an alarm goes off 🔔
3. Your webcam opens — show your water bottle to the camera
4. Hold it steady for **3 seconds** (default) — a progress bar tracks your hold; brief detection flickers (<0.5s) don't reset it
5. Alarm stops ✅ — cycle repeats

## Quick Start

```bash
# Create a virtual environment and install dependencies
python3 -m venv venv && source venv/bin/activate
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
- **Alarm**: macOS `afplay` (looped `alarm.wav`; falls back to a terminal bell elsewhere)
- **No training needed** — works out of the box

## Requirements

- Python 3.8+
- macOS (the alarm uses `afplay`)
- Webcam (grant camera access to your terminal/editor; `python test_cam.py` checks it)
- Speakers (for the alarm; `python test_audio.py` checks it)

If the camera can't be opened, the alarm keeps ringing and retries until it can — press Ctrl+C to quit. In `--no-display` mode there is no window, so Ctrl+C is the only way to quit.
