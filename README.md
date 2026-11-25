<div align="center">

# 💧 Water Bottle Detector

**A hydration reminder that makes you prove it.**

An alarm rings on a timer and *won't stop* until your webcam sees you holding a water bottle.

![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)
![YOLOv8](https://img.shields.io/badge/detector-YOLOv8n-00B4D8)
![OpenCV](https://img.shields.io/badge/camera-OpenCV-5C3EE8?logo=opencv&logoColor=white)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey?logo=apple)

[Quick start](#-quick-start) · [How it works](#-how-it-works) · [Usage](#-usage) · [Configuration](#-configuration) · [Run at login](#-run-it-automatically-at-login) · [Under the hood](#-under-the-hood) · [Troubleshooting](#-troubleshooting)

</div>

---

## ✨ Features

- ⏰ **Recurring reminders** — every 30 minutes by default, fully adjustable
- 🔔 **A real alarm** — a looping two-tone sound that keeps going until you comply
- 📷 **Camera verification** — YOLOv8 detects a bottle, and you hold it steady to stop the alarm
- 🎯 **Forgiving timer** — brief detection flickers (under 0.5 s) don't reset your progress
- 📊 **Live overlay** — bounding boxes, status banner and a progress bar while you hold
- 🧪 **Test mode** — trigger an alarm in about 10 seconds to try it out
- 🔇 **Headless mode** — run without the preview window
- 🚫 **No training required** — uses the pretrained COCO `bottle` class

---

## 🚀 Quick start

```bash
# 1. Get the code
git clone https://github.com/DeveloperDoodles/bottledetector.git
cd bottledetector

# 2. Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. (Optional) Generate the alarm sound — main.py does this automatically if it's missing
python generate_alarm.py

# 4. Try it: the alarm fires after about 10 seconds
python main.py --test
```

When the alarm starts, hold a bottle in front of the camera for 3 seconds. The alarm stops and the timer starts counting again.

> **First run:** macOS will ask for camera access. Allow it for your terminal app (Terminal, iTerm, VS Code, …). The very first launch may also take a moment while dependencies load.

---

## 🔄 How it works

```mermaid
flowchart TD
    A([Start]) --> B[Wait for the interval<br/>countdown window shown]
    B -->|time is up| C[Start looping alarm 🔔]
    C --> D[Open webcam]
    D --> E{YOLOv8 sees a bottle<br/>above the confidence threshold?}
    E -->|yes| F[Hold timer runs]
    E -->|no, longer than 0.5s| G[Timer resets]
    E -->|no, under 0.5s| F
    F -->|held for the full duration| H[Alarm stops ✅<br/>"HYDRATED!" screen]
    G --> E
    H --> B
    B -. press Q or ESC .-> Z([Quit])
    E -. press Q or ESC .-> Z
```

1. The program sits in the background showing a small countdown window.
2. When the interval ends, the alarm starts looping (`afplay` plays `alarm.wav`).
3. The webcam opens and every frame goes through YOLOv8-nano.
4. A detection only counts if it is the COCO class **bottle** (id `39`) and its confidence meets your threshold.
5. Keep the bottle in view for the whole **hold duration**. A dropout longer than the grace period resets the timer.
6. The alarm stops, a green "HYDRATED!" frame appears briefly, and the next countdown begins.

---

## 🧰 Requirements

| Requirement | Notes |
|---|---|
| **macOS** | The alarm is played with the built-in `afplay`. On other systems the program still runs, but the alarm falls back to a terminal bell. |
| **Python 3.8+** | Tested here with Python 3.14. |
| **Webcam** | Camera access must be granted to the app you launch Python from. |
| **Speakers** | For the alarm. |
| **Internet (first run only)** | Only if `yolov8n.pt` is missing; it is also included in this repo (about 6 MB). |

Python packages (see [`requirements.txt`](requirements.txt)): `ultralytics`, `opencv-python`, `numpy`.

---

## 🕹 Usage

```bash
python main.py [options]
```

| Option | Default | What it does |
|---|---|---|
| `--test` | off | Test mode: first alarm after about 10 seconds. |
| `--interval MINUTES` | `30` | Minutes between reminders. Accepts decimals, e.g. `0.5` for 30 seconds. |
| `--hold SECONDS` | `3` | How long the bottle must stay in view to silence the alarm. |
| `--confidence 0-1` | `0.45` | Minimum detection confidence. **Lower = more sensitive** (catches more bottles, but more false positives). |
| `--no-display` | off | Don't show the camera or countdown windows. The camera is still used. |
| `-h`, `--help` | | Show help. |

### Examples

```bash
python main.py                           # every 30 minutes, 3-second hold
python main.py --interval 45             # every 45 minutes
python main.py --interval 20 --hold 10   # every 20 minutes, hold for 10 seconds
python main.py --confidence 0.3          # be more lenient with hard-to-detect bottles
python main.py --test --hold 5           # quick trial with a 5-second hold
python main.py --no-display              # no windows, just the alarm and the camera check
```

### Controls

| Key | Action |
|---|---|
| `Q` or `ESC` | Quit (works while a window is focused) |
| `Ctrl+C` | Quit from the terminal (the only way in `--no-display` mode) |

### What you'll see

- **Waiting window** — "Next alarm in MM:SS" and the time of the next reminder.
- **Alarm window** — a red banner while no bottle is detected, a green banner and bounding box when one is, and a progress bar showing how much longer to hold.
- **Success screen** — a green "HYDRATED!" overlay for a couple of seconds.

---

## ⚙️ Configuration

Day-to-day settings are command-line flags. Deeper defaults live as constants at the top of [`main.py`](main.py):

| Constant | Default | Meaning |
|---|---|---|
| `BOTTLE_CLASS_ID` | `39` | COCO class to look for. |
| `CONFIDENCE_THRESHOLD` | `0.45` | Default for `--confidence`. |
| `HOLD_DURATION` | `3` | Default for `--hold`, in seconds. |
| `GRACE_PERIOD` | `0.5` | Seconds a bottle may disappear before the timer resets. |
| `DEFAULT_INTERVAL` | `30` | Default for `--interval`, in minutes. |
| `TEST_INTERVAL` | `0.167` | Interval used by `--test` (about 10 seconds). |
| `CAMERA_RETRY_SECONDS` | `2` | Delay between attempts to reopen a missing camera. |
| `YOLO_MODEL` | `"yolov8n.pt"` | Model weights file. |

### Common tweaks

<details>
<summary><b>Make it harder to cheat (longer hold)</b></summary>

```bash
python main.py --hold 15
```
</details>

<details>
<summary><b>Detect something else (a cup, for example)</b></summary>

Change `BOTTLE_CLASS_ID` in `main.py` to another [COCO class id](https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/coco.yaml). `39` is `bottle`, `41` is `cup`. The on-screen labels still say "Bottle", so update the strings in `draw_detection_overlay` if you want them to match.
</details>

<details>
<summary><b>Use a more accurate model</b></summary>

Set `YOLO_MODEL = "yolov8s.pt"` (or `yolov8m.pt`). Ultralytics downloads it on first run. Larger models are more accurate but slower, which matters on older laptops.
</details>

<details>
<summary><b>Use your own alarm sound</b></summary>

Replace `alarm.wav` with any WAV file (short clips that loop well work best). Or tweak the tones in `generate_alarm.py` (`FREQ_HIGH`, `FREQ_LOW`, `PULSE_RATE`) and run `python generate_alarm.py`.
</details>

<details>
<summary><b>Use a different camera</b></summary>

The code opens camera index `0` (`cv2.VideoCapture(0)` in `run_alarm_session`). Change it to `1`, `2`, … to pick an external webcam.
</details>

---

## 🔁 Run it automatically at login

The detector only helps if it's running, so you can have macOS start it for you with a Launch Agent. This is an optional setup, and I haven't tested it against every macOS version, so treat it as a starting point.

1. **Find your paths** (run these inside the project folder):

   ```bash
   pwd                          # project folder
   echo "$(pwd)/venv/bin/python" # the Python inside your venv
   ```

2. **Create** `~/Library/LaunchAgents/com.waterbottledetector.plist`, replacing the two paths with yours:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.waterbottledetector</string>
       <key>ProgramArguments</key>
       <array>
           <string>/ABSOLUTE/PATH/TO/bottledetector/venv/bin/python</string>
           <string>/ABSOLUTE/PATH/TO/bottledetector/main.py</string>
       </array>
       <key>WorkingDirectory</key>
       <string>/ABSOLUTE/PATH/TO/bottledetector</string>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
       <key>StandardOutPath</key>
       <string>/tmp/waterbottledetector.log</string>
       <key>StandardErrorPath</key>
       <string>/tmp/waterbottledetector.log</string>
   </dict>
   </plist>
   ```

3. **Load it:**

   ```bash
   launchctl load ~/Library/LaunchAgents/com.waterbottledetector.plist
   ```

4. **Stop it:**

   ```bash
   launchctl unload ~/Library/LaunchAgents/com.waterbottledetector.plist
   ```

> ⚠️ **Camera permission:** a background process may not get a camera prompt, so run `python main.py --test` from your terminal once and allow access first. If the alarm rings but the camera can't open, check `/tmp/waterbottledetector.log`. The alarm keeps ringing until the camera works, so test this before relying on it.
>
> ⚠️ With `KeepAlive` on, quitting with `Q` makes macOS restart the program. Use the `unload` command above to stop it for real.

---

## 🧱 Under the hood

### Project layout

```
bottledetector/
├── main.py            # the app: timer loop, alarm, camera, detection, UI
├── generate_alarm.py  # writes alarm.wav (two-tone, 1 s, loops seamlessly)
├── alarm.wav          # the alarm sound
├── yolov8n.pt         # YOLOv8-nano weights (pretrained on COCO)
├── test_cam.py        # checks that the camera opens and returns frames
├── test_audio.py      # checks that afplay can play alarm.wav
├── requirements.txt
└── README.md
```

### Key pieces of `main.py`

| Piece | Role |
|---|---|
| `parse_args()` | Defines the command-line options. |
| `AlarmManager` | Locates or generates `alarm.wav`, loops it with `afplay` in a background thread, and stops it on request. |
| `detect_bottles(results, conf)` | Filters YOLO output to the bottle class above the confidence threshold and returns boxes. |
| `run_alarm_session(model, alarm, args)` | One full alarm: start the sound, open the camera, run detection per frame, track the hold timer and grace period, then stop. Returns `False` if you quit. |
| `draw_detection_overlay(...)` | Draws boxes, the status banner, the progress bar and the timer text. |
| `main()` | Loads the model, then loops forever: wait for the interval, run an alarm session. |

### Design decisions

- **The alarm only stops on success or quit.** If the camera can't be opened, the alarm keeps ringing and the program retries, so a blocked camera can't be used to skip the check.
- **Grace period.** Object detectors flicker between frames. A 0.5 s tolerance stops a single missed frame from sending you back to zero.
- **Zero-training detector.** The pretrained COCO model already knows what a bottle is, which keeps setup to a single `pip install`.
- **Native audio.** Using `afplay` avoids an audio library dependency, which is why the alarm is macOS-only.

### Testing the pieces

```bash
python test_cam.py     # opens the camera for 3 seconds and shows a frame
python test_audio.py   # plays the alarm for 3 seconds
python main.py --test  # full end-to-end run
```

---

## 🛠 Troubleshooting

<details>
<summary><b>"Could not open camera"</b></summary>

Go to **System Settings → Privacy & Security → Camera** and enable it for your terminal or editor, then restart that app. Run `python test_cam.py` to confirm. Also check that no other app (Zoom, FaceTime, …) is using the camera, or try another index as described in [Common tweaks](#common-tweaks).
</details>

<details>
<summary><b>My bottle isn't being detected</b></summary>

- Lower the threshold: `--confidence 0.3`.
- Improve the lighting and hold the bottle upright and clearly in frame, not hidden behind your hand.
- Try a larger model (`yolov8s.pt`).
- Remember that the detector looks for the generic COCO "bottle" shape. Unusual flasks or fully opaque tumblers may score lower.
</details>

<details>
<summary><b>Other objects keep counting as a bottle</b></summary>

Raise the threshold: `--confidence 0.6`.
</details>

<details>
<summary><b>No sound</b></summary>

Check your volume and output device, then run `python test_audio.py`. If `afplay` isn't available (non-macOS), the program prints a terminal bell instead of looping a sound.
</details>

<details>
<summary><b><code>alarm.wav not found</code></b></summary>

`main.py` generates it automatically. You can also run `python generate_alarm.py` yourself.
</details>

<details>
<summary><b>Slow or laggy video</b></summary>

Detection runs on every frame on your CPU. Close heavy apps, keep the default nano model, or lower the resolution in `run_alarm_session` (`CAP_PROP_FRAME_WIDTH` / `CAP_PROP_FRAME_HEIGHT`).
</details>

<details>
<summary><b>The program won't quit in <code>--no-display</code> mode</b></summary>

There is no window to receive `Q`, so use `Ctrl+C` in the terminal.
</details>

---

## ⚠️ Known limitations

- **It can be fooled.** Any bottle-shaped object counts, including a photo of a bottle or one sitting on your desk. It checks that a bottle is visible, not that you are drinking.
- **macOS only for sound.** Other platforms get a terminal bell instead of a looping alarm.
- **One camera, one person.** There is no face or person check.

Ideas for stricter checks: require a person in frame as well (COCO class `0`), or require motion of the bottle between frames.

---

## 🤝 Contributing

Issues and pull requests are welcome. If you change behaviour, run `python main.py --test` end to end with a real camera before opening a PR.

---

<div align="center">

Built with [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) and [OpenCV](https://opencv.org/). Stay hydrated. 💧

</div>
