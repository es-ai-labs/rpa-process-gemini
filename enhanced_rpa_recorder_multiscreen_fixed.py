#!/usr/bin/env python3
"""
Enhanced RPA Recorder - MULTI-SCREEN EDITION (FIXED)
Video + Audio + Full Keyboard Logging + Visual Recording Area Highlight
Maximum visibility with zero crashes + proper multi-screen support
"""

import os
import sys
import time
import json
import threading
import traceback
import subprocess
from datetime import datetime
from pathlib import Path
import platform
import wave

# Basic imports
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    import cv2
    import numpy as np
    import mss
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Please install requirements: pip install opencv-python mss pillow")
    sys.exit(1)

# Audio imports
try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Audio recording not available (pyaudio not installed)")

# macOS specific imports
try:
    from AppKit import NSPasteboard, NSEvent, NSWorkspace
    from Cocoa import NSRunLoop, NSDefaultRunLoopMode
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False
    print("AppKit not available - some keyboard features disabled")

# Accessibility
try:
    from accessibility_enhanced import create_accessibility_inspector
    ACCESSIBILITY_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_AVAILABLE = False
    print("Enhanced accessibility not available")

PLATFORM = platform.system()

class ScreenHighlighter:
    """Visual highlight overlay for recording area"""
    
    def __init__(self):
        self.overlay_window = None
        self.highlight_active = False
        self.recording_mode = False
        self.auto_hide_timer = None
        
    def show_recording_area(self, monitor_info, recording=False):
        """Show visual highlight of recording area"""
        try:
            self.recording_mode = recording
            if PLATFORM == "Darwin":
                self._show_macos_highlight(monitor_info)
            else:
                self._show_generic_highlight(monitor_info)
        except Exception as e:
            print(f"⚠️ Could not show recording area highlight: {e}")
    
    def _show_macos_highlight(self, monitor_info):
        """Show red border around recording area on macOS"""
        try:
            # Hide existing highlight if any
            if self.overlay_window:
                self.hide_highlight()
            
            # Create overlay window
            self.overlay_window = tk.Toplevel()
            self.overlay_window.title("Recording Area Border")
            
            # Position and size the window to match monitor
            x = monitor_info['left']
            y = monitor_info['top'] 
            width = monitor_info['width']
            height = monitor_info['height']
            
            print(f"🎯 Creating highlight window: {width}x{height} at ({x}, {y})")
            
            # Configure window properties - FIXED: Make it visible!
            self.overlay_window.configure(bg='black')
            self.overlay_window.attributes('-topmost', True)  # Always on top
            self.overlay_window.overrideredirect(True)  # No title bar
            self.overlay_window.attributes('-alpha', 0.3)  # FIXED: 30% transparent (was 1% - invisible!)
            
            # Set window geometry
            self.overlay_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Force window to be visible and update
            self.overlay_window.update()
            self.overlay_window.lift()
            self.overlay_window.focus_force()
            
            # Create thick red border using multiple frames
            border_thickness = 12
            
            # Top border
            top_border = tk.Frame(self.overlay_window, bg='red', height=border_thickness)
            top_border.pack(side=tk.TOP, fill=tk.X)
            
            # Bottom border  
            bottom_border = tk.Frame(self.overlay_window, bg='red', height=border_thickness)
            bottom_border.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Middle section with left and right borders
            middle_frame = tk.Frame(self.overlay_window, bg='black')
            middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            # Left border
            left_border = tk.Frame(middle_frame, bg='red', width=border_thickness)
            left_border.pack(side=tk.LEFT, fill=tk.Y)
            
            # Right border
            right_border = tk.Frame(middle_frame, bg='red', width=border_thickness)
            right_border.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Inner content area
            inner_frame = tk.Frame(middle_frame, bg='black')
            inner_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Add recording indicator at center
            if self.recording_mode:
                indicator_text = "🔴 RECORDING THIS SCREEN 🔴"
                indicator_color = "red"
                bg_color = "black"
            else:
                indicator_text = "🔍 PREVIEW - RECORDING AREA 🔍"
                indicator_color = "orange"
                bg_color = "black"
                
            indicator_label = tk.Label(inner_frame, 
                                     text=indicator_text, 
                                     font=("Arial", 20, "bold"),
                                     fg=indicator_color, 
                                     bg=bg_color)
            indicator_label.place(relx=0.5, rely=0.1, anchor='center')
            
            # Add corner markers for extra visibility
            corner_size = 60
            corner_thickness = 8
            
            # Top-left corner
            tl_h = tk.Frame(self.overlay_window, bg='yellow', height=corner_thickness, width=corner_size)
            tl_h.place(x=0, y=0)
            tl_v = tk.Frame(self.overlay_window, bg='yellow', height=corner_size, width=corner_thickness)
            tl_v.place(x=0, y=0)
            
            # Top-right corner
            tr_h = tk.Frame(self.overlay_window, bg='yellow', height=corner_thickness, width=corner_size)
            tr_h.place(x=width-corner_size, y=0)
            tr_v = tk.Frame(self.overlay_window, bg='yellow', height=corner_size, width=corner_thickness)
            tr_v.place(x=width-corner_thickness, y=0)
            
            # Bottom-left corner
            bl_h = tk.Frame(self.overlay_window, bg='yellow', height=corner_thickness, width=corner_size)
            bl_h.place(x=0, y=height-corner_thickness)
            bl_v = tk.Frame(self.overlay_window, bg='yellow', height=corner_size, width=corner_thickness)
            bl_v.place(x=0, y=height-corner_size)
            
            # Bottom-right corner
            br_h = tk.Frame(self.overlay_window, bg='yellow', height=corner_thickness, width=corner_size)
            br_h.place(x=width-corner_size, y=height-corner_thickness)
            br_v = tk.Frame(self.overlay_window, bg='yellow', height=corner_size, width=corner_thickness)
            br_v.place(x=width-corner_thickness, y=height-corner_size)
            
            # Force final update
            self.overlay_window.update_idletasks()
            
            # Only auto-hide if NOT in recording mode
            if not self.recording_mode:
                self.auto_hide_timer = self.overlay_window.after(3000, self.hide_highlight)
                print(f"✅ Preview border shown: {width}x{height} at ({x}, {y}) - auto-hide in 3s")
            else:
                print(f"✅ Recording border shown: {width}x{height} at ({x}, {y}) - stays visible during recording")
            
            self.highlight_active = True
            
        except Exception as e:
            print(f"❌ macOS border highlight error: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_generic_highlight(self, monitor_info):
        """Generic highlight method"""
        mode = "RECORDING" if self.recording_mode else "PREVIEW"
        print(f"📺 {mode} area: {monitor_info['width']}x{monitor_info['height']} at ({monitor_info['left']}, {monitor_info['top']})")
    
    def hide_highlight(self):
        """Hide the recording area highlight"""
        try:
            if self.auto_hide_timer:
                # Cancel auto-hide timer if it exists
                if self.overlay_window:
                    self.overlay_window.after_cancel(self.auto_hide_timer)
                self.auto_hide_timer = None
                
            if self.overlay_window:
                self.overlay_window.destroy()
                self.overlay_window = None
            self.highlight_active = False
            self.recording_mode = False
            print("📺 Recording area highlight hidden")
        except:
            pass

class MultiScreenVideoRecorder:
    """Multi-screen video recorder with proper frame writing and visual feedback"""
    
    def __init__(self):
        self.recording = False
        self.output_path = None
        self.fps = 15
        self.record_thread = None
        self.audio_thread = None
        self.video_writer = None
        self.audio_frames = []
        self.selected_monitor = 1  # Default to primary monitor
        self.highlighter = ScreenHighlighter()
        
        # Audio settings
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 22050
        self.chunk = 512
        self.audio = None
        
        # SYNC FIX: Shared timing coordination
        self.recording_start_time = None
        self.sync_barrier = threading.Barrier(2)  # For audio and video sync
        self.frame_timestamps = []  # Track actual frame timing
        
    def get_available_monitors(self):
        """Get list of available monitors"""
        try:
            with mss.mss() as sct:
                monitors = []
                for i, monitor in enumerate(sct.monitors):
                    if i == 0:  # Skip the "All monitors" option
                        continue
                    monitors.append({
                        'index': i,
                        'name': f"Monitor {i}",
                        'resolution': f"{monitor['width']}x{monitor['height']}",
                        'position': f"({monitor['left']}, {monitor['top']})",
                        'info': f"Monitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})",
                        'monitor_data': monitor
                    })
                return monitors
        except Exception as e:
            print(f"Error getting monitors: {e}")
            return [{'index': 1, 'name': 'Primary Monitor', 'resolution': 'Unknown', 
                    'position': '(0, 0)', 'info': 'Primary Monitor', 'monitor_data': {}}]
    
    def set_monitor(self, monitor_index):
        """Set which monitor to record"""
        self.selected_monitor = monitor_index
        print(f"📺 Selected monitor {monitor_index} for recording")
        
        # Show visual highlight of recording area (preview mode)
        monitors = self.get_available_monitors()
        for monitor in monitors:
            if monitor['index'] == monitor_index:
                self.highlighter.show_recording_area(monitor['monitor_data'], recording=False)
                break
    
    def start_recording(self, output_path, fps=15, record_audio=True):
        """Start multi-screen recording with improved frame writing and sync"""
        if self.recording:
            return False
        
        self.output_path = output_path
        self.fps = fps
        self.recording = True
        self.audio_frames = []
        self.frame_timestamps = []
        
        print(f"🎬 Starting multi-screen recording on monitor {self.selected_monitor}: {output_path}")
        
        # Show recording border (stays visible during recording)
        monitors = self.get_available_monitors()
        for monitor in monitors:
            if monitor['index'] == self.selected_monitor:
                self.highlighter.show_recording_area(monitor['monitor_data'], recording=True)
                break
        
        # SYNC FIX: Initialize sync barrier for proper coordination
        barrier_count = 1  # Always have video
        if AUDIO_AVAILABLE and record_audio:
            barrier_count = 2
        self.sync_barrier = threading.Barrier(barrier_count)
        
        # Start video recording
        self.record_thread = threading.Thread(target=self._video_loop)
        self.record_thread.daemon = True
        self.record_thread.start()
        
        # Start audio recording
        if AUDIO_AVAILABLE and record_audio:
            try:
                self.audio_thread = threading.Thread(target=self._audio_loop)
                self.audio_thread.daemon = True
                self.audio_thread.start()
                print("🎤 Multi-screen audio recording enabled")
            except Exception as e:
                print(f"⚠️ Audio recording failed: {e}")
        
        return True
    
    def _video_loop(self):
        """FIXED: Video recording loop for specific monitor"""
        try:
            with mss.mss() as sct:
                # Get the specific monitor
                if self.selected_monitor >= len(sct.monitors):
                    print(f"❌ Monitor {self.selected_monitor} not available, using monitor 1")
                    self.selected_monitor = 1
                
                monitor = sct.monitors[self.selected_monitor]
                print(f"📺 Recording monitor {self.selected_monitor}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
                
                # FIXED: Take first screenshot to determine ACTUAL frame dimensions (like working version)
                try:
                    first_screenshot = sct.grab(monitor)
                    first_frame = np.array(first_screenshot)
                    print(f"✅ First screenshot captured: {first_frame.shape}")
                    
                    # Convert to BGR to get final dimensions
                    if first_frame.shape[2] == 4:  # BGRA
                        first_frame = cv2.cvtColor(first_frame, cv2.COLOR_BGRA2BGR)
                    elif first_frame.shape[2] == 3:  # RGB
                        first_frame = cv2.cvtColor(first_frame, cv2.COLOR_RGB2BGR)
                    
                    # FIXED: Use ACTUAL frame dimensions, not monitor info
                    height, width = first_frame.shape[:2]
                    print(f"📐 ACTUAL frame dimensions from screenshot: {width}x{height}")
                    
                except Exception as e:
                    print(f"❌ First screenshot failed: {e}")
                    return
                
                # FIXED: Ensure dimensions are even and reasonable
                if width % 2 != 0:
                    width -= 1
                if height % 2 != 0:
                    height -= 1
                
                # Minimum size check
                if width < 100 or height < 100:
                    print(f"❌ Invalid dimensions: {width}x{height}")
                    return
                
                # Validate and adjust FPS for better compatibility
                if self.fps > 30:
                    self.fps = 30
                    print(f"🔧 Adjusted FPS to {self.fps} for compatibility")
                elif self.fps < 5:
                    self.fps = 10
                    print(f"🔧 Adjusted FPS to {self.fps} for compatibility")
                
                print(f"📺 Video dimensions: {width}x{height}, FPS: {self.fps}")
                print(f"📁 Output path: {self.output_path}")
                
                # FIXED: Use simpler codec approach like working version - try H264 first, then XVID
                print(f"🎬 Initializing video writer with dimensions {width}x{height}")
                
                # Try H264 first (like working version)
                fourcc = cv2.VideoWriter_fourcc(*'H264')
                self.video_writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))
                
                if not self.video_writer.isOpened():
                    print("❌ H264 failed, trying XVID fallback...")
                    # Fallback to XVID with .avi extension (like working version)
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    fallback_path = self.output_path.replace('.mp4', '.avi')
                    self.video_writer = cv2.VideoWriter(fallback_path, fourcc, self.fps, (width, height))
                    
                    if self.video_writer.isOpened():
                        self.output_path = fallback_path
                        print(f"✅ XVID fallback successful: {fallback_path}")
                    else:
                        print("❌ Both H264 and XVID failed!")
                        return
                else:
                    print("✅ H264 codec initialized successfully")
                
                print(f"✅ Video writer initialized successfully")
                
                frame_count = 0
                last_status_time = time.time()
                
                # SYNC FIX: Wait for all threads to be ready, then start synchronized
                print("📹 Video thread ready, waiting for sync...")
                try:
                    self.sync_barrier.wait(timeout=5.0)
                    self.recording_start_time = time.time()
                    print(f"✅ Synchronized recording started at {self.recording_start_time}")
                except threading.BrokenBarrierError:
                    print("⚠️ Sync barrier broken, starting video anyway")
                    self.recording_start_time = time.time()
                
                # SYNC FIX: Precise frame timing
                target_frame_duration = 1.0 / self.fps
                next_frame_time = self.recording_start_time
                
                while self.recording:
                    try:
                        # Capture screenshot
                        screenshot = sct.grab(monitor)
                        frame = np.array(screenshot)
                        
                        # FIXED: Proper color space conversion
                        if frame.shape[2] == 4:  # BGRA
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                        elif frame.shape[2] == 3:  # RGB  
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        # FIXED: ALWAYS ensure frame dimensions match video writer (like working version)
                        if frame.shape[:2] != (height, width):
                            print(f"🔧 Resizing frame from {frame.shape[1]}x{frame.shape[0]} to {width}x{height}")
                            frame = cv2.resize(frame, (width, height))
                        
                        # Ensure proper data type
                        frame = frame.astype(np.uint8)
                        
                        # FIXED: Enhanced frame validation before writing
                        if frame.size == 0:
                            print("⚠️ Empty frame, skipping...")
                            continue
                        
                        # Validate frame properties
                        if frame.shape[0] != height or frame.shape[1] != width:
                            print(f"⚠️ Frame size mismatch: expected {width}x{height}, got {frame.shape[1]}x{frame.shape[0]}")
                            frame = cv2.resize(frame, (width, height))
                            
                        if frame.dtype != np.uint8:
                            print(f"⚠️ Frame dtype mismatch: expected uint8, got {frame.dtype}")
                            frame = frame.astype(np.uint8)
                        
                        # Ensure frame is contiguous in memory
                        if not frame.flags['C_CONTIGUOUS']:
                            frame = np.ascontiguousarray(frame)
                        
                        # Write frame with enhanced error checking
                        if self.video_writer and self.video_writer.isOpened():
                            try:
                                success = self.video_writer.write(frame)
                                if success:
                                    frame_count += 1
                                    
                                    # SYNC FIX: Track actual frame timestamp
                                    frame_timestamp = time.time() - self.recording_start_time
                                    self.frame_timestamps.append(frame_timestamp)
                                    
                                    # Status update every 3 seconds
                                    current_time = time.time()
                                    if current_time - last_status_time > 3.0:
                                        actual_fps = frame_count / frame_timestamp if frame_timestamp > 0 else 0
                                        print(f"📹 Recording: {frame_count} frames ({frame_timestamp:.1f}s) actual FPS: {actual_fps:.1f} ✅")
                                        last_status_time = current_time
                                else:
                                    print(f"❌ Frame write returned False at frame {frame_count}")
                                    print(f"   Frame shape: {frame.shape}, dtype: {frame.dtype}")
                                    print(f"   Writer opened: {self.video_writer.isOpened()}")
                                    
                                    # Try to recover by recreating the writer
                                    if frame_count > 0:  # Only if we've successfully written some frames
                                        print("🔧 Attempting to recover video writer...")
                                        try:
                                            fourcc = self.video_writer.get(cv2.CAP_PROP_FOURCC)
                                            self.video_writer.release()
                                            self.video_writer = cv2.VideoWriter(self.output_path, int(fourcc), self.fps, (width, height))
                                            if self.video_writer.isOpened():
                                                print("✅ Video writer recovered")
                                            else:
                                                print("❌ Video writer recovery failed")
                                        except Exception as recovery_error:
                                            print(f"❌ Recovery error: {recovery_error}")
                                            
                            except Exception as write_error:
                                print(f"❌ Frame write exception: {write_error}")
                        else:
                            print("❌ Video writer not available or not opened")
                        
                        # SYNC FIX: Precise frame rate control
                        next_frame_time += target_frame_duration
                        current_time = time.time()
                        sleep_time = next_frame_time - current_time
                        
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        elif sleep_time < -target_frame_duration:
                            # If we're more than one frame behind, skip ahead
                            next_frame_time = current_time + target_frame_duration
                        
                    except Exception as e:
                        print(f"Frame capture error: {e}")
                        time.sleep(0.1)
                
                print(f"📹 Multi-screen video complete: {frame_count} frames on monitor {self.selected_monitor}")
                
        except Exception as e:
            print(f"Video recording error: {e}")
            traceback.print_exc()
        finally:
            if self.video_writer:
                self.video_writer.release()
                print("📹 Video writer released")
    
    def _audio_loop(self):
        """Audio recording loop with sync coordination"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Find a working input device
            device_info = None
            for i in range(self.audio.get_device_count()):
                try:
                    info = self.audio.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        device_info = info
                        print(f"🎤 Using audio device: {info['name']}")
                        break
                except:
                    continue
            
            if not device_info:
                print("❌ No audio input device found")
                return
            
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                input_device_index=device_info['index']
            )
            
            # SYNC FIX: Wait for sync with video thread
            print("🎤 Audio thread ready, waiting for sync...")
            try:
                self.sync_barrier.wait(timeout=5.0)
                print("✅ Audio synchronized with video")
            except threading.BrokenBarrierError:
                print("⚠️ Audio sync barrier broken, starting anyway")
            
            audio_start_time = time.time()
            chunk_count = 0
            
            while self.recording:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    self.audio_frames.append(data)
                    chunk_count += 1
                    
                    # Optional: Track audio timing for debugging
                    if chunk_count % 100 == 0:  # Every ~2.3 seconds at 22050Hz/512chunk
                        audio_duration = chunk_count * self.chunk / self.rate
                        actual_duration = time.time() - audio_start_time
                        print(f"🎵 Audio: {audio_duration:.1f}s recorded, {actual_duration:.1f}s elapsed")
                        
                except:
                    time.sleep(0.01)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Audio error: {e}")
        finally:
            if self.audio:
                self.audio.terminate()
    
    def stop_recording(self):
        """Stop recording and combine audio/video"""
        if not self.recording:
            return
        
        print("🛑 Stopping multi-screen recording...")
        self.recording = False
        
        # Hide recording border
        self.highlighter.hide_highlight()
        
        if self.record_thread:
            self.record_thread.join(timeout=5)
        if self.audio_thread:
            self.audio_thread.join(timeout=3)
        
        # Save audio and combine with video
        if self.audio_frames:
            self._save_and_combine_audio()
        
        print("✅ Multi-screen recording stopped")
    
    def _save_and_combine_audio(self):
        """Save audio and attempt to combine with video using ffmpeg with sync fixes"""
        try:
            # Save audio to temporary file
            audio_path = self.output_path.replace('.mp4', '_audio.wav')
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.get_sample_size(self.audio_format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.audio_frames))
            
            # Calculate actual durations for sync debugging
            audio_duration = len(self.audio_frames) * self.chunk / self.rate
            video_duration = len(self.frame_timestamps) / self.fps if self.frame_timestamps else 0
            
            print(f"🎵 Audio saved: {audio_path}")
            print(f"📊 Duration analysis: Video={video_duration:.2f}s, Audio={audio_duration:.2f}s, Diff={abs(video_duration-audio_duration):.2f}s")
            
            # Try to combine audio and video using ffmpeg with better sync handling
            try:
                output_with_audio = self.output_path.replace('.mp4', '_with_audio.mp4')
                
                # SYNC FIX: Enhanced ffmpeg command with sync options
                cmd = [
                    'ffmpeg', '-y',  # -y to overwrite existing files
                    '-i', self.output_path,  # video input
                    '-i', audio_path,        # audio input
                    '-c:v', 'copy',          # copy video codec (no re-encoding)
                    '-c:a', 'aac',           # encode audio as AAC
                    '-map', '0:v:0',         # map video from first input
                    '-map', '1:a:0',         # map audio from second input
                    '-shortest',             # use shortest stream duration to avoid sync drift
                    '-avoid_negative_ts', 'make_zero',  # handle timestamp issues
                    '-fflags', '+genpts',    # generate presentation timestamps
                    output_with_audio
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"✅ Combined video with audio: {output_with_audio}")
                    # Optionally remove the separate files
                    try:
                        os.remove(self.output_path)  # Remove video-only file
                        os.remove(audio_path)        # Remove audio-only file
                        # Rename combined file to original name
                        os.rename(output_with_audio, self.output_path)
                        print(f"🎬 Final video with audio: {self.output_path}")
                    except:
                        print(f"⚠️ Could not clean up temporary files")
                else:
                    print(f"⚠️ ffmpeg failed: {result.stderr}")
                    print(f"💡 Audio saved separately as: {audio_path}")
                    
            except subprocess.TimeoutExpired:
                print("⚠️ ffmpeg timed out - audio saved separately")
            except FileNotFoundError:
                print("⚠️ ffmpeg not found - audio saved separately")
                print("💡 Install ffmpeg to automatically combine audio and video")
                print("💡 On macOS: brew install ffmpeg")
            except Exception as e:
                print(f"⚠️ Error combining audio/video: {e}")
                print(f"💡 Audio saved separately as: {audio_path}")
            
        except Exception as e:
            print(f"Audio save error: {e}")

class FullKeyboardLogger:
    """ENHANCED keyboard logger with Core Graphics event monitoring"""
    
    def __init__(self):
        self.keyboard_events = []
        self.logging = False
        self.event_tap = None
        self.event_thread = None
        self.clipboard_thread = None
        self.app_monitor_thread = None
        
        # State tracking
        self.last_clipboard = ""
        self.last_app = ""
        self.typing_session_start = None
        self.consecutive_keys = 0
        self.last_key_time = 0
        
    def start_logging(self):
        """Start comprehensive keyboard logging"""
        if self.logging:
            return True
            
        self.logging = True
        self.keyboard_events = []
        
        print("⌨️ Starting ENHANCED keyboard logging...")
        
        # Start Core Graphics event monitoring
        self.event_thread = threading.Thread(target=self._core_graphics_monitor)
        self.event_thread.daemon = True
        self.event_thread.start()
        
        # Start clipboard monitoring
        self.clipboard_thread = threading.Thread(target=self._clipboard_monitor)
        self.clipboard_thread.daemon = True
        self.clipboard_thread.start()
        
        # Start app monitoring
        self.app_monitor_thread = threading.Thread(target=self._app_monitor)
        self.app_monitor_thread.daemon = True
        self.app_monitor_thread.start()
        
        return True
    
    def _core_graphics_monitor(self):
        """Enhanced Core Graphics keyboard event monitoring"""
        try:
            import Quartz
            from Quartz import (
                CGEventTapCreate, CGEventTapEnable, CGEventMaskBit, 
                kCGEventKeyDown, kCGEventKeyUp, kCGEventFlagsChanged,
                kCGHIDEventTap, kCGHeadInsertEventTap, kCGEventTapOptionListenOnly,
                CFRunLoopGetCurrent, CFRunLoopAddSource, kCFRunLoopDefaultMode,
                CGEventGetIntegerValueField, kCGKeyboardEventKeycode,
                CFMachPortCreateRunLoopSource, CFMachPortInvalidate,
                CGEventGetFlags
            )
            from Cocoa import NSRunLoop, NSDefaultRunLoopMode, NSDate
            
            print("🔑 Starting Core Graphics keyboard monitoring...")
            
            def key_event_callback(proxy, event_type, event, refcon):
                try:
                    if not self.logging:
                        return event
                    
                    timestamp = time.time()
                    key_code = int(CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode))
                    key_name = self._key_code_to_name(key_code)
                    flags = CGEventGetFlags(event)
                    modifiers = self._decode_flags(flags)
                    
                    # Log key events with full context
                    if event_type == kCGEventKeyDown:
                        self._log_key_event({
                            'type': 'key_press',
                            'key_code': key_code,
                            'key_name': key_name,
                            'modifiers': modifiers,
                            'is_character': key_name.isalnum() or key_name in ['.', ',', '!', '?', ';', ':', "'", '"', ' '],
                            'is_special': key_name in ['Return', 'Tab', 'Delete', 'Escape', 'Space'],
                            'timestamp': timestamp,
                            'capture_method': 'core_graphics'
                        })
                        
                        # Track typing patterns
                        self._update_typing_session(key_name, timestamp)
                        
                        print(f"🔑 Key pressed: {key_name} (code: {key_code}) {'+'.join(modifiers) if modifiers else ''}")
                    
                    elif event_type == kCGEventKeyUp:
                        # Only log key releases for special keys
                        if key_name in ['Return', 'Tab', 'Delete', 'Escape', 'Command', 'Shift', 'Control', 'Option']:
                            self._log_key_event({
                                'type': 'key_release',
                                'key_code': key_code,
                                'key_name': key_name,
                                'modifiers': modifiers,
                                'timestamp': timestamp,
                                'capture_method': 'core_graphics'
                            })
                    
                    elif event_type == kCGEventFlagsChanged:
                        # Log modifier changes
                        self._log_key_event({
                            'type': 'modifier_change',
                            'modifiers': modifiers,
                            'timestamp': timestamp,
                            'capture_method': 'core_graphics'
                        })
                    
                    return event
                    
                except Exception as e:
                    print(f"Key event callback error: {e}")
                    return event
            
            # Create event tap with proper parameters
            event_mask = (
                CGEventMaskBit(kCGEventKeyDown) |
                CGEventMaskBit(kCGEventKeyUp) |
                CGEventMaskBit(kCGEventFlagsChanged)
            )
            
            try:
                event_tap = CGEventTapCreate(
                    kCGHIDEventTap,
                    kCGHeadInsertEventTap,
                    kCGEventTapOptionListenOnly,
                    event_mask,
                    key_event_callback,
                    None
                )
                
                if event_tap is None:
                    print("❌ Failed to create event tap - accessibility permissions needed")
                    print("💡 Enable 'Accessibility' permission for Terminal/Python in System Preferences")
                    return
                
                # Set up run loop
                run_loop_source = CFMachPortCreateRunLoopSource(None, event_tap, 0)
                run_loop = CFRunLoopGetCurrent()
                CFRunLoopAddSource(run_loop, run_loop_source, kCFRunLoopDefaultMode)
                
                CGEventTapEnable(event_tap, True)
                print("✅ Core Graphics event tap enabled - capturing all keystrokes")
                
                # Run event loop
                while self.logging:
                    try:
                        run_until = NSDate.dateWithTimeIntervalSinceNow_(0.1)
                        NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, run_until)
                    except Exception as e:
                        print(f"Event loop error: {e}")
                        time.sleep(0.1)
                
                # Cleanup
                CGEventTapEnable(event_tap, False)
                print("🛑 Core Graphics event tap disabled")
                
            except Exception as e:
                print(f"❌ Event tap setup failed: {e}")
                
        except ImportError:
            print("❌ Quartz not available - falling back to basic monitoring")
        except Exception as e:
            print(f"❌ Core Graphics monitoring failed: {e}")
    
    def _key_code_to_name(self, key_code):
        """Convert macOS key code to readable name"""
        key_map = {
            0: 'a', 1: 's', 2: 'd', 3: 'f', 4: 'h', 5: 'g', 6: 'z', 7: 'x', 8: 'c', 9: 'v',
            10: '§', 11: 'b', 12: 'q', 13: 'w', 14: 'e', 15: 'r', 16: 'y', 17: 't',
            18: '1', 19: '2', 20: '3', 21: '4', 22: '6', 23: '5', 24: '=', 25: '9',
            26: '7', 27: '-', 28: '8', 29: '0', 30: ']', 31: 'o', 32: 'u', 33: '[',
            34: 'i', 35: 'p', 36: 'Return', 37: 'l', 38: 'j', 39: "'", 40: 'k', 41: ';',
            42: '\\', 43: ',', 44: '/', 45: 'n', 46: 'm', 47: '.', 48: 'Tab',
            49: 'Space', 50: '`', 51: 'Delete', 52: 'Enter', 53: 'Escape',
            54: 'RightCommand', 55: 'Command', 56: 'Shift', 57: 'CapsLock',
            58: 'Option', 59: 'Control', 60: 'RightShift', 61: 'RightOption',
            62: 'RightControl', 63: 'Function'
        }
        return key_map.get(key_code, f'Key{key_code}')
    
    def _decode_flags(self, flags):
        """Decode modifier flags"""
        modifiers = []
        if flags & (1 << 17):  # Shift
            modifiers.append('Shift')
        if flags & (1 << 18):  # Control
            modifiers.append('Control')
        if flags & (1 << 19):  # Option
            modifiers.append('Option')
        if flags & (1 << 20):  # Command
            modifiers.append('Command')
        return modifiers
    
    def _clipboard_monitor(self):
        """Monitor clipboard changes"""
        if not APPKIT_AVAILABLE:
            return
            
        try:
            self.last_clipboard = self._get_clipboard()
            
            while self.logging:
                try:
                    current_clipboard = self._get_clipboard()
                    
                    if current_clipboard != self.last_clipboard and current_clipboard:
                        self._log_key_event({
                            'type': 'clipboard_change',
                            'action': 'copy_paste',
                            'content_length': len(current_clipboard),
                            'content_preview': self._safe_preview(current_clipboard),
                            'timestamp': time.time(),
                            'inferred_shortcut': 'Cmd+C or Cmd+V'
                        })
                        self.last_clipboard = current_clipboard
                    
                    time.sleep(0.3)
                except:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Clipboard monitoring error: {e}")
    
    def _app_monitor(self):
        """Monitor app focus changes"""
        if not APPKIT_AVAILABLE:
            return
            
        try:
            self.last_app = self._get_current_app()
            
            while self.logging:
                try:
                    current_app = self._get_current_app()
                    
                    if current_app != self.last_app:
                        self._log_key_event({
                            'type': 'app_switch',
                            'from_app': self.last_app,
                            'to_app': current_app,
                            'timestamp': time.time(),
                            'inferred_shortcut': 'Cmd+Tab or mouse click'
                        })
                        self.last_app = current_app
                    
                    time.sleep(0.5)
                except:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"App monitoring error: {e}")
    
    def _get_clipboard(self):
        """Get clipboard content"""
        try:
            pb = NSPasteboard.generalPasteboard()
            return pb.stringForType_("public.utf8-plain-text") or ""
        except:
            return ""
    
    def _get_current_app(self):
        """Get current app name"""
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            return active_app.get('NSApplicationName', 'Unknown')
        except:
            return "Unknown"
    
    def _safe_preview(self, text, max_length=50):
        """Create safe text preview"""
        if not text:
            return ""
        
        if any(keyword in text.lower() for keyword in ['password', 'secret', 'token', 'key']):
            return "[SENSITIVE_CONTENT_MASKED]"
        
        preview = text.replace('\n', ' ').replace('\t', ' ')
        if len(preview) > max_length:
            preview = preview[:max_length] + '...'
        
        return preview
    
    def _update_typing_session(self, key_name, timestamp):
        """Track typing sessions and patterns"""
        try:
            # Start typing session
            if self.typing_session_start is None:
                self.typing_session_start = timestamp
                self.consecutive_keys = 0
            
            # Check if key is part of current session (within 3 seconds)
            if timestamp - self.last_key_time < 3.0:
                self.consecutive_keys += 1
            else:
                # End current session and start new one
                if self.consecutive_keys > 5:  # Only log substantial typing sessions
                    session_duration = self.last_key_time - self.typing_session_start
                    self._log_key_event({
                        'type': 'typing_session_end',
                        'key_count': self.consecutive_keys,
                        'duration': session_duration,
                        'typing_speed': self.consecutive_keys / max(session_duration, 1),
                        'timestamp': timestamp
                    })
                
                # Start new session
                self.typing_session_start = timestamp
                self.consecutive_keys = 1
            
            self.last_key_time = timestamp
            
        except Exception as e:
            print(f"Typing session tracking error: {e}")
    
    def _log_key_event(self, event_data):
        """Log keyboard event"""
        try:
            event = {
                'datetime': datetime.now().isoformat(),
                'source': 'enhanced_keyboard_logger',
                **event_data
            }
            self.keyboard_events.append(event)
            
        except Exception as e:
            print(f"Keyboard event logging error: {e}")
    
    def stop_logging(self):
        """Stop keyboard logging"""
        if not self.logging:
            return
            
        self.logging = False
        
        # Wait for threads to finish
        if self.event_thread:
            self.event_thread.join(timeout=2)
        if self.clipboard_thread:
            self.clipboard_thread.join(timeout=1)
        if self.app_monitor_thread:
            self.app_monitor_thread.join(timeout=1)
        
        print(f"✅ Enhanced keyboard logging stopped - captured {len(self.keyboard_events)} events")

class MultiScreenInteractionLogger:
    """Multi-screen interaction logger with enhanced keyboard support"""
    
    def __init__(self, accessibility_inspector=None):
        self.inspector = accessibility_inspector
        self.interactions = []
        self.logging = False
        
        # Mouse tracking
        self.mouse_thread = None
        self.last_position = None
        self.click_state = False
        
        # Enhanced keyboard logger
        self.keyboard_logger = FullKeyboardLogger()
        
        self.start_time = None
        
    def start_logging(self, capture_keyboard=True):
        """Start comprehensive interaction logging"""
        if self.logging:
            return True
        
        self.logging = True
        self.interactions = []
        self.start_time = time.time()
        
        # Start mouse tracking
        self.mouse_thread = threading.Thread(target=self._mouse_loop)
        self.mouse_thread.daemon = True
        self.mouse_thread.start()
        
        # Start enhanced keyboard logging
        if capture_keyboard and APPKIT_AVAILABLE:
            self.keyboard_logger.start_logging()
        
        print("✅ Multi-screen interaction logging started with enhanced keyboard capture")
        return True
    
    def _mouse_loop(self):
        """Mouse tracking loop"""
        print("🔍 Starting mouse tracking...")
        
        while self.logging:
            try:
                current_pos = self._get_safe_mouse_position()
                
                if current_pos != (0, 0):
                    # Mouse movement detection
                    if self.last_position:
                        dx = abs(current_pos[0] - self.last_position[0])
                        dy = abs(current_pos[1] - self.last_position[1])
                        
                        if dx > 10 or dy > 10:
                            interaction = {
                                'type': 'mouse_move',
                                'timestamp': self._get_relative_timestamp(),
                                'datetime': datetime.now().isoformat(),
                                'position': {'x': current_pos[0], 'y': current_pos[1]},
                                'movement': {'dx': dx, 'dy': dy},
                                'source': 'multiscreen_enhanced'
                            }
                            self._safe_log_interaction(interaction)
                    
                    # Click detection
                    self._check_for_clicks(current_pos)
                    self.last_position = current_pos
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"⚠️ Mouse tracking error: {e}")
                time.sleep(0.5)
        
        print("🛑 Mouse tracking stopped")
    
    def _get_safe_mouse_position(self):
        """Get mouse position safely"""
        try:
            if PLATFORM == "Darwin":
                from Cocoa import NSEvent
                from AppKit import NSScreen
                point = NSEvent.mouseLocation()
                screen_height = NSScreen.mainScreen().frame().size.height
                return (int(point.x), int(screen_height - point.y))
            else:
                import pyautogui
                return pyautogui.position()
        except:
            return (0, 0)
    
    def _check_for_clicks(self, current_pos):
        """Click detection"""
        try:
            if PLATFORM == "Darwin":
                from Cocoa import NSEvent
                current_mouse_down = NSEvent.pressedMouseButtons()
                
                if current_mouse_down > 0 and not self.click_state:
                    self.click_state = True
                    interaction = {
                        'type': 'mouse_press',
                        'timestamp': self._get_relative_timestamp(),
                        'datetime': datetime.now().isoformat(),
                        'position': {'x': current_pos[0], 'y': current_pos[1]},
                        'button': 'left',
                        'source': 'multiscreen_enhanced'
                    }
                    self._safe_log_interaction(interaction)
                    
                elif current_mouse_down == 0 and self.click_state:
                    self.click_state = False
                    interaction = {
                        'type': 'mouse_release',
                        'timestamp': self._get_relative_timestamp(),
                        'datetime': datetime.now().isoformat(),
                        'position': {'x': current_pos[0], 'y': current_pos[1]},
                        'button': 'left',
                        'source': 'multiscreen_enhanced'
                    }
                    self._safe_log_interaction(interaction)
        except:
            pass
    
    def _get_relative_timestamp(self):
        """Get relative timestamp"""
        try:
            return time.time() - self.start_time if self.start_time else 0
        except:
            return 0
    
    def _safe_log_interaction(self, interaction):
        """Log interaction safely"""
        try:
            self.interactions.append(interaction)
            
            if len(self.interactions) % 50 == 0:
                print(f"📝 Logged {len(self.interactions)} interactions...")
                
        except Exception as e:
            print(f"⚠️ Interaction log error: {e}")
    
    def stop_logging(self):
        """Stop interaction logging"""
        if not self.logging:
            return
        
        self.logging = False
        
        # Stop mouse thread
        if self.mouse_thread:
            self.mouse_thread.join(timeout=3)
        
        # Stop keyboard logger
        self.keyboard_logger.stop_logging()
        
        print(f"✅ Multi-screen interaction logging stopped")
        print(f"   Mouse interactions: {len(self.interactions)}")
        print(f"   Keyboard events: {len(self.keyboard_logger.keyboard_events)}")
    
    def save_interactions(self, output_path):
        """Save all interaction data"""
        try:
            comprehensive_data = {
                'session_info': {
                    'platform': PLATFORM,
                    'start_time': datetime.now().isoformat(),
                    'duration': self._get_relative_timestamp(),
                    'interaction_count': len(self.interactions),
                    'keyboard_event_count': len(self.keyboard_logger.keyboard_events),
                    'capture_method': 'multiscreen_enhanced_fixed',
                    'features': {
                        'multi_screen_recording': True,
                        'visual_recording_highlight': True,
                        'enhanced_keyboard_logging': True,
                        'core_graphics_event_tap': True,
                        'mouse_tracking': True,
                        'click_detection': True,
                        'clipboard_monitoring': True,
                        'app_switching': True,
                        'typing_session_analysis': True,
                        'audio_video_integration': True
                    }
                },
                'mouse_interactions': self.interactions,
                'keyboard_events': self.keyboard_logger.keyboard_events
            }
            
            with open(output_path, 'w') as f:
                json.dump(comprehensive_data, f, indent=2)
            
            print(f"💾 Enhanced interactions saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving interactions: {e}")
            return False

class MultiScreenRPARecorderApp:
    """Enhanced Multi-screen RPA Recorder GUI with visual feedback"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced RPA Recorder (Multi-Screen Fixed Edition)")
        self.root.geometry("700x580")  # More compact size
        
        # Initialize components
        self.accessibility_inspector = None
        if ACCESSIBILITY_AVAILABLE:
            try:
                self.accessibility_inspector = create_accessibility_inspector()
            except Exception as e:
                print(f"⚠️ Accessibility inspector failed: {e}")
        
        self.video_recorder = MultiScreenVideoRecorder()
        self.interaction_logger = MultiScreenInteractionLogger(self.accessibility_inspector)
        
        # State
        self.recording = False
        self.output_directory = str(Path.cwd() / "records")
        Path(self.output_directory).mkdir(exist_ok=True)
        
        # Get available monitors
        self.monitors = self.video_recorder.get_available_monitors()
        
        self.setup_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """Setup compact multi-screen GUI"""
        # Compact title section
        title_label = ttk.Label(self.root, text="Enhanced RPA Recorder", font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ttk.Label(self.root, text="Multi-Screen + Enhanced Keyboard + Persistent Recording Border", 
                                 font=("Arial", 10), foreground="darkblue")
        subtitle_label.pack(pady=(0, 5))
        
        # Status
        self.status_var = tk.StringVar(value="Ready for recording")
        status_label = ttk.Label(self.root, textvariable=self.status_var, font=("Arial", 11, "bold"))
        status_label.pack(pady=3)
        
        # Main content frame with two columns
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left column
        left_column = ttk.Frame(main_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right column
        right_column = ttk.Frame(main_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # LEFT COLUMN CONTENT
        
        # Monitor selection (compact)
        monitor_frame = ttk.LabelFrame(left_column, text="📺 Monitor Selection")
        monitor_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(monitor_frame, text="Select monitor:", font=("Arial", 9)).pack(anchor=tk.W, pady=2)
        
        self.monitor_var = tk.StringVar()
        monitor_dropdown = ttk.Combobox(monitor_frame, textvariable=self.monitor_var, state="readonly", font=("Arial", 9))
        monitor_dropdown['values'] = [f"Monitor {m['index']}: {m['resolution']}" for m in self.monitors]
        if self.monitors:
            monitor_dropdown.current(0)
        monitor_dropdown.pack(fill=tk.X, pady=2)
        monitor_dropdown.bind('<<ComboboxSelected>>', self.on_monitor_changed)
        
        # Preview and info in same row
        preview_info_frame = ttk.Frame(monitor_frame)
        preview_info_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(preview_info_frame, text="🔍 Preview Border", 
                  command=self.preview_recording_area).pack(side=tk.LEFT)
        
        ttk.Label(preview_info_frame, text=f"({len(self.monitors)} monitors)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.RIGHT)
        
        # Output directory (compact)
        dir_frame = ttk.LabelFrame(left_column, text="📁 Output")
        dir_frame.pack(fill=tk.X, pady=5)
        
        dir_row = ttk.Frame(dir_frame)
        dir_row.pack(fill=tk.X, pady=2)
        
        self.dir_var = tk.StringVar(value=self.output_directory)
        dir_entry = ttk.Entry(dir_row, textvariable=self.dir_var, state="readonly", font=("Arial", 8))
        dir_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)
        ttk.Button(dir_row, text="Browse", command=self.browse_directory).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Recording options (compact)
        options_frame = ttk.LabelFrame(left_column, text="🎬 Recording")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Video and audio in same row
        video_audio_frame = ttk.Frame(options_frame)
        video_audio_frame.pack(fill=tk.X, pady=2)
        
        self.video_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(video_audio_frame, text="Video", variable=self.video_enabled).pack(side=tk.LEFT)
        
        self.audio_enabled = tk.BooleanVar(value=AUDIO_AVAILABLE)
        audio_cb = ttk.Checkbutton(video_audio_frame, text="Audio", variable=self.audio_enabled)
        audio_cb.pack(side=tk.LEFT, padx=(10, 0))
        if not AUDIO_AVAILABLE:
            audio_cb.configure(state="disabled")
        
        # FPS in same row
        ttk.Label(video_audio_frame, text="FPS:").pack(side=tk.LEFT, padx=(10, 0))
        self.fps_var = tk.StringVar(value="15")
        ttk.Entry(video_audio_frame, textvariable=self.fps_var, width=4, font=("Arial", 9)).pack(side=tk.LEFT, padx=(2, 0))
        
        # RIGHT COLUMN CONTENT
        
        # Enhanced keyboard (compact)
        keyboard_frame = ttk.LabelFrame(right_column, text="⌨️ Keyboard Logging")
        keyboard_frame.pack(fill=tk.X, pady=5)
        
        self.keyboard_enabled = tk.BooleanVar(value=APPKIT_AVAILABLE)
        keyboard_cb = ttk.Checkbutton(keyboard_frame, text="✅ Enhanced Keystroke Capture", 
                                     variable=self.keyboard_enabled)
        keyboard_cb.pack(anchor=tk.W, pady=2)
        if not APPKIT_AVAILABLE:
            keyboard_cb.configure(state="disabled")
        
        keyboard_features = "• Core Graphics event tap\n• Real-time key monitoring\n• Modifier combinations\n• Clipboard & app switching"
        ttk.Label(keyboard_frame, text=keyboard_features, font=("Arial", 8), foreground="darkgreen").pack(pady=2)
        
        # Mouse and visual features (combined)
        features_frame = ttk.LabelFrame(right_column, text="🖱️ Mouse & Visual")
        features_frame.pack(fill=tk.X, pady=5)
        
        self.mouse_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(features_frame, text="Track Mouse & Clicks", 
                       variable=self.mouse_enabled).pack(anchor=tk.W, pady=2)
        
        visual_text = "✨ RED BORDER highlight shows recording area\n🔍 Preview: orange border (auto-hides in 3s)\n🔴 Recording: red border (stays visible)"
        ttk.Label(features_frame, text=visual_text, font=("Arial", 8), foreground="purple").pack(pady=2)
        
        # Status display (compact)
        status_frame = ttk.LabelFrame(right_column, text="🚀 System Status")
        status_frame.pack(fill=tk.X, pady=5)
        
        caps_text = f"Video✅ Audio{'✅' if AUDIO_AVAILABLE else '❌'} Keyboard{'✅' if APPKIT_AVAILABLE else '❌'} Monitors{len(self.monitors)}📺"
        ttk.Label(status_frame, text=caps_text, font=("Arial", 8), foreground="blue").pack(pady=2)
        
        # Control buttons at bottom
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.record_button = ttk.Button(button_frame, text="🔴 Start Enhanced Recording", 
                                      command=self.toggle_recording, style="Accent.TButton")
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📁 Open Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
    
    def on_monitor_changed(self, event=None):
        """Handle monitor selection change"""
        try:
            selection = self.monitor_var.get()
            # Extract monitor index from selection string "Monitor X: resolution"
            if selection:
                monitor_index = int(selection.split(':')[0].replace('Monitor ', ''))
                self.video_recorder.set_monitor(monitor_index)
        except Exception as e:
            print(f"Error changing monitor: {e}")
    
    def preview_recording_area(self):
        """Preview the recording area with red border highlight"""
        try:
            selection = self.monitor_var.get()
            if selection:
                # Extract monitor index from selection string "Monitor X: resolution"
                monitor_index = int(selection.split(':')[0].replace('Monitor ', ''))
                
                # Find the monitor data
                for monitor in self.monitors:
                    if monitor['index'] == monitor_index:
                        self.video_recorder.highlighter.show_recording_area(monitor['monitor_data'], recording=False)
                        messagebox.showinfo("Red Border Preview", 
                                          f"Red border preview active!\n\nMonitor: {monitor['name']}\nResolution: {monitor['resolution']}\nPosition: {monitor['position']}\n\n🔍 Orange preview border (auto-hides in 3s)\n🔴 During recording: red border stays visible")
                        break
        except Exception as e:
            messagebox.showerror("Preview Error", f"Could not preview recording area: {e}")
    
    def browse_directory(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(initialdir=self.output_directory)
        if directory:
            self.output_directory = directory
            self.dir_var.set(directory)
    
    def toggle_recording(self):
        """Toggle recording state"""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start enhanced multi-screen recording"""
        try:
            if self.recording:
                return
            
            # Set monitor before recording
            self.on_monitor_changed()
            
            self.recording = True
            self.record_button.configure(text="Stop Recording")
            self.status_var.set("🔴 ENHANCED MULTI-SCREEN RECORDING...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_path = Path(self.output_directory) / f"enhanced_multiscreen_{timestamp}"
            
            started_components = []
            
            # Start video recording
            if self.video_enabled.get():
                try:
                    fps = max(5, min(30, int(self.fps_var.get() or 15)))
                    video_path = str(base_path) + ".mp4"
                    record_audio = self.audio_enabled.get() and AUDIO_AVAILABLE
                    
                    success = self.video_recorder.start_recording(video_path, fps, record_audio)
                    if success:
                        if record_audio:
                            started_components.append("video+audio-fixed")
                        else:
                            started_components.append("video-fixed")
                except Exception as e:
                    print(f"❌ Video recording failed: {e}")
                    messagebox.showerror("Error", f"Video recording failed: {e}")
                    self.recording = False
                    self.record_button.configure(text="Start Enhanced Multi-Screen Recording")
                    self.status_var.set("Ready for enhanced multi-screen recording")
                    return
            
            # Start enhanced interaction logging
            if self.mouse_enabled.get() or self.keyboard_enabled.get():
                try:
                    capture_keyboard = self.keyboard_enabled.get() and APPKIT_AVAILABLE
                    
                    success = self.interaction_logger.start_logging(capture_keyboard)
                    if success:
                        components = []
                        if self.mouse_enabled.get():
                            components.append("mouse")
                        if capture_keyboard:
                            components.append("enhanced-keyboard")
                        started_components.append(f"interactions({'+'.join(components)})")
                except Exception as e:
                    print(f"⚠️ Interaction logging failed: {e}")
            
            if started_components:
                selected_monitor = next((m for m in self.monitors if m['info'] == self.monitor_var.get()), self.monitors[0])
                print(f"🎬 Enhanced recording started on {selected_monitor['name']}: {', '.join(started_components)}")
                messagebox.showinfo("Recording Started", 
                                  f"Enhanced multi-screen recording started!\n\nMonitor: {selected_monitor['name']}\nComponents: {', '.join(started_components)}\n\n✨ Recording area is highlighted!\n🔑 Enhanced keyboard logging active!")
            else:
                self.recording = False
                self.record_button.configure(text="Start Enhanced Multi-Screen Recording")
                self.status_var.set("Ready for enhanced multi-screen recording")
                messagebox.showerror("Error", "No recording components could be started")
            
        except Exception as e:
            print(f"❌ Recording start failed: {e}")
            messagebox.showerror("Error", f"Failed to start recording: {e}")
            self.recording = False
            self.record_button.configure(text="Start Enhanced Multi-Screen Recording")
            self.status_var.set("Ready for enhanced multi-screen recording")
    
    def stop_recording(self):
        """Stop enhanced multi-screen recording"""
        try:
            if not self.recording:
                return
            
            self.recording = False
            self.record_button.configure(text="Start Enhanced Multi-Screen Recording")
            self.status_var.set("⏳ Saving enhanced data...")
            
            stopped_components = []
            
            # Stop video recording
            try:
                self.video_recorder.stop_recording()
                stopped_components.append("video+audio-integrated")
            except Exception as e:
                print(f"⚠️ Error stopping video: {e}")
            
            # Stop interaction logging and save
            try:
                self.interaction_logger.stop_logging()
                if len(self.interaction_logger.interactions) > 0 or len(self.interaction_logger.keyboard_logger.keyboard_events) > 0:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    interaction_path = Path(self.output_directory) / f"enhanced_multiscreen_interactions_{timestamp}.json"
                    success = self.interaction_logger.save_interactions(str(interaction_path))
                    if success:
                        stopped_components.append("enhanced-interactions")
            except Exception as e:
                print(f"⚠️ Error saving interactions: {e}")
            
            self.status_var.set("✅ Enhanced recording saved!")
            print(f"🛑 Enhanced multi-screen recording completed: {', '.join(stopped_components)}")
            messagebox.showinfo("Recording Complete", 
                              f"Enhanced multi-screen recording saved!\n\nComponents: {', '.join(stopped_components)}\n\n✅ Fixed video frame writing\n🔑 Enhanced keyboard logging\n🎵 Audio integration\n✨ Visual feedback")
            
        except Exception as e:
            print(f"❌ Error stopping recording: {e}")
            self.status_var.set("❌ Error during stop")
            messagebox.showerror("Error", f"Error stopping recording: {e}")
    
    def open_output_folder(self):
        """Open output folder"""
        try:
            if PLATFORM == "Darwin":
                os.system(f'open "{self.output_directory}"')
            elif PLATFORM == "Windows":
                os.system(f'explorer "{self.output_directory}"')
            else:
                os.system(f'xdg-open "{self.output_directory}"')
        except Exception as e:
            print(f"Error opening folder: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        try:
            if self.recording:
                if messagebox.askokcancel("Quit", "Enhanced recording in progress. Stop and quit?"):
                    self.stop_recording()
                    time.sleep(2)
                    self.root.destroy()
            else:
                self.root.destroy()
        except Exception as e:
            print(f"Error during closing: {e}")
            self.root.destroy()
    
    def run(self):
        """Run enhanced application"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"GUI error: {e}")

def main():
    """Main entry point"""
    print("🚀 Starting Enhanced RPA Recorder (MULTI-SCREEN FIXED EDITION)...")
    print(f"Platform: {PLATFORM}")
    print(f"Audio Recording: {'✅' if AUDIO_AVAILABLE else '❌'}")
    print(f"Enhanced Keyboard: {'✅' if APPKIT_AVAILABLE else '❌'}")
    print(f"UI Tree Capture: {'✅' if ACCESSIBILITY_AVAILABLE else '❌'}")
    print()
    print("🔧 FIXES IN THIS VERSION:")
    print("   • ✅ Fixed video frame writing issues")
    print("   • ✅ Enhanced keyboard logging with Core Graphics")
    print("   • ✅ Visual recording area highlight")
    print("   • ✅ Improved error handling and validation")
    print("   • ✅ Better codec fallbacks")
    print("   • ✅ FIXED AUDIO/VIDEO SYNC ISSUES:")
    print("     - Synchronized thread startup")
    print("     - Precise frame timing")
    print("     - Enhanced ffmpeg combination")
    print("     - Duration analysis and debugging")
    print()
    print("📺 MULTI-SCREEN FEATURES:")
    print("   • Record any specific monitor/screen")
    print("   • Visual highlight shows recording area")
    print("   • Preview recording area before starting")
    print("   • Automatic audio/video integration")
    print()
    print("⌨️ ENHANCED KEYBOARD LOGGING:")
    print("   • Core Graphics event tap for every keystroke")
    print("   • Real-time key press monitoring")
    print("   • Modifier key combinations")
    print("   • Clipboard and app switching detection")
    print("   • Typing session analysis")
    
    if not AUDIO_AVAILABLE:
        print("⚠️ Install pyaudio for audio recording: pip install pyaudio")
    
    # Check for ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        print("✅ ffmpeg found - audio/video integration available")
    except:
        print("⚠️ ffmpeg not found - install for automatic audio/video combination")
        print("💡 On macOS: brew install ffmpeg")
    
    print()
    print("🎯 Perfect for multi-monitor workflows with complete keystroke visibility!")
    
    try:
        app = MultiScreenRPARecorderApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Enhanced Multi-Screen RPA Recorder stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()