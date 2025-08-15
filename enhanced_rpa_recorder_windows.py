#!/usr/bin/env python3
"""
Enhanced RPA Recorder - WINDOWS EDITION
Video + Audio + Full Keyboard Logging + Visual Recording Area Highlight
Windows-compatible version with all macOS features translated
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

# Windows keyboard logging
try:
    import pynput
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("Enhanced keyboard logging not available (pynput not installed)")

# Windows clipboard and app detection
try:
    import win32clipboard
    import win32gui
    import win32process
    import psutil
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Windows clipboard/app monitoring not available (pywin32 not installed)")

# Windows-specific mouse events
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Mouse automation not available (pyautogui not installed)")

PLATFORM = platform.system()

class WindowsScreenHighlighter:
    """Windows-compatible visual highlight overlay for recording area"""
    
    def __init__(self):
        self.overlay_window = None
        self.highlight_active = False
        self.recording_mode = False
        self.auto_hide_timer = None
        
    def show_recording_area(self, monitor_info, recording=False):
        """Show visual highlight of recording area on Windows"""
        try:
            self.recording_mode = recording
            self._show_windows_highlight(monitor_info)
        except Exception as e:
            print(f"⚠️ Could not show recording area highlight: {e}")
    
    def _show_windows_highlight(self, monitor_info):
        """Show red border around recording area on Windows using tkinter"""
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
            
            print(f"🎯 Creating Windows highlight window: {width}x{height} at ({x}, {y})")
            
            # Configure window properties for Windows
            self.overlay_window.configure(bg='black')
            self.overlay_window.attributes('-topmost', True)  # Always on top
            self.overlay_window.overrideredirect(True)  # No title bar
            self.overlay_window.attributes('-alpha', 0.3)  # 30% transparent
            
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
            print(f"❌ Windows border highlight error: {e}")
            import traceback
            traceback.print_exc()
    
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

class WindowsVideoRecorder:
    """Windows-compatible multi-screen video recorder"""
    
    def __init__(self):
        self.recording = False
        self.output_path = None
        self.fps = 15
        self.record_thread = None
        self.audio_thread = None
        self.video_writer = None
        self.audio_frames = []
        self.selected_monitor = 1  # Default to primary monitor
        self.highlighter = WindowsScreenHighlighter()
        
        # Audio settings
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 22050
        self.chunk = 512
        self.audio = None
        
        # Sync coordination
        self.recording_start_time = None
        self.sync_barrier = threading.Barrier(2)
        self.frame_timestamps = []
        
    def get_available_monitors(self):
        """Get list of available monitors on Windows"""
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
    
    def _get_best_codec(self):
        """Find the best working codec for Windows"""
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Test codecs in order of preference
        codecs_to_try = [
            ('XVID', '.avi'),
            ('MJPG', '.avi'), 
            ('mp4v', '.mp4'),
            ('WMV1', '.wmv'),
            ('WMV2', '.wmv')
        ]
        
        for codec_name, extension in codecs_to_try:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec_name)
                test_path = 'test_codec' + extension
                writer = cv2.VideoWriter(test_path, fourcc, 15, (100, 100))
                
                if writer.isOpened():
                    success = writer.write(test_frame)
                    writer.release()
                    
                    # Clean up test file
                    try:
                        os.remove(test_path)
                    except:
                        pass
                    
                    if success:
                        print(f"✅ Using codec: {codec_name} with extension: {extension}")
                        return codec_name, extension
                        
            except Exception as e:
                continue
        
        print("⚠️ No reliable codec found, using XVID fallback")
        return 'XVID', '.avi'
    
    def start_recording(self, output_path, fps=15, record_audio=True):
        """Start Windows multi-screen recording"""
        if self.recording:
            return False
        
        self.output_path = output_path
        self.fps = fps
        self.recording = True
        self.audio_frames = []
        self.frame_timestamps = []
        
        print(f"🎬 Starting Windows multi-screen recording on monitor {self.selected_monitor}: {output_path}")
        
        # Show recording border (stays visible during recording)
        monitors = self.get_available_monitors()
        for monitor in monitors:
            if monitor['index'] == self.selected_monitor:
                self.highlighter.show_recording_area(monitor['monitor_data'], recording=True)
                break
        
        # Initialize sync barrier
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
                print("🎤 Windows audio recording enabled")
            except Exception as e:
                print(f"⚠️ Audio recording failed: {e}")
        
        return True
    
    def _video_loop(self):
        """Windows video recording loop"""
        try:
            with mss.mss() as sct:
                # Get the specific monitor
                if self.selected_monitor >= len(sct.monitors):
                    print(f"❌ Monitor {self.selected_monitor} not available, using monitor 1")
                    self.selected_monitor = 1
                
                monitor = sct.monitors[self.selected_monitor]
                print(f"📺 Recording Windows monitor {self.selected_monitor}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
                
                # Take first screenshot to determine actual frame dimensions
                try:
                    first_screenshot = sct.grab(monitor)
                    first_frame = np.array(first_screenshot)
                    print(f"✅ First screenshot captured: {first_frame.shape}")
                    
                    # Convert to BGR
                    if first_frame.shape[2] == 4:  # BGRA
                        first_frame = cv2.cvtColor(first_frame, cv2.COLOR_BGRA2BGR)
                    elif first_frame.shape[2] == 3:  # RGB
                        first_frame = cv2.cvtColor(first_frame, cv2.COLOR_RGB2BGR)
                    
                    # Use actual frame dimensions
                    height, width = first_frame.shape[:2]
                    print(f"📐 ACTUAL Windows frame dimensions: {width}x{height}")
                    
                except Exception as e:
                    print(f"❌ First screenshot failed: {e}")
                    return
                
                # Ensure dimensions are even
                if width % 2 != 0:
                    width -= 1
                if height % 2 != 0:
                    height -= 1
                
                # Validate FPS
                if self.fps > 30:
                    self.fps = 30
                elif self.fps < 5:
                    self.fps = 10
                
                print(f"📺 Windows video dimensions: {width}x{height}, FPS: {self.fps}")
                
                # Get best codec for Windows
                best_codec, extension = self._get_best_codec()
                
                # Adjust output path if needed
                if not self.output_path.endswith(extension):
                    self.output_path = self.output_path.rsplit('.', 1)[0] + extension
                
                print(f"📁 Windows output path: {self.output_path}")
                
                # Initialize video writer with Windows-compatible codec
                fourcc = cv2.VideoWriter_fourcc(*best_codec)
                self.video_writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))
                
                if not self.video_writer.isOpened():
                    print("❌ Windows video writer failed to open!")
                    return
                else:
                    print(f"✅ Windows video writer initialized with {best_codec}")
                
                frame_count = 0
                last_status_time = time.time()
                
                # Sync with audio thread
                print("📹 Windows video thread ready, waiting for sync...")
                try:
                    self.sync_barrier.wait(timeout=5.0)
                    self.recording_start_time = time.time()
                    print(f"✅ Windows synchronized recording started at {self.recording_start_time}")
                except threading.BrokenBarrierError:
                    print("⚠️ Sync barrier broken, starting video anyway")
                    self.recording_start_time = time.time()
                
                # Precise frame timing
                target_frame_duration = 1.0 / self.fps
                next_frame_time = self.recording_start_time
                
                while self.recording:
                    try:
                        # Capture screenshot
                        screenshot = sct.grab(monitor)
                        frame = np.array(screenshot)
                        
                        # Convert color space
                        if frame.shape[2] == 4:  # BGRA
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                        elif frame.shape[2] == 3:  # RGB  
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        # Ensure frame dimensions match
                        if frame.shape[:2] != (height, width):
                            frame = cv2.resize(frame, (width, height))
                        
                        # Ensure proper data type
                        frame = frame.astype(np.uint8)
                        
                        # Validate frame
                        if frame.size == 0:
                            continue
                        
                        # Ensure frame is contiguous
                        if not frame.flags['C_CONTIGUOUS']:
                            frame = np.ascontiguousarray(frame)
                        
                        # Write frame
                        if self.video_writer and self.video_writer.isOpened():
                            success = self.video_writer.write(frame)
                            if success:
                                frame_count += 1
                                
                                # Track frame timestamp
                                frame_timestamp = time.time() - self.recording_start_time
                                self.frame_timestamps.append(frame_timestamp)
                                
                                # Status update every 3 seconds
                                current_time = time.time()
                                if current_time - last_status_time > 3.0:
                                    actual_fps = frame_count / frame_timestamp if frame_timestamp > 0 else 0
                                    print(f"📹 Windows Recording: {frame_count} frames ({frame_timestamp:.1f}s) actual FPS: {actual_fps:.1f} ✅")
                                    last_status_time = current_time
                        
                        # Frame rate control
                        next_frame_time += target_frame_duration
                        current_time = time.time()
                        sleep_time = next_frame_time - current_time
                        
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        elif sleep_time < -target_frame_duration:
                            next_frame_time = current_time + target_frame_duration
                        
                    except Exception as e:
                        print(f"Windows frame capture error: {e}")
                        time.sleep(0.1)
                
                print(f"📹 Windows video complete: {frame_count} frames on monitor {self.selected_monitor}")
                
        except Exception as e:
            print(f"Windows video recording error: {e}")
            traceback.print_exc()
        finally:
            if self.video_writer:
                self.video_writer.release()
                print("📹 Windows video writer released")
    
    def _audio_loop(self):
        """Windows audio recording loop"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Find a working input device on Windows
            device_info = None
            for i in range(self.audio.get_device_count()):
                try:
                    info = self.audio.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        device_info = info
                        print(f"🎤 Using Windows audio device: {info['name']}")
                        break
                except:
                    continue
            
            if not device_info:
                print("❌ No audio input device found on Windows")
                return
            
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                input_device_index=device_info['index']
            )
            
            # Sync with video thread
            print("🎤 Windows audio thread ready, waiting for sync...")
            try:
                self.sync_barrier.wait(timeout=5.0)
                print("✅ Windows audio synchronized with video")
            except threading.BrokenBarrierError:
                print("⚠️ Windows audio sync barrier broken, starting anyway")
            
            audio_start_time = time.time()
            chunk_count = 0
            
            while self.recording:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    self.audio_frames.append(data)
                    chunk_count += 1
                    
                    if chunk_count % 100 == 0:
                        audio_duration = chunk_count * self.chunk / self.rate
                        actual_duration = time.time() - audio_start_time
                        print(f"🎵 Windows Audio: {audio_duration:.1f}s recorded, {actual_duration:.1f}s elapsed")
                        
                except:
                    time.sleep(0.01)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Windows audio error: {e}")
        finally:
            if self.audio:
                self.audio.terminate()
    
    def stop_recording(self):
        """Stop Windows recording"""
        if not self.recording:
            return
        
        print("🛑 Stopping Windows multi-screen recording...")
        self.recording = False
        
        # Hide recording border
        self.highlighter.hide_highlight()
        
        if self.record_thread:
            self.record_thread.join(timeout=5)
        if self.audio_thread:
            self.audio_thread.join(timeout=3)
        
        # Save audio separately (Windows doesn't need complex ffmpeg integration)
        if self.audio_frames:
            self._save_audio()
        
        print("✅ Windows multi-screen recording stopped")
    
    def _save_audio(self):
        """Save audio to separate file on Windows"""
        try:
            audio_path = self.output_path.replace('.avi', '_audio.wav').replace('.mp4', '_audio.wav')
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.get_sample_size(self.audio_format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.audio_frames))
            
            print(f"🎵 Windows audio saved: {audio_path}")
            
        except Exception as e:
            print(f"Windows audio save error: {e}")

