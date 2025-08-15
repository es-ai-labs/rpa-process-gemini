#!/usr/bin/env python3
"""
Test video codecs on Windows to find what works
"""

import cv2
import numpy as np

def test_video_codecs():
    """Test various video codecs on Windows"""
    print("🔍 Testing video codecs on Windows...")
    
    # Test frame
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_frame[:] = (0, 255, 0)  # Green frame
    
    codecs_to_test = [
        ('XVID', 'test_xvid.avi'),
        ('MJPG', 'test_mjpg.avi'), 
        ('mp4v', 'test_mp4v.mp4'),
        ('H264', 'test_h264.mp4'),
        ('WMV1', 'test_wmv1.wmv'),
        ('WMV2', 'test_wmv2.wmv')
    ]
    
    working_codecs = []
    
    for codec_name, filename in codecs_to_test:
        try:
            print(f"\n📹 Testing {codec_name}...")
            fourcc = cv2.VideoWriter_fourcc(*codec_name)
            writer = cv2.VideoWriter(filename, fourcc, 15, (640, 480))
            
            if writer.isOpened():
                # Try to write a few frames
                success_count = 0
                for i in range(5):
                    success = writer.write(test_frame)
                    if success:
                        success_count += 1
                
                writer.release()
                
                if success_count > 0:
                    print(f"   ✅ {codec_name} works! ({success_count}/5 frames written)")
                    working_codecs.append((codec_name, filename))
                else:
                    print(f"   ❌ {codec_name} opened but couldn't write frames")
            else:
                print(f"   ❌ {codec_name} failed to open")
                
        except Exception as e:
            print(f"   ❌ {codec_name} error: {e}")
    
    print(f"\n🎯 Working codecs: {[c[0] for c in working_codecs]}")
    return working_codecs

def test_opencv_backends():
    """Test OpenCV backends"""
    print("\n🔧 OpenCV Backend Info:")
    try:
        backends = cv2.videoio_registry.getBackends()
        for backend in backends:
            name = cv2.videoio_registry.getBackendName(backend)
            print(f"   • {name}")
    except:
        print("   Could not get backend info")
    
    print(f"\nOpenCV Version: {cv2.__version__}")

if __name__ == "__main__":
    test_opencv_backends()
    working_codecs = test_video_codecs()
    
    if working_codecs:
        print(f"\n✅ Recommended codec for Windows: {working_codecs[0][0]}")
    else:
        print("\n❌ No working codecs found - OpenCV video writing may have issues")