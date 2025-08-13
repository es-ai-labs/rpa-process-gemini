#!/usr/bin/env python3
"""
Complete Video Processor for Murex RPA Workflows

Enhanced version that ensures end-to-end video processing to capture
complete workflows from start to finish without missing any steps.
"""

import json
import base64
import requests
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enhanced_murex_rpa_generator import EnhancedMurexRpaGenerator, UIInteraction

class CompleteVideoProcessor(EnhancedMurexRpaGenerator):
    """Processes complete video from start to finish ensuring no steps are missed"""
    
    def __init__(self):
        super().__init__()
        # Enhanced settings for complete video processing
        self.complete_video_config = {
            "fps": 1.0,  # Slightly higher for complete coverage
            "ensure_full_coverage": True,
            "sample_beginning_and_end": True,
            "include_idle_moments": True
        }
    
    def analyze_complete_video_duration(self, json_path: str) -> Tuple[float, float, int]:
        """Analyze the complete duration and interaction spread"""
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Get session duration
        session_duration = data.get('session_info', {}).get('duration', 0)
        
        # Find first and last interaction timestamps
        all_timestamps = []
        
        # Collect all timestamps
        for event in data.get('mouse_interactions', []):
            if 'timestamp' in event:
                all_timestamps.append(event['timestamp'])
        
        for event in data.get('keyboard_events', []):
            if 'timestamp' in event:
                all_timestamps.append(event['timestamp'])
        
        for event in data.get('app_switches', []):
            if 'timestamp' in event:
                all_timestamps.append(event['timestamp'])
        
        if all_timestamps:
            first_interaction = min(all_timestamps)
            last_interaction = max(all_timestamps)
        else:
            first_interaction = 0
            last_interaction = session_duration
        
        return session_duration, first_interaction, last_interaction
    
    def create_complete_timeline(self, interactions: List[UIInteraction], 
                               session_duration: float, first_interaction: float, 
                               last_interaction: float) -> str:
        """Create timeline ensuring complete video coverage"""
        
        timeline = []
        timeline.append("=== COMPLETE VIDEO TIMELINE FOR END-TO-END ANALYSIS ===")
        timeline.append(f"Session Duration: {session_duration:.1f} seconds")
        timeline.append(f"First Interaction: {first_interaction:.1f}s")
        timeline.append(f"Last Interaction: {last_interaction:.1f}s")
        timeline.append(f"Total Interactions: {len(interactions)}")
        timeline.append("")
        timeline.append("CRITICAL: Analyze the COMPLETE video from 0s to end to capture ALL workflow steps")
        timeline.append("")
        
        # Add specific markers for complete coverage
        timeline.append("📍 KEY ANALYSIS POINTS:")
        timeline.append(f"   🟢 Video Start (0.0s) - Capture initial screen state")
        timeline.append(f"   🟡 First Action ({first_interaction:.1f}s) - Workflow begins")
        
        # Add mid-points for long videos
        if session_duration > 60:  # If longer than 1 minute
            mid_point = session_duration / 2
            timeline.append(f"   🟠 Mid-point ({mid_point:.1f}s) - Ensure continuous coverage")
        
        timeline.append(f"   🟡 Last Action ({last_interaction:.1f}s) - Final interaction")
        timeline.append(f"   🔴 Video End ({session_duration:.1f}s) - Capture completion state")
        timeline.append("")
        
        # Create complete chronological sequence
        timeline.append("COMPLETE INTERACTION SEQUENCE (chronological order):")
        timeline.append("")
        
        for i, interaction in enumerate(interactions, 1):
            timeline.append(f"{i:2d}. [{interaction.timestamp:6.1f}s] {interaction.description}")
            if interaction.coordinates:
                timeline.append(f"     📍 Location: {interaction.coordinates}")
            if interaction.text_content:
                timeline.append(f"     📝 Text: '{interaction.text_content}'")
            if interaction.ui_context:
                timeline.append(f"     🎯 Context: {interaction.ui_context}")
        
        # Add coverage gaps analysis
        timeline.append("")
        timeline.append("🔍 COVERAGE ANALYSIS:")
        
        # Check for gaps in interactions
        gaps = self._find_interaction_gaps(interactions, session_duration)
        if gaps:
            timeline.append("   ⚠️  Potential gaps in interactions:")
            for gap in gaps:
                timeline.append(f"      Gap: {gap['start']:.1f}s - {gap['end']:.1f}s ({gap['duration']:.1f}s)")
                timeline.append(f"           May contain: Screen transitions, loading, or completion steps")
        else:
            timeline.append("   ✅ Good interaction coverage throughout video")
        
        timeline.append("")
        timeline.append("=" * 80)
        
        return "\n".join(timeline)
    
    def _find_interaction_gaps(self, interactions: List[UIInteraction], 
                              session_duration: float, gap_threshold: float = 5.0) -> List[Dict]:
        """Find gaps between interactions that might contain important workflow steps"""
        
        if not interactions:
            return [{'start': 0, 'end': session_duration, 'duration': session_duration}]
        
        gaps = []
        
        # Sort interactions by timestamp
        sorted_interactions = sorted(interactions, key=lambda x: x.timestamp)
        
        # Check gap at beginning
        first_timestamp = sorted_interactions[0].timestamp
        if first_timestamp > gap_threshold:
            gaps.append({
                'start': 0,
                'end': first_timestamp,
                'duration': first_timestamp
            })
        
        # Check gaps between interactions
        for i in range(len(sorted_interactions) - 1):
            current_time = sorted_interactions[i].timestamp
            next_time = sorted_interactions[i + 1].timestamp
            gap_duration = next_time - current_time
            
            if gap_duration > gap_threshold:
                gaps.append({
                    'start': current_time,
                    'end': next_time,
                    'duration': gap_duration
                })
        
        # Check gap at end
        last_timestamp = sorted_interactions[-1].timestamp
        if session_duration - last_timestamp > gap_threshold:
            gaps.append({
                'start': last_timestamp,
                'end': session_duration,
                'duration': session_duration - last_timestamp
            })
        
        return gaps
    
    def create_complete_workflow_prompt(self, complete_timeline: str, 
                                      session_duration: float) -> str:
        """Create enhanced prompt that emphasizes complete video analysis"""
        
        prompt = f"""You are an expert RPA analyst creating COMPLETE workflow documentation for Murex applications. 

🎯 CRITICAL REQUIREMENT: Analyze the ENTIRE video from start ({0.0}s) to finish ({session_duration:.1f}s) to capture ALL workflow steps.

🔍 CRITICAL FIELD ANALYSIS: For each field interaction in the video, carefully observe:
- Does the field have a dropdown icon (three dots with lines) on the far right? → DROPDOWN FIELD
- Is it just a label and input area with NO dropdown icon? → FREE TEXT FIELD
- Use this visual analysis to determine the correct interaction pattern for each field

COMPLETE ANALYSIS APPROACH:
🔴 MANDATORY: Process the video from 0.0 seconds to {session_duration:.1f} seconds
🔴 MANDATORY: Capture ALL steps including login, navigation, data entry, AND completion
🔴 MANDATORY: Include the final state/result of the workflow
🔴 MANDATORY: Do not stop at the last interaction - continue to video end

VIDEO ANALYSIS REQUIREMENTS:
✅ START STATE (0.0s): What is the initial screen/application state?
✅ LOGIN SEQUENCE: How does the user authenticate and enter the system?
✅ NAVIGATION: How does the user reach the target module/screen?
✅ WORKFLOW EXECUTION: What are ALL the data entry and interaction steps?
✅ COMPLETION: How does the workflow conclude? What is the final result?
✅ END STATE ({session_duration:.1f}s): What is the final screen showing?

{complete_timeline}

RPA COMMAND STRUCTURE FOR COMPLETE WORKFLOW:

CRITICAL DROPDOWN INTERACTION FORMAT:
For all dropdown selections, use this exact structure:
1. **Field Description:** In the "Section Name", Click on [Field Name] field, A dropdown list appears. Select "[Option]" from the "[Field Name]" dropdown menu.

MUREX UI NAVIGATION PATTERNS (CRITICAL CONTEXT):
These Murex-specific UI patterns must be incorporated into your RPA commands:

📋 **FILE/SCREEN ACCESS:**
- Access screens via top bar menu dropdown
- Click dropdown menu, then click again to open the target screen
- Pattern: "Click on [Menu] in the top bar, then click [Submenu] to access [Screen]"

🎯 **MUREX FIELD INTERACTION PATTERNS:**

**FIELD TYPE DETECTION:**
- All fields have: Label (left) + Input space (middle) + [Optional] Dropdown icon (far right)
- **Dropdown Fields**: Have three dots with lines icon on far right
- **Free Text Fields**: NO dropdown icon on far right, just label and input space

**FIELD INTERACTION METHODS:**

**Free Text Fields (NO dropdown icon):**
- Simply click in the input area and type
- Pattern: "Click in the '[Field Label]' input field and type '[Text]'"

**Dropdown Fields (WITH dropdown icon):**
- Method 1: Press Spacebar while field is focused (PREFERRED)
- Method 2: Click the dropdown icon (three dots with lines) on far right
- Pattern: "Click on the '[Field Label]' field and press Spacebar to open the dropdown list" OR "Click the dropdown icon on the far right of the '[Field Label]' field"

🔍 **LIST SELECTION MECHANISMS:**

**Single-Column Lists:**
- Search for string in search bar, press Enter
- Double-click on found item to select
- Pattern: "In the dropdown list, type '[Search Term]' in the search bar and press Enter. Double-click on '[Item]' to select it."

**Multi-Column Lists:**
- Find the 'Label' column or appropriate column header
- Click on that column header
- Type search query in the top input field
- Double-click on result
- Pattern: "In the multi-column list, click on the 'Label' column header. Type '[Search Term]' in the top search input field. Double-click on '[Item]' to select it."

**Tree Structure Lists:**
- Press Ctrl+F to enable search functionality
- Type search text and press Enter
- Double-click to select the item
- Pattern: "In the tree structure list, press Ctrl+F to enable search. Type '[Search Term]' and press Enter. Double-click on '[Item]' to select it."

DETAILED INTERACTION REQUIREMENTS:
✅ FIELD TYPE DETECTION: First determine if field has dropdown icon or is free text
✅ FREE TEXT FIELDS: "Click in the '[Field Label]' input field and type '[Text]'"
✅ DROPDOWN FIELDS: "Click on the '[Field Label]' field and press Spacebar to open the dropdown list"
✅ ALTERNATIVE DROPDOWN: "Click the dropdown icon (three dots with lines) on the far right of the '[Field Label]' field"
✅ LIST NAVIGATION: Use appropriate pattern based on list type (single-column, multi-column, tree)
✅ SELECTION COMPLETION: Always end with "Double-click on '[Item]' to select it"
✅ BUTTON ACTIONS: "Click the '[Button Name]' button"
✅ MENU NAVIGATION: "Click on [Menu] in the top bar, then click [Submenu]"

STRUCTURED OUTPUT FORMAT:
Use numbered steps with descriptive headers:

1. **Login Process:** Login to Murex application using username [USERNAME] and password [PASSWORD], then click Login button.

2. **Navigate to Module:** Click on the [GROUP] group and click Start.

3. **Access Function:** On the main page, type '[SEARCH_TERM]' in the search field and press Enter.

4. **Free Text Entry:** Click in the '[FIELD_LABEL]' input field and type '[TEXT_VALUE]'. Press Tab to move to next field.

5. **Dropdown Selection:** Click on the '[FIELD_LABEL]' field and press Spacebar to open the dropdown list. In the dropdown list, type '[SEARCH_TERM]' in the search bar and press Enter. Double-click on '[ITEM]' to select it.

6. **Alternative Dropdown:** Click the dropdown icon (three dots with lines) on the far right of the '[FIELD_LABEL]' field to open the list. Select '[ITEM]' using appropriate list navigation pattern.

7. **Action Execution:** Click the '[BUTTON_NAME]' button to [ACTION_PURPOSE].

8. **Completion:** [Describe final steps and results]

CRITICAL OUTPUT REQUIREMENTS:
🎯 STRUCTURED STEPS: Use numbered steps with descriptive headers
🎯 MUREX UI PATTERNS: Apply the specific Murex navigation patterns described above
🎯 FIELD TYPE DETECTION: Distinguish between free text fields and dropdown fields
🎯 FREE TEXT HANDLING: "Click in the '[Field Label]' input field and type '[Text]'"
🎯 DROPDOWN HANDLING: "Click on the '[Field Label]' field and press Spacebar" (preferred)
🎯 ALTERNATIVE DROPDOWN: "Click the dropdown icon (three dots with lines)" (if Spacebar doesn't work)
🎯 LIST HANDLING: Use appropriate pattern (single-column, multi-column, or tree structure)
🎯 SELECTION COMPLETION: Always end with "Double-click on '[Item]' to select it"
🎯 MENU NAVIGATION: Use top bar menu patterns for screen access
🎯 COMPLETE WORKFLOW: From login to final completion state
🎯 CONTEXT-AWARE ACTIONS: Use video context to determine field type and appropriate interaction

EXAMPLE STRUCTURED OUTPUT WITH MUREX FIELD PATTERNS:
"1. **Login to Murex:** Login to Murex application using username MUREXFO and password MUREX, then click Login button.

2. **Access Module:** Click on the FO_AM group and click Start.

3. **Navigate to Function:** Click on 'Tools' in the top bar menu, then click 'Revaluation rate curves' to access the function.

4. **Enter Description:** Click in the 'Description' input field and type 'Bond revaluation analysis'. Press Tab to move to next field.

5. **Select Currency:** Click on the 'Currency' field and press Spacebar to open the dropdown list. In the dropdown list, type 'ANG' in the search bar and press Enter. Double-click on 'ANG' to select it.

6. **Enter Amount:** Click in the 'Amount' input field and type '1000000'. Press Tab to move to next field.

7. **Select Industry:** Click on the 'Industry' field and press Spacebar to open the dropdown list. In the multi-column list, click on the 'Label' column header. Type 'Insurance' in the top search input field. Double-click on 'Insurance' to select it.

8. **Navigate Category Tree:** Click on the 'Category' field and press Spacebar to open the tree structure list. Press Ctrl+F to enable search. Type 'Government Bonds' and press Enter. Double-click on 'Government Bonds' to select it.

9. **Enter Comments:** Click in the 'Comments' input field and type 'Monthly revaluation process'. 

10. **Execute Action:** Click the 'Submit' button to execute the configuration.

11. **Complete Workflow:** Review the confirmation screen and close any open dialogs to complete the workflow."

Generate the COMPLETE RPA workflow commands that document every step from video start to video end, ensuring no part of the process is omitted."""

        return prompt
    
    def process_complete_workflow(self, video_path: str, json_path: str) -> str:
        """Process the complete video ensuring end-to-end coverage"""
        
        print("Processing video for RPA workflow generation...")
        
        # Validate inputs (silently)
        validation_results = self.validator.validate_complete_workflow(video_path, json_path)
        
        has_errors = False
        for category, results in validation_results.items():
            for result in results:
                if result.severity == 'error':
                    print(f"❌ {result.message}")
                    has_errors = True
        
        if has_errors:
            return None
        
        # Analyze video and extract interactions
        session_duration, first_interaction, last_interaction = self.analyze_complete_video_duration(json_path)
        interactions = self.extract_enhanced_interactions(json_path)
        
        # Create complete timeline
        complete_timeline = self.create_complete_timeline(
            interactions, session_duration, first_interaction, last_interaction
        )
        
        # Create complete workflow prompt
        prompt = self.create_complete_workflow_prompt(complete_timeline, session_duration)
        
        # Check video file
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if size_mb > self.config.MAX_FILE_SIZE_MB:
            print(f"❌ Video file too large: {size_mb:.1f} MB")
            return None
        
        # Encode video
        try:
            with open(video_path, 'rb') as f:
                video_bytes = f.read()
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        except Exception as e:
            print(f"❌ Error encoding video: {e}")
            return None
        
        # Enhanced configuration for complete processing
        complete_config = {
            "temperature": 0.1,  # Lower for more consistent complete analysis
            "topK": 2,
            "topP": 0.7,
            "maxOutputTokens": 8000,  # More tokens for complete workflows
            "responseMimeType": "text/plain"
        }
        
        # Video metadata for complete analysis
        complete_video_metadata = {
            "fps": self.complete_video_config["fps"]  # Ensure good coverage
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
                            "video_metadata": complete_video_metadata
                        }
                    ]
                }
            ],
            "generationConfig": complete_config
        }
        
        # Make API request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.GEMINI_MODEL}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        print(f"Analyzing complete video ({session_duration:.1f}s) for end-to-end workflow...")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=600)  # Longer timeout
            
            if response.status_code == 200:
                result = response.json()
                
                
                # Extract complete RPA commands
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text_parts = [part.get("text", "") for part in candidate["content"]["parts"]]
                        rpa_commands = "".join(text_parts).strip()
                        
                        # Validate that we got a complete workflow
                        completion_score = self._assess_workflow_completeness(
                            rpa_commands, session_duration, interactions
                        )
                        
                        # Only output if completeness is adequate
                        if completion_score['score'] < 6:
                            print(f"⚠️  Workflow completeness score: {completion_score['score']:.1f}/10")
                            print("❌ Generated workflow may be incomplete - missing key elements")
                            if not completion_score['has_login']:
                                print("   Missing: Login sequence")
                            if not completion_score['has_completion']:
                                print("   Missing: Completion/final state")
                            if not completion_score['adequate_length']:
                                print("   Missing: Adequate detail level")
                            if not completion_score['has_murex_patterns']:
                                print(f"   Missing: Murex UI patterns (found {completion_score['murex_pattern_count']}/8)")
                            if not completion_score['has_structured_format']:
                                print("   Missing: Structured format with numbered steps and headers")
                            print("🔄 Consider re-processing with better video quality or longer recording")
                            return None
                        
                        # Save clean RPA commands only
                        base_name = os.path.splitext(os.path.basename(video_path))[0]
                        output_name = f"{base_name}_RPA_commands.txt"
                        
                        output_dir = self.config.ensure_output_dir()
                        output_path = os.path.join(output_dir, output_name)
                        
                        # Save only the clean RPA commands
                        with open(output_path, 'w') as f:
                            f.write(rpa_commands)
                        
                        print(f"✅ Complete RPA workflow saved to: {output_path}")
                        print(f"✅ Completeness score: {completion_score['score']:.1f}/10")
                        print(f"✅ Murex UI patterns: {completion_score['murex_pattern_count']}/8 detected")
                        print(f"✅ Structured format: {'Yes' if completion_score['has_structured_format'] else 'No'}")
                        
                        # Output the clean RPA commands directly
                        print("\n" + "="*50)
                        print("RPA WORKFLOW COMMANDS:")
                        print("="*50)
                        print(rpa_commands)
                        print("="*50)
                        
                        return rpa_commands
                        
            else:
                print(f"❌ API Error: HTTP {response.status_code}")
                if response.text:
                    print(f"Error details: {response.text[:300]}")
                
        except Exception as e:
            print(f"❌ Processing error: {e}")
            
        return None
    
    def _assess_workflow_completeness(self, rpa_commands: str, session_duration: float, 
                                    interactions: List[UIInteraction]) -> Dict:
        """Assess if the generated workflow captures the complete process and follows Murex patterns"""
        
        command_lower = rpa_commands.lower()
        
        # Check for login
        has_login = any(word in command_lower for word in ['login', 'username', 'password', 'authenticate'])
        
        # Check for completion indicators
        completion_words = ['complete', 'finish', 'close', 'final', 'result', 'summary', 'end', 'done']
        has_completion = any(word in command_lower for word in completion_words)
        
        # Check for Murex-specific UI patterns
        murex_patterns = [
            'press spacebar',
            'input field and type',
            'dropdown icon',
            'three dots',
            'double-click',
            'top bar',
            'ctrl+f',
            'search bar and press enter'
        ]
        murex_pattern_count = sum(1 for pattern in murex_patterns if pattern in command_lower)
        has_murex_patterns = murex_pattern_count >= 3  # At least 3 Murex-specific patterns
        
        # Check for structured format
        has_numbered_steps = '1.' in rpa_commands and '2.' in rpa_commands
        has_descriptive_headers = '**' in rpa_commands  # Bold headers
        
        # Check adequate length (should be proportional to session duration and interactions)
        expected_min_length = max(400, len(interactions) * 25)  # Higher minimum for detailed Murex patterns
        adequate_length = len(rpa_commands) >= expected_min_length
        
        # Calculate overall score
        score = 0
        if has_login:
            score += 2
        if has_completion:
            score += 2
        if adequate_length:
            score += 2
        if has_murex_patterns:
            score += 2  # Important for Murex accuracy
        if has_numbered_steps:
            score += 1
        if has_descriptive_headers:
            score += 1
        
        return {
            'score': score,
            'has_login': has_login,
            'has_completion': has_completion,
            'adequate_length': adequate_length,
            'has_murex_patterns': has_murex_patterns,
            'murex_pattern_count': murex_pattern_count,
            'has_structured_format': has_numbered_steps and has_descriptive_headers,
            'command_length': len(rpa_commands),
            'expected_min_length': expected_min_length
        }


def main():
    """Main function for complete workflow processing"""
    print("🎬 Complete Murex RPA Workflow Processor")
    print("=" * 70)
    print("End-to-end video analysis ensuring complete workflow capture")
    print("=" * 70)
    
    # File paths
    import sys
    if len(sys.argv) > 2:
        video_path = sys.argv[1]
        json_path = sys.argv[2]
    else:
        # Default paths
        video_path = "records/enhanced_multiscreen_20250803_064201.mp4"
        json_path = "records/enhanced_multiscreen_interactions_20250803_064519.json"
    
    print(f"📹 Video: {video_path}")
    print(f"📊 JSON:  {json_path}")
    
    # Check files exist
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return
    
    try:
        processor = CompleteVideoProcessor()
        workflow = processor.process_complete_workflow(video_path, json_path)
        
        if workflow:
            print(f"\n✅ RPA workflow ready for execution")
        else:
            print(f"\n❌ Workflow generation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()