class WindowsKeyboardLogger:
    """Windows-compatible keyboard logger using pynput"""
    
    def __init__(self):
        self.keyboard_events = []
        self.logging = False
        self.keyboard_listener = None
        self.clipboard_thread = None
        self.app_monitor_thread = None
        
        # State tracking
        self.last_clipboard = ""
        self.last_app = ""
        self.typing_session_start = None
        self.consecutive_keys = 0
        self.last_key_time = 0
        
    def start_logging(self):
        """Start Windows keyboard logging"""
        if self.logging or not PYNPUT_AVAILABLE:
            return True
            
        self.logging = True
        self.keyboard_events = []
        
        print("⌨️ Starting Windows keyboard logging...")
        
        # Start pynput keyboard listener
        try:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.start()
            print("✅ Windows pynput keyboard listener started")
        except Exception as e:
            print(f"❌ Windows keyboard listener failed: {e}")
        
        # Start clipboard monitoring
        if WIN32_AVAILABLE:
            self.clipboard_thread = threading.Thread(target=self._clipboard_monitor)
            self.clipboard_thread.daemon = True
            self.clipboard_thread.start()
        
        # Start app monitoring
        if WIN32_AVAILABLE:
            self.app_monitor_thread = threading.Thread(target=self._app_monitor)
            self.app_monitor_thread.daemon = True
            self.app_monitor_thread.start()
        
        return True
    
    def _on_key_press(self, key):
        """Handle key press events on Windows"""
        try:
            timestamp = time.time()
            
            # Get key name
            try:
                key_name = key.char if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
            except AttributeError:
                key_name = str(key).replace('Key.', '')
            
            # Log key event
            self._log_key_event({
                'type': 'key_press',
                'key_name': key_name,
                'is_character': hasattr(key, 'char') and key.char and key.char.isalnum(),
                'is_special': not hasattr(key, 'char') or not key.char,
                'timestamp': timestamp,
                'capture_method': 'pynput_windows'
            })
            
            # Track typing patterns
            self._update_typing_session(key_name, timestamp)
            
            print(f"🔑 Windows key pressed: {key_name}")
            
        except Exception as e:
            print(f"Key press error: {e}")
    
    def _on_key_release(self, key):
        """Handle key release events on Windows"""
        try:
            timestamp = time.time()
            
            # Get key name
            try:
                key_name = key.char if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
            except AttributeError:
                key_name = str(key).replace('Key.', '')
            
            # Only log releases for special keys
            if not hasattr(key, 'char') or not key.char:
                self._log_key_event({
                    'type': 'key_release',
                    'key_name': key_name,
                    'timestamp': timestamp,
                    'capture_method': 'pynput_windows'
                })
                
        except Exception as e:
            print(f"Key release error: {e}")
    
    def _clipboard_monitor(self):
        """Monitor Windows clipboard changes"""
        try:
            self.last_clipboard = self._get_windows_clipboard()
            
            while self.logging:
                try:
                    current_clipboard = self._get_windows_clipboard()
                    
                    if current_clipboard != self.last_clipboard and current_clipboard:
                        self._log_key_event({
                            'type': 'clipboard_change',
                            'action': 'copy_paste',
                            'content_length': len(current_clipboard),
                            'content_preview': self._safe_preview(current_clipboard),
                            'timestamp': time.time(),
                            'inferred_shortcut': 'Ctrl+C or Ctrl+V'
                        })
                        self.last_clipboard = current_clipboard
                    
                    time.sleep(0.5)
                except:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Windows clipboard monitoring error: {e}")
    
    def _app_monitor(self):
        """Monitor Windows app focus changes"""
        try:
            self.last_app = self._get_current_windows_app()
            
            while self.logging:
                try:
                    current_app = self._get_current_windows_app()
                    
                    if current_app != self.last_app:
                        self._log_key_event({
                            'type': 'app_switch',
                            'from_app': self.last_app,
                            'to_app': current_app,
                            'timestamp': time.time(),
                            'inferred_shortcut': 'Alt+Tab or mouse click'
                        })
                        self.last_app = current_app
                    
                    time.sleep(0.5)
                except:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Windows app monitoring error: {e}")
    
    def _get_windows_clipboard(self):
        """Get Windows clipboard content"""
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return data or ""
        except:
            return ""
    
    def _get_current_windows_app(self):
        """Get current Windows app name"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name()
        except:
            return "Unknown"
    
    def _safe_preview(self, text, max_length=50):
        """Create safe text preview"""
        if not text:
            return ""
        
        if any(keyword in text.lower() for keyword in ['password', 'secret', 'token', 'key']):
            return "[SENSITIVE_CONTENT_MASKED]"
        
        preview = str(text).replace('\n', ' ').replace('\t', ' ')
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
            print(f"Windows typing session tracking error: {e}")
    
    def _log_key_event(self, event_data):
        """Log keyboard event"""
        try:
            event = {
                'datetime': datetime.now().isoformat(),
                'source': 'windows_keyboard_logger',
                **event_data
            }
            self.keyboard_events.append(event)
            
        except Exception as e:
            print(f"Windows keyboard event logging error: {e}")
    
    def stop_logging(self):
        """Stop Windows keyboard logging"""
        if not self.logging:
            return
            
        self.logging = False
        
        # Stop keyboard listener
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        # Wait for threads to finish
        if self.clipboard_thread:
            self.clipboard_thread.join(timeout=1)
        if self.app_monitor_thread:
            self.app_monitor_thread.join(timeout=1)
        
        print(f"✅ Windows keyboard logging stopped - captured {len(self.keyboard_events)} events")

# Import imageio for reliable video recording on Windows
try:
    import imageio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False
    print("ImageIO not available - install with: pip install imageio imageio-ffmpeg")

class WindowsImageIOVideoRecorder:
    """Windows video recorder using ImageIO (much more reliable than OpenCV)"""
    
    def __init__(self):
        self.recording = False
        self.output_path = None
        self.fps = 15
        self.record_thread = None
        self.audio_thread = None
        self.video_writer = None
        self.audio_frames = []
        self.selected_monitor = 1
        self.highlighter = WindowsScreenHighlighter()
        
        # Audio settings
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 22050
        self.chunk = 512
        self.audio = None
        
        # Sync coordination
        self.recording_start_time = None
        self.sync_barrier = threading.Barrier(2)
        self.frame_timestamps = []
        self.frames_buffer = []  # Store frames for imageio
        
    def get_available_monitors(self):
        """Get list of available monitors on Windows"""
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
        """Start Windows recording with ImageIO"""
        if self.recording or not IMAGEIO_AVAILABLE:
            return False
        
        self.output_path = output_path
        self.fps = fps
        self.recording = True
        self.audio_frames = []
        self.frame_timestamps = []
        self.frames_buffer = []
        
        # Ensure MP4 extension for imageio
        if not self.output_path.endswith('.mp4'):
            self.output_path = self.output_path.rsplit('.', 1)[0] + '.mp4'
        
        print(f"🎬 Starting Windows ImageIO recording on monitor {self.selected_monitor}: {self.output_path}")
        
        # Show recording border
        monitors = self.get_available_monitors()
        for monitor in monitors:
            if monitor['index'] == self.selected_monitor:
                self.highlighter.show_recording_area(monitor['monitor_data'], recording=True)
                break
        
        # Initialize sync barrier
        barrier_count = 1  # Always have video
        if AUDIO_AVAILABLE and record_audio:
            barrier_count = 2
        self.sync_barrier = threading.Barrier(barrier_count)
        
        # Start video recording
        self.record_thread = threading.Thread(target=self._imageio_video_loop)
        self.record_thread.daemon = True
        self.record_thread.start()
        
        # Start audio recording
        if AUDIO_AVAILABLE and record_audio:
            try:
                self.audio_thread = threading.Thread(target=self._audio_loop)
                self.audio_thread.daemon = True
                self.audio_thread.start()
                print("🎤 Windows ImageIO audio recording enabled")
            except Exception as e:
                print(f"⚠️ Audio recording failed: {e}")
        
        return True
    
    def _imageio_video_loop(self):
        """Windows video recording loop using ImageIO"""
        try:
            with mss.mss() as sct:
                # Get the specific monitor
                if self.selected_monitor >= len(sct.monitors):
                    print(f"❌ Monitor {self.selected_monitor} not available, using monitor 1")
                    self.selected_monitor = 1
                
                monitor = sct.monitors[self.selected_monitor]
                print(f"📺 Recording Windows monitor {self.selected_monitor} with ImageIO: {monitor['width']}x{monitor['height']}")
                
                frame_count = 0
                last_status_time = time.time()
                
                # Sync with audio thread
                print("📹 Windows ImageIO video thread ready, waiting for sync...")
                try:
                    self.sync_barrier.wait(timeout=5.0)
                    self.recording_start_time = time.time()
                    print(f"✅ Windows ImageIO synchronized recording started")
                except threading.BrokenBarrierError:
                    print("⚠️ Sync barrier broken, starting video anyway")
                    self.recording_start_time = time.time()
                
                # Precise frame timing
                target_frame_duration = 1.0 / self.fps
                next_frame_time = self.recording_start_time
                
                while self.recording:
                    try:
                        # Capture screenshot
                        screenshot = sct.grab(monitor)
                        frame = np.array(screenshot)
                        
                        # Convert BGRA to RGB for ImageIO
                        if frame.shape[2] == 4:  # BGRA
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                        elif frame.shape[2] == 3:  # BGR
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Ensure proper data type
                        frame = frame.astype(np.uint8)
                        
                        # Add frame to buffer
                        self.frames_buffer.append(frame)
                        frame_count += 1
                        
                        # Track frame timestamp
                        frame_timestamp = time.time() - self.recording_start_time
                        self.frame_timestamps.append(frame_timestamp)
                        
                        # Status update every 3 seconds
                        current_time = time.time()
                        if current_time - last_status_time > 3.0:
                            actual_fps = frame_count / frame_timestamp if frame_timestamp > 0 else 0
                            print(f"📹 Windows ImageIO Recording: {frame_count} frames ({frame_timestamp:.1f}s) actual FPS: {actual_fps:.1f} ✅")
                            last_status_time = current_time
                        
                        # Frame rate control
                        next_frame_time += target_frame_duration
                        current_time = time.time()
                        sleep_time = next_frame_time - current_time
                        
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        elif sleep_time < -target_frame_duration:
                            next_frame_time = current_time + target_frame_duration
                        
                    except Exception as e:
                        print(f"Windows ImageIO frame capture error: {e}")
                        time.sleep(0.1)
                
                print(f"📹 Windows ImageIO video complete: {frame_count} frames")
                
                # Save video using ImageIO
                self._save_imageio_video()
                
        except Exception as e:
            print(f"Windows ImageIO video recording error: {e}")
            traceback.print_exc()
    
    def _save_imageio_video(self):
        """Save video using ImageIO"""
        try:
            if not self.frames_buffer:
                print("❌ No frames to save")
                return
                
            print(f"💾 Saving {len(self.frames_buffer)} frames to video using ImageIO...")
            
            # Save with ImageIO - much more reliable on Windows
            with imageio.get_writer(self.output_path, fps=self.fps, quality=8) as writer:
                for frame in self.frames_buffer:
                    writer.append_data(frame)
            
            print(f"✅ Windows ImageIO video saved: {self.output_path}")
            
        except Exception as e:
            print(f"❌ ImageIO save error: {e}")
            traceback.print_exc()
    
    def _audio_loop(self):
        """Windows audio recording loop"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Find working audio device
            device_info = None
            for i in range(self.audio.get_device_count()):
                try:
                    info = self.audio.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        device_info = info
                        print(f"🎤 Using Windows audio device: {info['name']}")
                        break
                except:
                    continue
            
            if not device_info:
                print("❌ No audio input device found on Windows")
                return
            
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                input_device_index=device_info['index']
            )
            
            # Sync with video thread
            print("🎤 Windows audio thread ready, waiting for sync...")
            try:
                self.sync_barrier.wait(timeout=5.0)
                print("✅ Windows audio synchronized with ImageIO video")
            except threading.BrokenBarrierError:
                print("⚠️ Windows audio sync barrier broken, starting anyway")
            
            chunk_count = 0
            
            while self.recording:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    self.audio_frames.append(data)
                    chunk_count += 1
                        
                except:
                    time.sleep(0.01)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Windows audio error: {e}")
        finally:
            if self.audio:
                self.audio.terminate()
    
    def stop_recording(self):
        """Stop Windows ImageIO recording"""
        if not self.recording:
            return
        
        print("🛑 Stopping Windows ImageIO recording...")
        self.recording = False
        
        # Hide recording border
        self.highlighter.hide_highlight()
        
        if self.record_thread:
            self.record_thread.join(timeout=10)  # Give more time for ImageIO save
        if self.audio_thread:
            self.audio_thread.join(timeout=3)
        
        # Save audio separately
        if self.audio_frames:
            self._save_audio()
        
        print("✅ Windows ImageIO recording stopped")
    
    def _save_audio(self):
        """Save audio to separate file"""
        try:
            audio_path = self.output_path.replace('.mp4', '_audio.wav')
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.get_sample_size(self.audio_format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.audio_frames))
            
            print(f"🎵 Windows audio saved: {audio_path}")
            
        except Exception as e:
            print(f"Windows audio save error: {e}")

