import cv2

# Test /dev/video4 specifically
cap = cv2.VideoCapture("/dev/video4", cv2.CAP_V4L2)

if not cap.isOpened():
    print("❌ No se pudo abrir /dev/video4")
else:
    print("✅ /dev/video4 abierta correctamente")
    
    # Try to reduce buffer size
    success = cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    actual_buffer = cap.get(cv2.CAP_PROP_BUFFERSIZE)
    print(f"Buffer size setting: success={success}, actual={actual_buffer}")
    
    # Try to read frame
    ret, frame = cap.read()
    if ret and frame is not None:
        print(f"✅ Frame capturado correctamente: {frame.shape}")
        
        # Try multiple reads
        for i in range(5):
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"  Read {i+1}: ✅ {frame.shape}")
            else:
                print(f"  Read {i+1}: ❌ Failed")
        
    else:
        print("❌ No se pudo capturar el frame")
    
    cap.release()

print("Test completado.") 