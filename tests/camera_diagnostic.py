#!/usr/bin/env python3

import cv2
import os
import subprocess
import sys

def check_camera_permissions():
    """Check if user has permissions to access video devices"""
    print("🔒 Checking camera permissions...")
    try:
        # Check if user is in video group (Linux)
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip()
        if 'video' in groups:
            print("✅ User is in 'video' group")
        else:
            print("⚠️  User is NOT in 'video' group")
            print("   Try: sudo usermod -a -G video $USER")
            print("   Then logout and login again")
    except:
        print("ℹ️  Could not check groups (might not be Linux)")

def list_video_devices():
    """List all video devices in /dev/"""
    print("\n📹 Video devices found in /dev/:")
    video_devices = []
    try:
        dev_files = os.listdir('/dev')
        for device in sorted(dev_files):
            if device.startswith('video'):
                device_path = f'/dev/{device}'
                video_devices.append(device_path)
                print(f"   {device_path}")
        
        if not video_devices:
            print("   ❌ No video devices found!")
        return video_devices
    except:
        print("   ❌ Could not access /dev/ directory")
        return []

def check_processes_using_cameras():
    """Check what processes might be using cameras"""
    print("\n🔍 Checking processes that might be using cameras...")
    try:
        # Check for common camera-using processes
        processes_to_check = ['cheese', 'firefox', 'chrome', 'obs', 'zoom', 'skype', 'teams', 'guvcview']
        
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        running_processes = result.stdout.lower()
        
        found_processes = []
        for process in processes_to_check:
            if process in running_processes:
                found_processes.append(process)
        
        if found_processes:
            print(f"   ⚠️  Found processes that might be using cameras: {', '.join(found_processes)}")
            print("   Try closing these applications and test again")
        else:
            print("   ✅ No obvious camera-using processes found")
            
    except:
        print("   ❌ Could not check running processes")

def test_camera_indices(max_index=10):
    """Test camera indices systematically"""
    print(f"\n📸 Testing camera indices 0-{max_index}...")
    available_cameras = []
    
    for i in range(max_index + 1):
        print(f"   Testing camera {i}...", end=" ")
        
        cap = None
        try:
            # Try to open camera
            cap = cv2.VideoCapture(i)
            
            if not cap.isOpened():
                print("❌ Failed to open")
                continue
            
            # Try to read a frame
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ Working ({width}x{height})")
                available_cameras.append(i)
            else:
                print("❌ Cannot read frames")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if cap is not None:
                cap.release()
    
    return available_cameras

def test_v4l2_info():
    """Try to get detailed camera info using v4l2-ctl (Linux)"""
    print("\n🛠️  Trying v4l2-ctl for detailed camera info...")
    try:
        # Check if v4l2-ctl is available
        result = subprocess.run(['which', 'v4l2-ctl'], capture_output=True)
        if result.returncode != 0:
            print("   ⚠️  v4l2-ctl not found. Install with: sudo apt install v4l-utils")
            return
        
        # List all video devices
        result = subprocess.run(['v4l2-ctl', '--list-devices'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   📋 Available video devices:")
            print(result.stdout)
        else:
            print("   ❌ Could not list devices with v4l2-ctl")
            
    except Exception as e:
        print(f"   ❌ Error running v4l2-ctl: {e}")

def suggest_solutions(available_cameras, requested_cameras):
    """Suggest solutions based on findings"""
    print("\n💡 RECOMMENDATIONS:")
    print("=" * 50)
    
    if not available_cameras:
        print("❌ NO CAMERAS DETECTED!")
        print("   1. Check if cameras are physically connected")
        print("   2. Check USB connections")
        print("   3. Try: lsusb | grep -i camera")
        print("   4. Check dmesg for USB errors: dmesg | grep -i usb")
        print("   5. Restart computer if cameras were recently connected")
    else:
        print(f"✅ Available cameras: {available_cameras}")
        
        missing_cameras = [cam for cam in requested_cameras if cam not in available_cameras]
        if missing_cameras:
            print(f"❌ Requested but unavailable cameras: {missing_cameras}")
            print(f"   -> Change your camera_indices_to_test to: {available_cameras}")
        else:
            print("✅ All requested cameras are available!")

def main():
    print("🎥 CAMERA DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # Cameras the user is trying to use
    requested_cameras = [2, 4, 6, 8]
    print(f"🎯 You're trying to use cameras: {requested_cameras}")
    
    # Run diagnostics
    check_camera_permissions()
    list_video_devices()
    check_processes_using_cameras()
    available_cameras = test_camera_indices(10)
    test_v4l2_info()
    
    # Provide recommendations
    suggest_solutions(available_cameras, requested_cameras)
    
    print("\n" + "=" * 50)
    print("🔧 QUICK FIXES TO TRY:")
    print("1. Close any apps using cameras (browser, video calls, etc.)")
    print("2. Unplug and reconnect USB cameras")  
    print("3. Try different USB ports")
    print("4. Check camera permissions: ls -la /dev/video*")
    print("5. Add user to video group: sudo usermod -a -G video $USER")

if __name__ == "__main__":
    main() 