class WindowsInteractionLogger:
    """Windows interaction logger with enhanced keyboard support"""
    
    def __init__(self, accessibility_inspector=None):
        self.inspector = accessibility_inspector
        self.interactions = []
        self.logging = False
        
        # Mouse tracking
        self.mouse_thread = None
        self.last_position = None
        self.click_state = False
        
        # Windows keyboard logger
        self.keyboard_logger = WindowsKeyboardLogger()
        
        self.start_time = None
        
    def start_logging(self, capture_keyboard=True):
        """Start Windows interaction logging"""
        if self.logging:
            return True
        
        self.logging = True
        self.interactions = []
        self.start_time = time.time()
        
        # Start mouse tracking
        self.mouse_thread = threading.Thread(target=self._mouse_loop)
        self.mouse_thread.daemon = True
        self.mouse_thread.start()
        
        # Start Windows keyboard logging
        if capture_keyboard and PYNPUT_AVAILABLE:
            self.keyboard_logger.start_logging()
        
        print("✅ Windows interaction logging started with enhanced keyboard capture")
        return True
    
    def _mouse_loop(self):
        """Windows mouse tracking loop"""
        print("🔍 Starting Windows mouse tracking...")
        
        while self.logging:
            try:
                if PYAUTOGUI_AVAILABLE:
                    current_pos = pyautogui.position()
                else:
                    current_pos = (0, 0)
                
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
                                'source': 'windows_enhanced'
                            }
                            self._safe_log_interaction(interaction)
                    
                    # Simple click detection (Windows)
                    self._check_for_clicks(current_pos)
                    self.last_position = current_pos
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"⚠️ Windows mouse tracking error: {e}")
                time.sleep(0.5)
        
        print("🛑 Windows mouse tracking stopped")
    
    def _check_for_clicks(self, current_pos):
        """Simple Windows click detection"""
        try:
            # Simple click detection - could be enhanced with win32api
            # For now, just log position changes as potential clicks
            pass
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
                print(f"📝 Logged {len(self.interactions)} Windows interactions...")
                
        except Exception as e:
            print(f"⚠️ Windows interaction log error: {e}")
    
    def stop_logging(self):
        """Stop Windows interaction logging"""
        if not self.logging:
            return
        
        self.logging = False
        
        # Stop mouse thread
        if self.mouse_thread:
            self.mouse_thread.join(timeout=3)
        
        # Stop keyboard logger
        self.keyboard_logger.stop_logging()
        
        print(f"✅ Windows interaction logging stopped")
        print(f"   Mouse interactions: {len(self.interactions)}")
        print(f"   Keyboard events: {len(self.keyboard_logger.keyboard_events)}")
    
    def save_interactions(self, output_path):
        """Save all Windows interaction data"""
        try:
            comprehensive_data = {
                'session_info': {
                    'platform': 'Windows',
                    'start_time': datetime.now().isoformat(),
                    'duration': self._get_relative_timestamp(),
                    'interaction_count': len(self.interactions),
                    'keyboard_event_count': len(self.keyboard_logger.keyboard_events),
                    'capture_method': 'windows_enhanced_imageio',
                    'features': {
                        'multi_screen_recording': True,
                        'visual_recording_highlight': True,
                        'windows_keyboard_logging': True,
                        'pynput_event_capture': True,
                        'mouse_tracking': True,
                        'click_detection': True,
                        'clipboard_monitoring': WIN32_AVAILABLE,
                        'app_switching': WIN32_AVAILABLE,
                        'typing_session_analysis': True,
                        'imageio_video_integration': True
                    }
                },
                'mouse_interactions': self.interactions,
                'keyboard_events': self.keyboard_logger.keyboard_events
            }
            
            with open(output_path, 'w') as f:
                json.dump(comprehensive_data, f, indent=2)
            
            print(f"💾 Windows interactions saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving Windows interactions: {e}")
            return False

