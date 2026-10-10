"""
Water Bottle Detector 💧
========================
Reminds you to drink water every 30 minutes by sounding an alarm.
The alarm stops ONLY when you hold a water bottle in front of the camera
for 15 continuous seconds.

Usage:
    python main.py              # Normal mode (30-minute intervals)
    python main.py --test       # Test mode (10-second intervals for quick testing)
    python main.py --interval 5 # Custom interval in minutes

Controls (while camera is active):
    q   — Quit the entire program
    ESC — Quit the entire program
"""

import cv2
import time
import sys
import os
import argparse
import signal
import numpy as np

# ──────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────

BOTTLE_CLASS_ID = 39           # COCO class index for "bottle"
CONFIDENCE_THRESHOLD = 0.45    # Min confidence to count as detected
HOLD_DURATION = 3             # Seconds of continuous bottle detection needed
DEFAULT_INTERVAL = 30          # Minutes between reminders
TEST_INTERVAL = 0.167          # ~10 seconds for test mode
YOLO_MODEL = "yolov8n.pt"     # Nano model — fast, auto-downloads on first run

# UI Colors (BGR)
COLOR_BG = (30, 30, 30)
COLOR_RED = (60, 60, 235)
COLOR_GREEN = (100, 200, 80)
COLOR_YELLOW = (50, 200, 230)
COLOR_WHITE = (240, 240, 240)
COLOR_GRAY = (130, 130, 130)
COLOR_DARK = (20, 20, 20)
COLOR_ACCENT = (230, 160, 50)   # Blue accent
COLOR_BAR_BG = (50, 50, 50)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Water Bottle Detector — Drink water reminder with camera verification"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Test mode: alarm triggers after ~10 seconds instead of 30 minutes"
    )
    parser.add_argument(
        "--interval", type=float, default=None,
        help="Custom interval in minutes between reminders (default: 30)"
    )
    parser.add_argument(
        "--hold", type=float, default=HOLD_DURATION,
        help=f"Seconds to hold bottle in front of camera (default: {HOLD_DURATION})"
    )
    parser.add_argument(
        "--confidence", type=float, default=CONFIDENCE_THRESHOLD,
        help=f"Detection confidence threshold 0-1 (default: {CONFIDENCE_THRESHOLD})"
    )
    parser.add_argument(
        "--no-display", action="store_true",
        help="Run without camera preview window (headless mode)"
    )
    return parser.parse_args()


# ──────────────────────────────────────────────
#  Alarm Manager
# ──────────────────────────────────────────────

class AlarmManager:
    """Handles alarm sound playback using macOS native afplay (no extra deps)."""

    def __init__(self):
        self._playing = False
        self._process = None
        self._alarm_path = None
        self._loop_thread = None

    def init(self):
        """Locate or generate the alarm sound file."""
        import subprocess as _sp

        self._alarm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarm.wav")

        if not os.path.exists(self._alarm_path):
            print("⚠️  alarm.wav not found — generating it now...")
            from generate_alarm import generate_alarm
            generate_alarm()

        # Verify afplay exists (macOS built-in)
        try:
            _sp.run(["which", "afplay"], capture_output=True, check=True)
            print("🔊 Alarm sound loaded (using macOS afplay)")
        except _sp.CalledProcessError:
            print("⚠️  afplay not found — alarm will use terminal bell as fallback")
            self._alarm_path = None

    def _loop_alarm(self):
        """Internal: loop the alarm in a background thread."""
        import subprocess as _sp
        import threading

        while self._playing:
            try:
                self._process = _sp.Popen(
                    ["afplay", self._alarm_path],
                    stdout=_sp.DEVNULL, stderr=_sp.DEVNULL
                )
                self._process.wait()
            except Exception:
                break

    def start(self):
        """Start playing the alarm on loop."""
        import threading

        self._playing = True

        if self._alarm_path:
            self._loop_thread = threading.Thread(target=self._loop_alarm, daemon=True)
            self._loop_thread.start()
        else:
            # Fallback: terminal bell
            print("\a🔔 ALARM! Hold a water bottle in front of the camera!", flush=True)

    def stop(self):
        """Stop the alarm."""
        self._playing = False
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=1)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None

    def is_playing(self):
        return self._playing

    def cleanup(self):
        """Clean up any running processes."""
        self.stop()


