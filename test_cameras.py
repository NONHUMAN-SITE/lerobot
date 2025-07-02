import cv2
import os
import glob
from pathlib import Path

def capture_from_video_device(device_path, output_path):
    """
    Attempt to capture an image from a video device.
    
    Args:
        device_path (str): Path to the video device (e.g., "/dev/video0")
        output_path (str): Path where to save the captured image
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"🔍 Probando dispositivo: {device_path}")
    
    # Try to open the device with V4L2 backend
    cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"❌ No se pudo abrir {device_path}")
        return False
    
    print(f"✅ {device_path} abierto correctamente")
    
    # Try to read a frame
    ret, frame = cap.read()
    if not ret:
        print(f"❌ No se pudo capturar frame de {device_path}")
        cap.release()
        return False
    
    print(f"✅ Frame capturado de {device_path}")
    
    # Save the image
    try:
        cv2.imwrite(output_path, frame)
        print(f"💾 Imagen guardada en: {output_path}")
        success = True
    except Exception as e:
        print(f"❌ Error al guardar imagen: {e}")
        success = False
    
    # Clean up
    cap.release()
    return success

def main():
    """Main function to iterate over all video devices and capture images."""
    
    # Create output directory
    output_dir = Path("outputs/captured_images")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio de salida creado: {output_dir}")
    
    # Find all video devices
    video_devices = glob.glob("/dev/video*")
    
    if not video_devices:
        print("❌ No se encontraron dispositivos de video en /dev/video*")
        return
    
    print(f"🔍 Encontrados {len(video_devices)} dispositivos de video:")
    for device in video_devices:
        print(f"  - {device}")
    
    print("\n" + "="*50)
    print("INICIANDO CAPTURA DE IMÁGENES")
    print("="*50)
    
    successful_captures = 0
    total_devices = len(video_devices)
    
    # Iterate over each video device
    for device_path in video_devices:
        # Extract device number from path (e.g., "/dev/video8" -> "8")
        device_number = device_path.split("video")[-1]
        output_path = output_dir / f"camera_{device_number}.jpg"
        
        print(f"\n📸 Procesando {device_path}...")
        
        if capture_from_video_device(device_path, str(output_path)):
            successful_captures += 1
        
        print("-" * 30)
    
    # Summary
    print("\n" + "="*50)
    print("RESUMEN")
    print("="*50)
    print(f"📊 Dispositivos totales: {total_devices}")
    print(f"✅ Capturas exitosas: {successful_captures}")
    print(f"❌ Capturas fallidas: {total_devices - successful_captures}")
    
    if successful_captures > 0:
        print(f"\n📁 Imágenes guardadas en: {output_dir}")
        print("📋 Archivos generados:")
        for img_file in output_dir.glob("camera_*.jpg"):
            print(f"  - {img_file.name}")
    else:
        print("\n⚠️  No se pudo capturar ninguna imagen")

if __name__ == "__main__":
    main()
