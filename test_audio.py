import subprocess
import os
import time

print("Testing afplay alarm sound...")
alarm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarm.wav")

if not os.path.exists(alarm_path):
    print(f"❌ ERROR: alarm.wav not found at {alarm_path}")
else:
    print(f"✅ alarm.wav found. Playing for 3 seconds...")
    try:
        proc = subprocess.Popen(["afplay", alarm_path])
        time.sleep(3)
        proc.terminate()
        print("✅ Sound test completed.")
    except Exception as e:
        print(f"❌ ERROR playing sound: {e}")
