#!/usr/bin/env python3
"""
Enhanced Murex RPA Workflow Generator

A sophisticated tool that combines JSON UI interactions with video analysis 
to generate contextual, human-readable RPA commands for Murex workflows.

Key Features:
- Video-aware UI element detection
- Contextual action mapping 
- Human-editable workflow structure
- Generic enough for multiple Murex screens
- Optimized frame rate for UI processing
"""

import json
import base64
import requests
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from simple_rpa_generator import SimpleRpaGenerator
from rpa_config import RpaConfig
from workflow_validator import WorkflowValidator

@dataclass
class UIInteraction:
    """Represents a UI interaction with context"""
    timestamp: float
    action_type: str  # 'click', 'type', 'key', 'navigate'
    description: str
    ui_context: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    text_content: Optional[str] = None
    confidence: float = 0.0

@dataclass
class WorkflowSection:
    """Represents a logical section of the workflow"""
    name: str
    interactions: List[UIInteraction]
    description: str

class EnhancedMurexRpaGenerator(SimpleRpaGenerator):
    """Enhanced RPA generator with video-aware UI element detection"""
    
    def __init__(self):
        super().__init__()
        self.validator = WorkflowValidator()
        # Optimized for UI processing
        self.ui_video_config = {
            "fps": 0.8,  # Lower frame rate for UI interactions
            "sample_key_moments": True,
            "focus_on_changes": True
        }
        
    def extract_enhanced_interactions(self, json_path: str) -> List[UIInteraction]:
        """Extract interactions with enhanced context analysis"""
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        interactions = []
        
        # Process mouse interactions
        mouse_events = data.get('mouse_interactions', [])
        clicks = []
        
        for event in mouse_events:
            if event.get('type') == 'mouse_press' and event.get('button') == 'left':
                clicks.append(UIInteraction(
                    timestamp=event.get('timestamp', 0),
                    action_type='click',
                    description=f"Click at screen location",
                    coordinates=(event.get('position', {}).get('x', 0), 
                               event.get('position', {}).get('y', 0))
                ))
        
        # Process keyboard interactions with better text grouping
        keyboard_events = data.get('keyboard_events', [])
        text_sequences = self._group_text_sequences(keyboard_events)
        
        for seq in text_sequences:
            if seq['text'].strip():
                interactions.append(UIInteraction(
                    timestamp=seq['timestamp'],
                    action_type='type',
                    description=f"Type '{seq['text']}'",
                    text_content=seq['text'],
                    ui_context=seq.get('end_action')
                ))
        
        # Add clicks
        interactions.extend(clicks)
        
        # Process application switches
        for switch in data.get('app_switches', []):
            interactions.append(UIInteraction(
                timestamp=switch.get('timestamp', 0),
                action_type='navigate',
                description=f"Switch from {switch.get('from_app')} to {switch.get('to_app')}",
                ui_context=f"app_switch:{switch.get('to_app')}"
            ))
        
        # Sort chronologically
        interactions.sort(key=lambda x: x.timestamp)
        
        return interactions
    
    def _group_text_sequences(self, keyboard_events: List[Dict]) -> List[Dict]:
        """Improved text sequence grouping with better end action detection"""
        
        sequences = []
        current_text = ""
        sequence_start = None
        
        for event in keyboard_events:
            if event.get('type') == 'key_press' and event.get('is_character'):
                key = event.get('key_name', '')
                timestamp = event.get('timestamp', 0)
                
                if key in ['Return', 'Enter']:
                    if current_text.strip():
                        sequences.append({
                            'timestamp': sequence_start,
                            'text': current_text,
                            'end_action': 'enter'
                        })
                    current_text = ""
                    sequence_start = None
                elif key == 'Tab':
                    if current_text.strip():
                        sequences.append({
                            'timestamp': sequence_start,
                            'text': current_text,
                            'end_action': 'tab'
                        })
                    current_text = ""
                    sequence_start = None
                elif key in ['Delete', 'BackSpace']:
                    if current_text:
                        current_text = current_text[:-1]
                    else:
                        sequences.append({
                            'timestamp': timestamp,
                            'text': '',
                            'end_action': 'delete'
                        })
                elif key and len(key) == 1:  # Regular character
                    if not current_text:
                        sequence_start = timestamp
                    current_text += key
        
        # Handle remaining text
        if current_text.strip():
            sequences.append({
                'timestamp': sequence_start,
                'text': current_text,
                'end_action': 'incomplete'
            })
        
        return sequences
    
    def create_interaction_timeline(self, interactions: List[UIInteraction]) -> str:
        """Create a detailed timeline for video analysis"""
        
        timeline = []
        timeline.append("=== UI INTERACTION TIMELINE FOR VIDEO ANALYSIS ===")
        timeline.append(f"Total Interactions: {len(interactions)}")
        timeline.append("")
        timeline.append("Key moments for video frame analysis:")
        timeline.append("")
        
        # Group interactions by time windows for efficient video sampling
        time_windows = self._create_time_windows(interactions)
        
        for i, window in enumerate(time_windows):
            timeline.append(f"--- Time Window {i+1}: {window['start']:.1f}s - {window['end']:.1f}s ---")
            for interaction in window['interactions']:
                timeline.append(f"[{interaction.timestamp:.1f}s] {interaction.description}")
                if interaction.coordinates:
                    timeline.append(f"    Coordinates: {interaction.coordinates}")
                if interaction.text_content:
                    timeline.append(f"    Text: '{interaction.text_content}'")
            timeline.append("")
        
        return "\n".join(timeline)
    
    def _create_time_windows(self, interactions: List[UIInteraction], window_size: float = 2.0) -> List[Dict]:
        """Group interactions into time windows for efficient video analysis"""
        
        if not interactions:
            return []
        
        windows = []
        current_window = {
            'start': interactions[0].timestamp,
            'end': interactions[0].timestamp,
            'interactions': [interactions[0]]
        }
        
        for interaction in interactions[1:]:
            if interaction.timestamp - current_window['end'] <= window_size:
                # Add to current window
                current_window['end'] = interaction.timestamp
                current_window['interactions'].append(interaction)
            else:
                # Start new window
                windows.append(current_window)
                current_window = {
                    'start': interaction.timestamp,
                    'end': interaction.timestamp,
                    'interactions': [interaction]
                }
        
        # Add the last window
        windows.append(current_window)
        
        return windows
    
    def create_enhanced_prompt(self, timeline: str, interactions: List[UIInteraction]) -> str:
        """Create an enhanced prompt that leverages video analysis for UI context"""
        
        interaction_summary = self._create_interaction_summary(interactions)
        
        prompt = f"""You are an expert RPA analyst creating detailed, contextual workflow commands for Murex applications. Your task is to analyze both the user interaction timeline AND the video to generate precise, human-readable RPA commands.

CRITICAL ANALYSIS APPROACH:
🎯 VIDEO-FIRST ANALYSIS: Use the video to identify what UI elements users are interacting with
🎯 CONTEXTUAL MAPPING: Correlate video frames with interaction timestamps to understand user intent  
🎯 SEMANTIC UNDERSTANDING: Describe what elements are being used (buttons, fields, dropdowns, tabs)
🎯 MUREX-AWARE: Recognize common Murex UI patterns and workflows
🎯 HUMAN-EDITABLE: Generate clear, structured commands that humans can easily modify

{timeline}

INTERACTION SUMMARY:
{interaction_summary}

VIDEO ANALYSIS REQUIREMENTS:
✅ IDENTIFY UI ELEMENTS: For each interaction, identify the specific UI element being used
- Login fields, buttons, menu items
- Search bars, dropdown menus, data grids
- Tabs, panels, dialog boxes
- Action buttons, navigation elements

✅ UNDERSTAND CONTEXT: Determine the purpose of each action
- What screen/module is the user in?
- What type of data are they entering?
- What workflow step are they performing?

✅ DETECT PATTERNS: Recognize common Murex interaction patterns
- Login sequence
- Menu navigation 
- Search and filter operations
- Data entry workflows
- Confirmation and submission steps

RPA COMMAND STRUCTURE:
Generate commands in this human-readable format:

1. LOGIN & SETUP:
"Login to Murex application using username [USERNAME] and password [PASSWORD], then click Login button. Navigate to [MODULE] by clicking on [GROUP] and then Start."

2. NAVIGATION & SEARCH:
"On the main page, type '[SEARCH_TERM]' in the search field and press Enter. In the [SECTION] area, locate the [ELEMENT_TYPE] for '[VALUE]' and [ACTION]."

3. DATA ENTRY:
"In the [FORM/GRID], locate the '[FIELD_NAME]' field and type '[VALUE]'. Use Tab to move to the next field. For dropdown fields, type '[OPTION]' directly to select."

4. COMPLETION:
"Click the '[BUTTON_NAME]' button to [ACTION_PURPOSE]. If confirmation dialog appears, click '[RESPONSE]'. Wait for processing to complete."

EXAMPLE OUTPUT:
"Login to Murex application using username MUREXFO and password MUREX, then click Login button. Click on the FO_AM group and click Start. On the main page, type 'Revaluation rate curves' in the search field and press Enter. In the currency list, type 'ANG' in the search filter and press Enter. Double-click on the 'ANG' option in the results list. In the configuration table, double-click on the cell containing 'ANG :std'. On the details page, click the 'Details' action button to open the configuration panel. Review the displayed configuration settings to complete the task."

Generate structured, contextual RPA commands that describe the specific UI elements and their purposes based on what you see in the video."""

        return prompt
    
    def _create_interaction_summary(self, interactions: List[UIInteraction]) -> str:
        """Create a summary of interaction types and patterns"""
        
        summary = []
        
        # Count interaction types
        type_counts = {}
        for interaction in interactions:
            type_counts[interaction.action_type] = type_counts.get(interaction.action_type, 0) + 1
        
        summary.append("Interaction Type Breakdown:")
        for action_type, count in type_counts.items():
            summary.append(f"- {action_type.title()}: {count}")
        
        summary.append("")
        
        # Identify text patterns
        text_inputs = [i.text_content for i in interactions if i.text_content]
        if text_inputs:
            summary.append("Text Input Patterns:")
            for text in text_inputs[:5]:  # Show first 5
                summary.append(f"- '{text}'")
            if len(text_inputs) > 5:
                summary.append(f"... and {len(text_inputs) - 5} more")
        
        return "\n".join(summary)
    
    def process_enhanced_workflow(self, video_path: str, json_path: str) -> str:
        """Process workflow with enhanced video analysis"""
        
        print(f"🚀 Enhanced Murex RPA Workflow Generator")
        print("=" * 60)
        print("Generating contextual, human-editable RPA commands")
        
        # Validate inputs first
        print("🔍 Validating input files...")
        validation_results = self.validator.validate_complete_workflow(video_path, json_path)
        
        # Check for critical errors
        has_errors = False
        for category, results in validation_results.items():
            for result in results:
                if result.severity == 'error':
                    print(f"❌ {result.message}")
                    if result.suggestion:
                        print(f"   💡 {result.suggestion}")
                    has_errors = True
                elif result.severity == 'warning':
                    print(f"⚠️  {result.message}")
        
        if has_errors:
            print("❌ Critical validation errors found. Please fix before proceeding.")
            return None
        
        print("✅ Input validation passed")
        
        # Extract enhanced interactions
        print("🔍 Extracting UI interactions with context...")
        interactions = self.extract_enhanced_interactions(json_path)
        print(f"📊 Found {len(interactions)} contextual interactions")
        
        # Create analysis timeline
        timeline = self.create_interaction_timeline(interactions)
        
        # Create enhanced prompt
        prompt = self.create_enhanced_prompt(timeline, interactions)
        
        # Check video file
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if size_mb > self.config.MAX_FILE_SIZE_MB:
            print(f"❌ Video file too large: {size_mb:.1f} MB")
            return None
        
        print(f"✅ Video size OK: {size_mb:.1f} MB")
        
        # Encode video with optimized settings for UI analysis
        print("🎬 Encoding video for UI element analysis...")
        try:
            with open(video_path, 'rb') as f:
                video_bytes = f.read()
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        except Exception as e:
            print(f"❌ Error encoding video: {e}")
            return None
        
        # Enhanced configuration for UI processing
        ui_analysis_config = {
            "temperature": 0.2,  # Lower for more consistent UI element identification
            "topK": 3,
            "topP": 0.8,
            "maxOutputTokens": 6000,  # More tokens for detailed descriptions
            "responseMimeType": "text/plain"
        }
        
        # Optimized video metadata for UI processing
        ui_video_metadata = {
            "fps": self.ui_video_config["fps"]  # Lower frame rate for UI
        }
        
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
                            "video_metadata": ui_video_metadata
                        }
                    ]
                }
            ],
            "generationConfig": ui_analysis_config
        }
        
        # Make API request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.GEMINI_MODEL}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        print("🧠 Analyzing video for UI context and generating RPA commands...")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=400)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract usage info
                if "usageMetadata" in result:
                    usage = result["usageMetadata"]
                    total_tokens = usage.get('totalTokenCount', 0)
                    estimated_cost = (total_tokens / 1000) * 0.00015
                    print(f"💰 Tokens used: {total_tokens:,}, Estimated cost: ${estimated_cost:.6f}")
                
                # Extract enhanced RPA commands
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text_parts = [part.get("text", "") for part in candidate["content"]["parts"]]
                        rpa_commands = "".join(text_parts).strip()
                        
                        # Save enhanced commands
                        base_name = os.path.splitext(os.path.basename(video_path))[0]
                        output_name = f"{base_name}_ENHANCED_rpa_workflow.txt"
                        
                        output_dir = self.config.ensure_output_dir()
                        output_path = os.path.join(output_dir, output_name)
                        
                        # Create structured output
                        structured_output = self._create_structured_output(
                            rpa_commands, video_path, json_path, interactions
                        )
                        
                        with open(output_path, 'w') as f:
                            f.write(structured_output)
                        
                        # Validate generated output
                        print("🔍 Validating generated workflow...")
                        output_validation = self.validator.validate_workflow_output(rpa_commands)
                        
                        for result in output_validation:
                            if result.severity == 'error':
                                print(f"❌ {result.message}")
                            elif result.severity == 'warning':
                                print(f"⚠️  {result.message}")
                            else:
                                print(f"✅ {result.message}")
                        
                        print(f"✅ Enhanced RPA workflow saved to: {output_path}")
                        print(f"\n🎯 Workflow Preview:")
                        print("-" * 60)
                        preview = rpa_commands[:500] + "..." if len(rpa_commands) > 500 else rpa_commands
                        print(preview)
                        
                        print(f"\n📋 Enhancement Summary:")
                        print(f"   • Video-aware UI element detection")
                        print(f"   • Contextual interaction mapping")
                        print(f"   • Human-editable command structure")
                        print(f"   • {len(interactions)} interactions processed")
                        print(f"   • Optimized for Murex workflows")
                        
                        return rpa_commands
                        
            else:
                print(f"❌ API Error: HTTP {response.status_code}")
                if response.text:
                    print(f"Error details: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Processing error: {e}")
            
        return None
    
    def _create_structured_output(self, rpa_commands: str, video_path: str, 
                                 json_path: str, interactions: List[UIInteraction]) -> str:
        """Create well-structured, human-editable output"""
        
        header = f"""# Enhanced Murex RPA Workflow Commands
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Source Video: {os.path.basename(video_path)}
# Source JSON: {os.path.basename(json_path)}
# Processing Mode: Enhanced Video-Aware Analysis
# Total Interactions: {len(interactions)}
# Frame Rate Used: {self.ui_video_config['fps']} fps (optimized for UI)
#
# INSTRUCTIONS FOR EDITING:
# - This file is designed to be human-readable and editable
# - Modify values in brackets [VALUE] as needed
# - Adjust timing and sequences based on your requirements
# - Test workflow sections individually before full execution
#
# WORKFLOW STRUCTURE:
# The commands below are organized in logical sections for easy modification

"""
        
        footer = f"""

# END OF WORKFLOW
# 
# Notes:
# - Commands generated using video analysis for UI context
# - Interaction timestamps preserved for reference
# - Generic enough for multiple Murex modules
# - Optimized for human editing and maintenance
"""
        
        return header + rpa_commands + footer