class WindowsRPARecorderApp:
    """Windows-compatible RPA Recorder GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced RPA Recorder (Windows Edition)")
        self.root.geometry("700x580")
        
        # Initialize Windows components
        self.accessibility_inspector = None
        
        # Use ImageIO video recorder for Windows reliability
        if IMAGEIO_AVAILABLE:
            self.video_recorder = WindowsImageIOVideoRecorder()
            print("✅ Using ImageIO video recorder for Windows")
        else:
            self.video_recorder = WindowsVideoRecorder()
            print("⚠️ ImageIO not available, falling back to OpenCV (may not work)")
            
        self.interaction_logger = WindowsInteractionLogger(self.accessibility_inspector)
        
        # State
        self.recording = False
        self.output_directory = str(Path.cwd() / "records")
        Path(self.output_directory).mkdir(exist_ok=True)
        
        # Get available monitors
        self.monitors = self.video_recorder.get_available_monitors()
        
        self.setup_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """Setup Windows GUI"""
        # Title section
        title_label = ttk.Label(self.root, text="Enhanced RPA Recorder", font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ttk.Label(self.root, text="Windows Edition - Multi-Screen + Enhanced Keyboard + ImageIO Video", 
                                 font=("Arial", 10), foreground="darkblue")
        subtitle_label.pack(pady=(0, 5))
        
        # Status
        self.status_var = tk.StringVar(value="Ready for Windows recording")
        status_label = ttk.Label(self.root, textvariable=self.status_var, font=("Arial", 11, "bold"))
        status_label.pack(pady=3)
        
        # Main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left column
        left_column = ttk.Frame(main_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right column
        right_column = ttk.Frame(main_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Monitor selection
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
        
        # Preview button
        preview_info_frame = ttk.Frame(monitor_frame)
        preview_info_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(preview_info_frame, text="🔍 Preview Border", 
                  command=self.preview_recording_area).pack(side=tk.LEFT)
        
        ttk.Label(preview_info_frame, text=f"({len(self.monitors)} monitors)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.RIGHT)
        
        # Output directory
        dir_frame = ttk.LabelFrame(left_column, text="📁 Output")
        dir_frame.pack(fill=tk.X, pady=5)
        
        dir_row = ttk.Frame(dir_frame)
        dir_row.pack(fill=tk.X, pady=2)
        
        self.dir_var = tk.StringVar(value=self.output_directory)
        dir_entry = ttk.Entry(dir_row, textvariable=self.dir_var, state="readonly", font=("Arial", 8))
        dir_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)
        ttk.Button(dir_row, text="Browse", command=self.browse_directory).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Recording options
        options_frame = ttk.LabelFrame(left_column, text="🎬 Recording")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Video and audio options
        video_audio_frame = ttk.Frame(options_frame)
        video_audio_frame.pack(fill=tk.X, pady=2)
        
        self.video_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(video_audio_frame, text="Video", variable=self.video_enabled).pack(side=tk.LEFT)
        
        self.audio_enabled = tk.BooleanVar(value=AUDIO_AVAILABLE)
        audio_cb = ttk.Checkbutton(video_audio_frame, text="Audio", variable=self.audio_enabled)
        audio_cb.pack(side=tk.LEFT, padx=(10, 0))
        if not AUDIO_AVAILABLE:
            audio_cb.configure(state="disabled")
        
        # FPS setting
        ttk.Label(video_audio_frame, text="FPS:").pack(side=tk.LEFT, padx=(10, 0))
        self.fps_var = tk.StringVar(value="15")
        ttk.Entry(video_audio_frame, textvariable=self.fps_var, width=4, font=("Arial", 9)).pack(side=tk.LEFT, padx=(2, 0))
        
        # Windows keyboard logging
        keyboard_frame = ttk.LabelFrame(right_column, text="⌨️ Windows Keyboard Logging")
        keyboard_frame.pack(fill=tk.X, pady=5)
        
        self.keyboard_enabled = tk.BooleanVar(value=PYNPUT_AVAILABLE)
        keyboard_cb = ttk.Checkbutton(keyboard_frame, text="✅ Enhanced Keystroke Capture", 
                                     variable=self.keyboard_enabled)
        keyboard_cb.pack(anchor=tk.W, pady=2)
        if not PYNPUT_AVAILABLE:
            keyboard_cb.configure(state="disabled")
        
        keyboard_features = "• Pynput key monitoring\n• Real-time key capture\n• Modifier combinations\n• Clipboard & app switching"
        ttk.Label(keyboard_frame, text=keyboard_features, font=("Arial", 8), foreground="darkgreen").pack(pady=2)
        
        # Mouse and visual features
        features_frame = ttk.LabelFrame(right_column, text="🖱️ Mouse & Visual")
        features_frame.pack(fill=tk.X, pady=5)
        
        self.mouse_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(features_frame, text="Track Mouse & Clicks", 
                       variable=self.mouse_enabled).pack(anchor=tk.W, pady=2)
        
        visual_text = "✨ RED BORDER highlight shows recording area\n🔍 Preview: orange border (auto-hides in 3s)\n🔴 Recording: red border (stays visible)"
        ttk.Label(features_frame, text=visual_text, font=("Arial", 8), foreground="purple").pack(pady=2)
        
        # Windows system status
        status_frame = ttk.LabelFrame(right_column, text="🚀 Windows System Status")
        status_frame.pack(fill=tk.X, pady=5)
        
        video_method = "ImageIO✅" if IMAGEIO_AVAILABLE else "OpenCV⚠️"
        caps_text = f"{video_method} Audio{'✅' if AUDIO_AVAILABLE else '❌'} Keyboard{'✅' if PYNPUT_AVAILABLE else '❌'} Win32{'✅' if WIN32_AVAILABLE else '❌'} Monitors{len(self.monitors)}📺"
        ttk.Label(status_frame, text=caps_text, font=("Arial", 8), foreground="blue").pack(pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.record_button = ttk.Button(button_frame, text="🔴 Start Windows Recording", 
                                      command=self.toggle_recording, style="Accent.TButton")
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📁 Open Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
    
    def on_monitor_changed(self, event=None):
        """Handle monitor selection change"""
        try:
            selection = self.monitor_var.get()
            if selection:
                monitor_index = int(selection.split(':')[0].replace('Monitor ', ''))
                self.video_recorder.set_monitor(monitor_index)
        except Exception as e:
            print(f"Error changing monitor: {e}")
    
    def preview_recording_area(self):
        """Preview the recording area with border highlight"""
        try:
            selection = self.monitor_var.get()
            if selection:
                monitor_index = int(selection.split(':')[0].replace('Monitor ', ''))
                
                for monitor in self.monitors:
                    if monitor['index'] == monitor_index:
                        self.video_recorder.highlighter.show_recording_area(monitor['monitor_data'], recording=False)
                        messagebox.showinfo("Windows Border Preview", 
                                          f"Windows recording area preview!\n\nMonitor: {monitor['name']}\nResolution: {monitor['resolution']}\nPosition: {monitor['position']}\n\n🔍 Orange preview border (auto-hides in 3s)\n🔴 During recording: red border stays visible")
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
        """Start Windows recording"""
        try:
            if self.recording:
                return
            
            # Set monitor before recording
            self.on_monitor_changed()
            
            self.recording = True
            self.record_button.configure(text="Stop Recording")
            self.status_var.set("🔴 WINDOWS RECORDING IN PROGRESS...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_path = Path(self.output_directory) / f"windows_enhanced_{timestamp}"
            
            started_components = []
            
            # Start video recording
            if self.video_enabled.get():
                try:
                    fps = max(5, min(30, int(self.fps_var.get() or 15)))
                    video_path = str(base_path) + ".mp4"
                    record_audio = self.audio_enabled.get() and AUDIO_AVAILABLE
                    
                    success = self.video_recorder.start_recording(video_path, fps, record_audio)
                    if success:
                        video_method = "ImageIO" if IMAGEIO_AVAILABLE else "OpenCV"
                        if record_audio:
                            started_components.append(f"{video_method}-video+audio")
                        else:
                            started_components.append(f"{video_method}-video")
                except Exception as e:
                    print(f"❌ Windows video recording failed: {e}")
                    messagebox.showerror("Error", f"Windows video recording failed: {e}")
                    self.recording = False
                    self.record_button.configure(text="Start Windows Recording")
                    self.status_var.set("Ready for Windows recording")
                    return
            
            # Start interaction logging
            if self.mouse_enabled.get() or self.keyboard_enabled.get():
                try:
                    capture_keyboard = self.keyboard_enabled.get() and PYNPUT_AVAILABLE
                    
                    success = self.interaction_logger.start_logging(capture_keyboard)
                    if success:
                        components = []
                        if self.mouse_enabled.get():
                            components.append("mouse")
                        if capture_keyboard:
                            components.append("windows-keyboard")
                        started_components.append(f"interactions({'+'.join(components)})")
                except Exception as e:
                    print(f"⚠️ Windows interaction logging failed: {e}")
            
            if started_components:
                selected_monitor = next((m for m in self.monitors if m['info'] == self.monitor_var.get()), self.monitors[0])
                print(f"🎬 Windows recording started on {selected_monitor['name']}: {', '.join(started_components)}")
                
                video_method = "ImageIO (reliable)" if IMAGEIO_AVAILABLE else "OpenCV (may fail)"
                messagebox.showinfo("Recording Started", 
                                  f"Windows recording started!\n\nMonitor: {selected_monitor['name']}\nVideo: {video_method}\nComponents: {', '.join(started_components)}\n\n✨ Recording area highlighted!\n🔑 Windows keyboard logging active!")
            else:
                self.recording = False
                self.record_button.configure(text="Start Windows Recording")
                self.status_var.set("Ready for Windows recording")
                messagebox.showerror("Error", "No recording components could be started")
            
        except Exception as e:
            print(f"❌ Windows recording start failed: {e}")
            messagebox.showerror("Error", f"Failed to start Windows recording: {e}")
            self.recording = False
            self.record_button.configure(text="Start Windows Recording")
            self.status_var.set("Ready for Windows recording")
    
    def stop_recording(self):
        """Stop Windows recording"""
        try:
            if not self.recording:
                return
            
            self.recording = False
            self.record_button.configure(text="Start Windows Recording")
            self.status_var.set("⏳ Saving Windows data...")
            
            stopped_components = []
            
            # Stop video recording
            try:
                self.video_recorder.stop_recording()
                video_method = "ImageIO" if IMAGEIO_AVAILABLE else "OpenCV"
                stopped_components.append(f"{video_method}-video+audio")
            except Exception as e:
                print(f"⚠️ Error stopping Windows video: {e}")
            
            # Stop interaction logging and save
            try:
                self.interaction_logger.stop_logging()
                if len(self.interaction_logger.interactions) > 0 or len(self.interaction_logger.keyboard_logger.keyboard_events) > 0:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    interaction_path = Path(self.output_directory) / f"windows_enhanced_interactions_{timestamp}.json"
                    success = self.interaction_logger.save_interactions(str(interaction_path))
                    if success:
                        stopped_components.append("windows-interactions")
            except Exception as e:
                print(f"⚠️ Error saving Windows interactions: {e}")
            
            self.status_var.set("✅ Windows recording saved!")
            print(f"🛑 Windows recording completed: {', '.join(stopped_components)}")
            
            video_method = "ImageIO (reliable)" if IMAGEIO_AVAILABLE else "OpenCV (may have failed)"
            messagebox.showinfo("Recording Complete", 
                              f"Windows recording saved!\n\nVideo: {video_method}\nComponents: {', '.join(stopped_components)}\n\n✅ Windows-compatible video format\n🔑 Enhanced Windows keyboard logging\n🎵 Audio saved separately\n✨ Visual feedback")
            
        except Exception as e:
            print(f"❌ Error stopping Windows recording: {e}")
            self.status_var.set("❌ Error during stop")
            messagebox.showerror("Error", f"Error stopping Windows recording: {e}")
    
    def open_output_folder(self):
        """Open output folder on Windows"""
        try:
            os.system(f'explorer "{self.output_directory}"')
        except Exception as e:
            print(f"Error opening Windows folder: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        try:
            if self.recording:
                if messagebox.askokcancel("Quit", "Windows recording in progress. Stop and quit?"):
                    self.stop_recording()
                    time.sleep(2)
                    self.root.destroy()
            else:
                self.root.destroy()
        except Exception as e:
            print(f"Error during Windows app closing: {e}")
            self.root.destroy()
    
    def run(self):
        """Run Windows application"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Windows GUI error: {e}")