# ──────────────────────────────────────────────
#  UI Overlay Drawing
# ──────────────────────────────────────────────

def draw_rounded_rect(img, pt1, pt2, color, radius=15, thickness=-1):
    """Draw a rounded rectangle on the image."""
    x1, y1 = pt1
    x2, y2 = pt2

    # Draw filled rectangle (simplified — true rounded corners need more work)
    overlay = img.copy()
    cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    cv2.circle(overlay, (x1 + radius, y1 + radius), radius, color, thickness)
    cv2.circle(overlay, (x2 - radius, y1 + radius), radius, color, thickness)
    cv2.circle(overlay, (x1 + radius, y2 - radius), radius, color, thickness)
    cv2.circle(overlay, (x2 - radius, y2 - radius), radius, color, thickness)
    cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)


def draw_progress_bar(frame, x, y, width, height, progress, color):
    """Draw a sleek progress bar."""
    # Background
    cv2.rectangle(frame, (x, y), (x + width, y + height), COLOR_BAR_BG, -1)
    cv2.rectangle(frame, (x, y), (x + width, y + height), COLOR_GRAY, 1)

    # Fill
    fill_width = int(width * min(progress, 1.0))
    if fill_width > 0:
        cv2.rectangle(frame, (x + 1, y + 1), (x + fill_width - 1, y + height - 1), color, -1)

        # Shine effect
        shine_color = tuple(min(c + 40, 255) for c in color)
        cv2.rectangle(frame, (x + 1, y + 1), (x + fill_width - 1, y + height // 3), shine_color, -1)


def draw_detection_overlay(frame, bottle_detected, hold_elapsed, hold_duration, detection_boxes):
    """Draw the full UI overlay on the camera frame."""
    h, w = frame.shape[:2]

    # ── Draw detection bounding boxes ──
    for box_data in detection_boxes:
        x1, y1, x2, y2, conf = box_data
        box_color = COLOR_GREEN if bottle_detected else COLOR_YELLOW
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

        label = f"Bottle {conf:.0%}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(frame, (x1, y1 - 25), (x1 + label_size[0] + 8, y1), box_color, -1)
        cv2.putText(frame, label, (x1 + 4, y1 - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_DARK, 2)

    # ── Top status bar ──
    draw_rounded_rect(frame, (10, 10), (w - 10, 75), COLOR_DARK, radius=10)

    if bottle_detected:
        status_text = "BOTTLE DETECTED"
        status_color = COLOR_GREEN
        icon = "+"
    else:
        status_text = "NO BOTTLE — SHOW YOUR WATER BOTTLE!"
        status_color = COLOR_RED
        icon = "!"

    # Pulsing effect for alarm state
    pulse = abs(np.sin(time.time() * 4))
    if not bottle_detected:
        border_color = tuple(int(c * (0.5 + 0.5 * pulse)) for c in COLOR_RED)
        cv2.rectangle(frame, (10, 10), (w - 10, 75), border_color, 2)

    cv2.putText(frame, f"[{icon}] {status_text}", (25, 52),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

    # ── Progress bar (bottom) ──
    bar_y = h - 80
    progress = hold_elapsed / hold_duration if hold_duration > 0 else 0

    draw_rounded_rect(frame, (10, bar_y - 10), (w - 10, h - 10), COLOR_DARK, radius=10)

    bar_color = COLOR_GREEN if progress > 0 else COLOR_GRAY
    draw_progress_bar(frame, 20, bar_y + 8, w - 40, 20, progress, bar_color)

    # Timer text
    remaining = max(0, hold_duration - hold_elapsed)
    if hold_elapsed > 0:
        timer_text = f"Hold steady: {remaining:.1f}s remaining"
        timer_color = COLOR_GREEN
    else:
        timer_text = f"Hold bottle for {hold_duration:.0f}s to silence alarm"
        timer_color = COLOR_GRAY

    cv2.putText(frame, timer_text, (20, bar_y + 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, timer_color, 1)

    # ── Controls hint ──
    cv2.putText(frame, "Press Q or ESC to quit", (w - 220, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_GRAY, 1)


def draw_waiting_screen():
    """Create a standalone waiting screen image."""
    frame = np.zeros((200, 550, 3), dtype=np.uint8)
    frame[:] = COLOR_BG

    cv2.putText(frame, "Water Bottle Detector", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_ACCENT, 2)
    cv2.putText(frame, "Waiting for next reminder...", (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_GRAY, 1)

    return frame


# ──────────────────────────────────────────────
#  Core Detection Logic
# ──────────────────────────────────────────────

def detect_bottles(results, confidence_threshold):
    """
    Extract bottle detections from YOLO results.
    Returns: (bool, list of (x1, y1, x2, y2, conf))
    """
    boxes_data = []
    found = False

    for box in results[0].boxes:
        cls_id = int(box.cls)
        conf = float(box.conf)

        if cls_id == BOTTLE_CLASS_ID and conf >= confidence_threshold:
            found = True
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            boxes_data.append((x1, y1, x2, y2, conf))

    return found, boxes_data


def run_alarm_session(model, alarm, args):
    """
    Run a single alarm session:
    1. Start alarm
    2. Open camera
    3. Detect bottle for hold_duration seconds continuously
    4. Stop alarm and return

    Returns: True if completed normally, False if user quit.
    """
    alarm.start()
    print("\n🔔 ALARM! Time to drink water!")
    print(f"   Show a water bottle to the camera for {args.hold} seconds to stop.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera! Stopping alarm after 30 seconds.")
        time.sleep(30)
        alarm.stop()
        return True

    # Try to set reasonable resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    bottle_start_time = None
    user_quit = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️  Camera frame grab failed, retrying...")
                time.sleep(0.1)
                continue

            # Run YOLO detection
            results = model(frame, verbose=False)

            bottle_detected, detection_boxes = detect_bottles(results, args.confidence)

            # Track continuous detection time
            if bottle_detected:
                if bottle_start_time is None:
                    bottle_start_time = time.time()
                    print("   🟢 Bottle detected! Keep holding...")

                hold_elapsed = time.time() - bottle_start_time

                if hold_elapsed >= args.hold:
                    alarm.stop()
                    print("   ✅ Great job! Alarm silenced. Stay hydrated! 💧")

                    # Show success frame briefly
                    if not args.no_display:
                        success_frame = frame.copy()
                        h, w = success_frame.shape[:2]
                        overlay = success_frame.copy()
                        cv2.rectangle(overlay, (0, 0), (w, h), COLOR_GREEN, -1)
                        cv2.addWeighted(overlay, 0.3, success_frame, 0.7, 0, success_frame)
                        cv2.putText(success_frame, "HYDRATED!", (w // 2 - 120, h // 2),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, COLOR_WHITE, 3)
                        cv2.putText(success_frame, "See you in 30 minutes...",
                                    (w // 2 - 150, h // 2 + 45),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_WHITE, 1)
                        cv2.imshow("Water Bottle Detector", success_frame)
                        cv2.waitKey(2500)

                    break
            else:
                if bottle_start_time is not None:
                    print("   🔴 Bottle lost! Timer reset.")
                bottle_start_time = None
                hold_elapsed = 0

            # Draw UI overlay
            if not args.no_display:
                draw_detection_overlay(
                    frame, bottle_detected,
                    hold_elapsed if bottle_detected else 0,
                    args.hold, detection_boxes
                )
                cv2.imshow("Water Bottle Detector", frame)

            # Check for quit keys
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q'), 27):  # q, Q, or ESC
                user_quit = True
                alarm.stop()
                break

    finally:
        cap.release()
        if not args.no_display:
            cv2.destroyAllWindows()

    return not user_quit


# ──────────────────────────────────────────────
#  Main Entry Point
# ──────────────────────────────────────────────

def main():
    args = parse_args()

    # Determine interval
    if args.test:
        interval_minutes = TEST_INTERVAL
        print("🧪 TEST MODE — alarm in ~10 seconds")
    elif args.interval is not None:
        interval_minutes = args.interval
    else:
        interval_minutes = DEFAULT_INTERVAL

    interval_seconds = interval_minutes * 60

    print("=" * 55)
    print("  💧 Water Bottle Detector")
    print("=" * 55)
    print(f"  Interval     : {interval_minutes} min ({interval_seconds:.0f}s)")
    print(f"  Hold duration: {args.hold}s")
    print(f"  Confidence   : {args.confidence:.0%}")
    print(f"  Display      : {'off' if args.no_display else 'on'}")
    print("=" * 55)

    # Load YOLO model
    print("\n⏳ Loading YOLO model (first run downloads ~6MB)...")
    try:
        from ultralytics import YOLO
        model = YOLO(YOLO_MODEL)
        print("✅ Model loaded successfully")
    except ImportError:
        print("❌ ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    # Initialize alarm
    alarm = AlarmManager()
    alarm.init()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\n👋 Shutting down...")
        alarm.stop()
        alarm.cleanup()
        cv2.destroyAllWindows()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # ── Main reminder loop ──
    reminder_count = 0

    try:
        while True:
            reminder_count += 1

            # Wait for the interval
            print(f"\n⏰ Reminder #{reminder_count} in {interval_minutes:.1f} min...")
            print(f"   Next alarm at: {time.strftime('%H:%M:%S', time.localtime(time.time() + interval_seconds))}")

            # Show waiting screen
            if not args.no_display:
                wait_frame = draw_waiting_screen()
                remaining = interval_seconds
                cv2.putText(wait_frame,
                            f"Next: {time.strftime('%H:%M:%S', time.localtime(time.time() + interval_seconds))}",
                            (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_WHITE, 1)
                cv2.putText(wait_frame, "Press Q to quit",
                            (30, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_GRAY, 1)
                cv2.imshow("Water Bottle Detector", wait_frame)

            # Interruptible sleep — check for quit key every second
            sleep_start = time.time()
            while time.time() - sleep_start < interval_seconds:
                if not args.no_display:
                    elapsed = time.time() - sleep_start
                    remaining = interval_seconds - elapsed
                    mins = int(remaining // 60)
                    secs = int(remaining % 60)

                    # Update countdown on waiting screen
                    wait_frame = draw_waiting_screen()
                    cv2.putText(wait_frame, f"Next alarm in: {mins:02d}:{secs:02d}",
                                (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_WHITE, 1)
                    cv2.putText(wait_frame, "Press Q to quit",
                                (30, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_GRAY, 1)
                    cv2.imshow("Water Bottle Detector", wait_frame)

                    key = cv2.waitKey(1000) & 0xFF
                    if key in (ord('q'), ord('Q'), 27):
                        print("\n👋 Quitting...")
                        alarm.cleanup()
                        cv2.destroyAllWindows()
                        return
                else:
                    time.sleep(1)

            # Time's up — run alarm session
            if not args.no_display:
                cv2.destroyAllWindows()

            should_continue = run_alarm_session(model, alarm, args)
            if not should_continue:
                print("\n👋 Quitting...")
                break

    finally:
        alarm.stop()
        alarm.cleanup()
        cv2.destroyAllWindows()
        print("💧 Stay hydrated! Goodbye.")


if __name__ == "__main__":
    main()
