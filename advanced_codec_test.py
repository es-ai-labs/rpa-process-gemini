#!/usr/bin/env python3
"""
Advanced codec test to find working video codecs on Windows
"""

import cv2
import numpy as np
import os

def test_advanced_codecs():
    """Test codecs with different approaches"""
    print("🔍 Advanced codec testing on Windows...")
    
    # Create a more realistic test frame
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # More codec combinations to test
    codec_combinations = [
        # (fourcc_code, extension, description)
        ('MJPG', '.avi', 'Motion JPEG'),
        ('XVID', '.avi', 'XVID MPEG-4'),
        ('X264', '.mp4', 'H.264'),
        ('mp4v', '.mp4', 'MPEG-4'),
        ('DIVX', '.avi', 'DivX'),
        ('FMP4', '.mp4', 'FFMPEG MPEG-4'),
        ('H264', '.mp4', 'H.264 Direct'),
        ('avc1', '.mp4', 'H.264 AVC1'),
        ('WMV1', '.wmv', 'Windows Media Video 7'),
        ('WMV2', '.wmv', 'Windows Media Video 8'),
        ('MPG1', '.mpg', 'MPEG-1'),
        ('MPG2', '.mpg', 'MPEG-2'),
        ('THEO', '.ogv', 'Theora'),
        ('FLV1', '.flv', 'Flash Video'),
        # Raw/uncompressed
        ('IYUV', '.avi', 'YUV 4:2:0'),
        ('YUY2', '.avi', 'YUV 4:2:2'),
        ('UYVY', '.avi', 'YUV 4:2:2 UYVY'),
        # Try numeric codes
        (0x47504A4D, '.avi', 'MJPG numeric'),  # MJPG
        (0x44495658, '.avi', 'XVID numeric'),  # XVID
    ]
    
    working_codecs = []
    
    for codec_code, extension, description in codec_combinations:
        filename = f'test_{codec_code}{extension}'
        
        try:
            print(f"\n📹 Testing {description} ({codec_code})...")
            
            # Create fourcc
            if isinstance(codec_code, str):
                if len(codec_code) == 4:
                    fourcc = cv2.VideoWriter_fourcc(*codec_code)
                else:
                    continue
            else:
                fourcc = codec_code
            
            # Try creating video writer
            writer = cv2.VideoWriter(filename, fourcc, 15, (640, 480))
            
            if writer.isOpened():
                print(f"   ✅ Writer opened for {description}")
                
                # Try writing multiple frames
                frames_written = 0
                for i in range(10):
                    # Create slightly different frame each time
                    frame = test_frame.copy()
                    frame[i*10:(i+1)*10, :] = [255, 0, 0]  # Add red stripe
                    
                    success = writer.write(frame)
                    if success:
                        frames_written += 1
                    else:
                        print(f"   ❌ Frame {i} write failed")
                        break
                
                writer.release()
                
                # Check if file was actually created and has content
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    if file_size > 1000 and frames_written > 0:  # At least 1KB and some frames
                        print(f"   ✅ SUCCESS: {description} - {frames_written} frames, {file_size} bytes")
                        working_codecs.append((codec_code, extension, description, frames_written, file_size))
                    else:
                        print(f"   ⚠️ File too small: {file_size} bytes, {frames_written} frames")
                        if os.path.exists(filename):
                            os.remove(filename)
                else:
                    print(f"   ❌ No output file created")
            else:
                print(f"   ❌ Writer failed to open for {description}")
                
        except Exception as e:
            print(f"   ❌ Exception with {description}: {e}")
        finally:
            # Clean up test files
            try:
                if os.path.exists(filename):
                    # Keep working codec files for verification
                    if not any(codec_code == wc[0] for wc in working_codecs):
                        os.remove(filename)
            except:
                pass
    
    print(f"\n🎯 Working codecs found: {len(working_codecs)}")
    for codec_code, extension, description, frames, size in working_codecs:
        print(f"   ✅ {description}: {frames} frames, {size} bytes")
    
    return working_codecs

def test_backend_specific():
    """Test with specific backends"""
    print("\n🔧 Testing with specific backends...")
    
    # Test with different backends
    backends_to_test = [
        (cv2.CAP_FFMPEG, "FFMPEG"),
        (cv2.CAP_MSMF, "Microsoft Media Foundation"),
        (cv2.CAP_DSHOW, "DirectShow"),
    ]
    
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_frame[:] = [0, 255, 0]  # Green
    
    for backend_id, backend_name in backends_to_test:
        try:
            print(f"\n🎬 Testing with {backend_name} backend...")
            
            # Try MJPG with this backend
            fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
            filename = f'test_{backend_name.replace(" ", "_")}.avi'
            
            # Note: cv2.VideoWriter doesn't directly accept backend parameter
            # But we can try setting the backend globally
            writer = cv2.VideoWriter(filename, fourcc, 15, (640, 480))
            
            if writer.isOpened():
                success = writer.write(test_frame)
                writer.release()
                
                if success and os.path.exists(filename):
                    size = os.path.getsize(filename)
                    print(f"   ✅ {backend_name} success: {size} bytes")
                    os.remove(filename)
                else:
                    print(f"   ❌ {backend_name} write failed")
            else:
                print(f"   ❌ {backend_name} writer failed to open")
                
        except Exception as e:
            print(f"   ❌ {backend_name} error: {e}")

def create_test_video_manually():
    """Try creating a video manually with raw frames"""
    print("\n🎞️ Testing manual video creation...")
    
    try:
        # Create a simple AVI file manually using MJPG
        import struct
        
        frames = []
        for i in range(30):  # 30 frames = 2 seconds at 15fps
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            frame[i*8:(i+1)*8, :] = [255, 0, 0]  # Moving red bar
            
            # Convert to JPEG
            success, jpeg_data = cv2.imencode('.jpg', frame)
            if success:
                frames.append(jpeg_data.tobytes())
        
        if frames:
            print(f"   ✅ Created {len(frames)} JPEG frames")
            
            # Try writing with OpenCV again
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            writer = cv2.VideoWriter('manual_test.avi', fourcc, 15, (320, 240))
            
            if writer.isOpened():
                frames_written = 0
                for i, frame_data in enumerate(frames):
                    # Convert back to frame
                    frame_array = np.frombuffer(frame_data, dtype=np.uint8)
                    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        success = writer.write(frame)
                        if success:
                            frames_written += 1
                
                writer.release()
                print(f"   ✅ Manual method: {frames_written} frames written")
                
                if os.path.exists('manual_test.avi'):
                    size = os.path.getsize('manual_test.avi')
                    print(f"   ✅ Manual video created: {size} bytes")
            else:
                print("   ❌ Manual method: writer failed to open")
        
    except Exception as e:
        print(f"   ❌ Manual creation error: {e}")

if __name__ == "__main__":
    # Run all tests
    working_codecs = test_advanced_codecs()
    test_backend_specific()
    create_test_video_manually()
    
    print(f"\n🏁 FINAL RESULTS:")
    if working_codecs:
        best_codec = working_codecs[0]
        print(f"✅ RECOMMENDED: {best_codec[2]} ({best_codec[0]}) with {best_codec[1]} extension")
        print(f"   Use this in your app: fourcc = cv2.VideoWriter_fourcc(*'{best_codec[0]}')")
    else:
        print("❌ NO WORKING CODECS FOUND")
        print("💡 Suggestions:")
        print("   1. Try installing additional codec pack")
        print("   2. Install ffmpeg for Windows")
        print("   3. Use different video library (like imageio)")