def main():
    """Main function for enhanced RPA generation"""
    print("🚀 Enhanced Murex RPA Workflow Generator")
    print("=" * 60)
    print("Video-aware • Context-sensitive • Human-editable")
    print("=" * 60)
    
    # File paths - modify these or pass as arguments
    import sys
    if len(sys.argv) > 2:
        video_path = sys.argv[1]
        json_path = sys.argv[2]
    else:
        # Default paths - update these to match your latest recordings
        video_path = "records/enhanced_multiscreen_20250803_064201.mp4"
        json_path = "records/enhanced_multiscreen_interactions_20250803_064519.json"
    
    print(f"📹 Video: {video_path}")
    print(f"📊 JSON:  {json_path}")
    
    # Check if files exist
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return
    
    try:
        generator = EnhancedMurexRpaGenerator()
        workflow = generator.process_enhanced_workflow(video_path, json_path)
        
        if workflow:
            print(f"\n🎉 SUCCESS: Enhanced RPA workflow generated!")
            print(f"✅ Video-aware UI element detection")
            print(f"✅ Contextual interaction mapping")
            print(f"✅ Human-editable command structure")
            print(f"✅ Optimized for Murex applications")
            print(f"📁 Ready for your RPA execution engine")
        else:
            print(f"\n❌ Enhanced workflow generation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()