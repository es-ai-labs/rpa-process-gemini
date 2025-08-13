"""
Simple Single-Session RPA Generator

A simplified version for processing individual recording sessions
and generating RPA commands. Good for testing and debugging.
"""

import os
import json
import base64
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from rpa_config import RpaConfig

class SimpleRpaGenerator:
    """Simplified RPA generator for single sessions"""
    
    def __init__(self):
        """Initialize the simple RPA generator"""
        self.api_key = self._load_api_key()
        self.config = RpaConfig()
        
    def _load_api_key(self) -> str:
        """Load API key from environment"""
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment")
        return api_key
    
    def list_available_sessions(self, records_dir: str = "records") -> None:
        """List all available recording sessions"""
        print(f"📁 Available recordings in '{records_dir}':")
        print("-" * 50)
        
        sessions = {}
        for filename in os.listdir(records_dir):
            if filename.endswith('.mp4'):
                base_name = filename.replace('.mp4', '')
                corresponding_json = f"{base_name}_interactions.json"
                json_path = os.path.join(records_dir, corresponding_json)
                
                if os.path.exists(json_path):
                    video_path = os.path.join(records_dir, filename)
                    size_mb = os.path.getsize(video_path) / (1024 * 1024)
                    sessions[base_name] = {
                        'video': video_path,
                        'json': json_path,
                        'size_mb': size_mb
                    }
        
        for i, (session_name, files) in enumerate(sessions.items(), 1):
            status = "✅" if files['size_mb'] <= self.config.MAX_FILE_SIZE_MB else "⚠️ (too large)"
            print(f"{i:2d}. {session_name}")
            print(f"     Video: {files['size_mb']:.1f} MB {status}")
            print(f"     JSON:  {os.path.basename(files['json'])}")
            print()
    
    def load_interaction_summary(self, json_path: str) -> str:
        """Load and create a summary of interactions"""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            session_info = data.get('session_info', {})
            
            # Count different interaction types
            mouse_count = len(data.get('mouse_interactions', []))
            keyboard_count = len(data.get('keyboard_events', []))
            app_switches = len(data.get('app_switches', []))
            
            # Get typing sessions if available
            typing_sessions = data.get('typing_sessions', [])
            typed_text = []
            for session in typing_sessions:
                if session.get('final_text'):
                    typed_text.append(f"'{session['final_text']}'")
            
            summary = []
            summary.append("=== SESSION SUMMARY ===")
            summary.append(f"Duration: {session_info.get('duration', 0):.1f} seconds")
            summary.append(f"Platform: {session_info.get('platform', 'Unknown')}")
            summary.append(f"Mouse actions: {mouse_count}")
            summary.append(f"Keyboard events: {keyboard_count}")
            summary.append(f"App switches: {app_switches}")
            
            if typed_text:
                summary.append(f"Text typed: {', '.join(typed_text[:3])}")
                if len(typed_text) > 3:
                    summary.append(f"... and {len(typed_text) - 3} more text entries")
            
            summary.append("=" * 24)
            
            return "\n".join(summary)
            
        except Exception as e:
            return f"Error loading interaction summary: {e}"
    
    def create_simple_prompt(self, interaction_summary: str) -> str:
        """Create a simplified prompt for RPA generation"""
        
        prompt = f"""You are an expert RPA (Robotic Process Automation) command generator. 

Analyze this recorded user session and generate natural language RPA commands that describe the complete workflow.

{interaction_summary}

TASK: Watch the video and listen to any audio to understand what the user is doing. Then generate step-by-step RPA commands in natural language.

OUTPUT FORMAT: Generate commands following this style:
"Login to [Application] using username [USERNAME] and password [PASSWORD], then click to Login. Then click on the [MENU] and select [OPTION]. Type '[TEXT]' into the [FIELD] and press enter. Click on [BUTTON] to [ACTION]..."

REQUIREMENTS:
1. Be specific about UI elements (button names, field labels, menu items)
2. Include exact text that was typed or selected
3. Mention any wait conditions ("Once on the page...", "When you see...")
4. Handle any popups, dialogs, or error messages
5. Describe the logical flow and decision points
6. End with a clear completion condition
7. Use precise application and UI terminology

Focus on creating commands that another person could follow to replicate the exact same workflow.

Generate ONLY the RPA commands, no additional explanation."""

        return prompt
    
    def process_single_session(self, video_path: str, json_path: str, 
                             output_name: Optional[str] = None) -> Optional[str]:
        """Process a single recording session"""
        
        print(f"🎬 Processing single session:")
        print(f"📹 Video: {os.path.basename(video_path)}")
        print(f"📊 JSON:  {os.path.basename(json_path)}")
        
        # Check file size
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if size_mb > self.config.MAX_FILE_SIZE_MB:
            print(f"❌ Video file too large: {size_mb:.1f} MB (max: {self.config.MAX_FILE_SIZE_MB} MB)")
            return None
        
        print(f"✅ Video size OK: {size_mb:.1f} MB")
        
        # Load interaction summary
        interaction_summary = self.load_interaction_summary(json_path)
        print("📋 Interaction summary loaded")
        
        # Create prompt
        prompt = self.create_simple_prompt(interaction_summary)
        
        # Encode video
        print("🔄 Encoding video to base64...")
        try:
            with open(video_path, 'rb') as f:
                video_bytes = f.read()
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
            print("✅ Video encoded successfully")
        except Exception as e:
            print(f"❌ Error encoding video: {e}")
            return None
        
        # Prepare API request
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "video/mp4",
                                "data": video_base64
                            },
                            "video_metadata": self.config.get_video_metadata()
                        }
                    ]
                }
            ],
            "generationConfig": self.config.get_generation_config()
        }
        
        # Make API request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.GEMINI_MODEL}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        print("🚀 Sending to Gemini API...")
        try:
            response = requests.post(url, headers=headers, json=payload, 
                                   timeout=self.config.API_TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract token usage
                if "usageMetadata" in result:
                    usage = result["usageMetadata"]
                    total_tokens = usage.get('totalTokenCount', 0)
                    estimated_cost = (total_tokens / 1000) * 0.00015
                    print(f"💰 Tokens: {total_tokens}, Cost: ${estimated_cost:.6f}")
                
                # Extract RPA commands
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text_parts = [part.get("text", "") for part in candidate["content"]["parts"]]
                        rpa_commands = "".join(text_parts).strip()
                        
                        # Generate output filename
                        if not output_name:
                            base_name = os.path.splitext(os.path.basename(video_path))[0]
                            output_name = f"{base_name}_rpa_commands.txt"
                        
                        # Save to file
                        output_dir = self.config.ensure_output_dir()
                        output_path = os.path.join(output_dir, output_name)
                        
                        with open(output_path, 'w') as f:
                            f.write(f"# RPA Commands Generated: {datetime.now()}\n")
                            f.write(f"# Source Video: {os.path.basename(video_path)}\n")
                            f.write(f"# Source JSON: {os.path.basename(json_path)}\n\n")
                            f.write(rpa_commands)
                        
                        print(f"✅ RPA commands saved to: {output_path}")
                        print(f"\n📋 Generated Commands Preview:")
                        print("-" * 50)
                        preview = rpa_commands[:300] + "..." if len(rpa_commands) > 300 else rpa_commands
                        print(preview)
                        
                        return rpa_commands
                
            else:
                print(f"❌ API Error: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(json.dumps(error_detail, indent=2))
                except:
                    print(response.text)
                    
        except requests.exceptions.Timeout:
            print("⏱️ Request timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        return None


def main():
    """Main function for interactive single session processing"""
    print("🎯 Simple RPA Generator - Single Session Processor")
    print("=" * 60)
    
    try:
        generator = SimpleRpaGenerator()
        
        # List available sessions
        generator.list_available_sessions()
        
        # Interactive selection
        print("📝 Usage Examples:")
        print("1. Process by session name:")
        print("   python simple_rpa_generator.py enhanced_multiscreen_20250802_172440")
        print("\n2. Process specific files:")
        print("   python simple_rpa_generator.py video.mp4 interactions.json")
        
        # Example: Process the first available session
        import sys
        if len(sys.argv) > 1:
            session_name = sys.argv[1]
            video_path = f"records/{session_name}.mp4"
            json_path = f"records/{session_name}_interactions.json"
            
            if os.path.exists(video_path) and os.path.exists(json_path):
                generator.process_single_session(video_path, json_path)
            else:
                print(f"❌ Files not found for session: {session_name}")
        else:
            print("\n💡 Tip: Provide a session name as argument to process automatically")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()