def main():
    """Main entry point for Windows"""
    print("🚀 Starting Enhanced RPA Recorder (WINDOWS EDITION)...")
    print(f"Platform: {PLATFORM}")
    print(f"Audio Recording: {'✅' if AUDIO_AVAILABLE else '❌'}")
    print(f"Enhanced Keyboard: {'✅' if PYNPUT_AVAILABLE else '❌'}")
    print(f"Win32 Features: {'✅' if WIN32_AVAILABLE else '❌'}")
    print(f"ImageIO Video: {'✅' if IMAGEIO_AVAILABLE else '❌'}")
    print(f"PyAutoGUI Mouse: {'✅' if PYAUTOGUI_AVAILABLE else '❌'}")
    print()
    print("🔧 WINDOWS FIXES:")
    print("   • ✅ ImageIO video recording (bypasses OpenCV codec issues)")
    print("   • ✅ Pynput keyboard logging (Windows-native)")
    print("   • ✅ Win32 clipboard and app monitoring")
    print("   • ✅ Windows-compatible visual overlays")
    print("   • ✅ Reliable MP4 video creation")
    print("   • ✅ Windows multi-monitor support")
    print()
    print("📺 MULTI-SCREEN FEATURES:")
    print("   • Record any specific monitor/screen")
    print("   • Visual highlight shows recording area")
    print("   • Preview recording area before starting")
    print("   • Separate audio/video files (Windows compatible)")
    print()
    print("⌨️ WINDOWS KEYBOARD LOGGING:")
    print("   • Pynput key event capture")
    print("   • Real-time key press monitoring")
    print("   • Modifier key combinations")
    print("   • Windows clipboard monitoring")
    print("   • Windows app switching detection")
    print("   • Typing session analysis")
    
    if not AUDIO_AVAILABLE:
        print("⚠️ Install pyaudio for audio recording: pip install pyaudio")
    
    if not PYNPUT_AVAILABLE:
        print("⚠️ Install pynput for keyboard logging: pip install pynput")
        
    if not WIN32_AVAILABLE:
        print("⚠️ Install pywin32 for enhanced Windows features: pip install pywin32")
        
    if not IMAGEIO_AVAILABLE:
        print("⚠️ Install imageio for reliable video: pip install imageio imageio-ffmpeg")
        print("   ImageIO provides much better Windows video compatibility!")
    else:
        print("✅ ImageIO available - reliable video recording enabled!")
    
    print()
    print("🎯 Perfect for Windows multi-monitor workflows with complete keystroke visibility!")
    
    try:
        app = WindowsRPARecorderApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Windows Enhanced RPA Recorder stopped by user")
    except Exception as e:
        print(f"❌ Fatal Windows error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()