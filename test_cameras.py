import cv2

cap = cv2.VideoCapture("/dev/video8", cv2.CAP_V4L2)  # Forzamos backend V4L2

if not cap.isOpened():
    print("❌ No se pudo abrir la cámara")
else:
    print("✅ Cámara abierta correctamente")
    ret, frame = cap.read()
    if ret:
        print("✅ Frame capturado correctamente")
        cv2.imshow("Frame", frame)
        cv2.waitKey(0)
    else:
        print("❌ No se pudo capturar el frame")
    cap.release()
    cv2.destroyAllWindows()
