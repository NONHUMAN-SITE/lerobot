import cv2
import os
from datetime import datetime
from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.common.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.common.cameras.configs import ColorMode, Cv2Rotation

def test_and_save_camera_images(camera_indices, num_images=5, output_dir="captured_images"):
    """
    Test multiple cameras and save captured images
    
    Args:
        camera_indices: List of camera indices to test (e.g., [0, 2, 4])
        num_images: Number of images to capture per camera
        output_dir: Directory to save images
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    cameras = {}
    configs = {}
    
    print(f"Testing cameras: {camera_indices}")
    print(f"Will capture {num_images} images per camera")
    print(f"Saving to directory: {output_dir}")
    
    # Initialize cameras
    for cam_idx in camera_indices:
        try:
            print(f"\n=== Initializing camera {cam_idx} ===")
            
            # Create camera configuration
            config = OpenCVCameraConfig(
                index_or_path=cam_idx,
                fps=30,
                width=640,
                height=480,
                color_mode=ColorMode.RGB,
                rotation=Cv2Rotation.NO_ROTATION
            )
            
            # Instantiate and connect camera
            camera = OpenCVCamera(config)
            camera.connect()
            
            cameras[cam_idx] = camera
            configs[cam_idx] = config
            print(f"✅ Camera {cam_idx} connected successfully")
            
        except Exception as e:
            print(f"❌ Failed to connect camera {cam_idx}: {e}")
            continue
    
    if not cameras:
        print("❌ No cameras were successfully connected!")
        return
    
    # Capture and save images
    try:
        for i in range(num_images):
            print(f"\n--- Capturing image set {i+1}/{num_images} ---")
            
            for cam_idx, camera in cameras.items():
                try:
                    # Capture frame
                    frame = camera.async_read(timeout_ms=1000)
                    print(f"Camera {cam_idx}: Captured frame shape {frame.shape}")
                    
                    # Convert RGB to BGR for OpenCV saving (if needed)
                    if configs[cam_idx].color_mode == ColorMode.RGB:
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    else:
                        frame_bgr = frame
                    
                    # Create filename
                    filename = f"cam{cam_idx}_{timestamp}_img{i+1:03d}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Save image
                    success = cv2.imwrite(filepath, frame_bgr)
                    if success:
                        print(f"✅ Saved: {filepath}")
                    else:
                        print(f"❌ Failed to save: {filepath}")
                        
                except Exception as e:
                    print(f"❌ Error capturing from camera {cam_idx}: {e}")
            
            # Wait a bit between captures
            import time
            time.sleep(0.5)
    
    finally:
        # Disconnect all cameras
        print("\n=== Disconnecting cameras ===")
        for cam_idx, camera in cameras.items():
            try:
                camera.disconnect()
                print(f"✅ Camera {cam_idx} disconnected")
            except Exception as e:
                print(f"❌ Error disconnecting camera {cam_idx}: {e}")

if __name__ == "__main__":
    # Configure cameras to test here
    # Example: Test cameras 0, 2, and 6
    camera_indices_to_test = [ 2, 4, 6, 8]  # Modify this list with your camera indices
    
    # Number of images to capture per camera
    num_images = 3
    
    # Output directory for saved images
    output_directory = "captured_images"
    
    print("🎥 Camera Test and Image Capture Script")
    print("=" * 40)
    
    test_and_save_camera_images(
        camera_indices=camera_indices_to_test,
        num_images=num_images,
        output_dir=output_directory
    )
    
    print("\n✅ Camera test completed!")