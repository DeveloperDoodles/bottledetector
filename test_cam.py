import cv2
import time

print("Testing camera access...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ ERROR: Could not open camera (index 0). This is usually a macOS permissions issue.")
    print("Please go to System Settings -> Privacy & Security -> Camera and enable it for your terminal/editor.")
else:
    print("✅ Camera opened successfully!")
    ret, frame = cap.read()
    if ret:
        print(f"✅ Successfully read a frame of size: {frame.shape}")
        cv2.imshow("Camera Test", frame)
        print("Waiting 3 seconds... look for the window!")
        cv2.waitKey(3000)
    else:
        print("❌ ERROR: Opened camera but could not read any frames.")
    
    cap.release()
    cv2.destroyAllWindows()
