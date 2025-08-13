#!/usr/bin/env python3
"""
Workflow Validator for Enhanced Murex RPA Generator

Provides validation and error handling for video, JSON, and generated workflow files.
Helps ensure high-quality RPA command generation.
"""

import json
import os
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    message: str
    severity: str  # 'error', 'warning', 'info'
    suggestion: Optional[str] = None

class WorkflowValidator:
    """Validates inputs and outputs for RPA workflow generation"""
    
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for validation messages"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_video_file(self, video_path: str) -> List[ValidationResult]:
        """Validate video file for RPA processing"""
        results = []
        
        # Check file existence
        if not os.path.exists(video_path):
            results.append(ValidationResult(
                is_valid=False,
                message=f"Video file not found: {video_path}",
                severity='error',
                suggestion="Check the file path and ensure the video file exists"
            ))
            return results
        
        # Check file size
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if size_mb > 100:  # Assuming 100MB limit for Gemini API
            results.append(ValidationResult(
                is_valid=False,
                message=f"Video file too large: {size_mb:.1f} MB",
                severity='error',
                suggestion="Compress the video or reduce recording duration. Consider using lower resolution for UI recordings."
            ))
        elif size_mb > 50:
            results.append(ValidationResult(
                is_valid=True,
                message=f"Video file large: {size_mb:.1f} MB",
                severity='warning',
                suggestion="Large files may take longer to process and cost more tokens"
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                message=f"Video file size OK: {size_mb:.1f} MB",
                severity='info'
            ))
        
        # Check file extension
        if not video_path.lower().endswith(('.mp4', '.mov', '.avi')):
            results.append(ValidationResult(
                is_valid=False,
                message="Unsupported video format",
                severity='error',
                suggestion="Use MP4, MOV, or AVI format for best compatibility"
            ))
        
        return results
    
    def validate_json_file(self, json_path: str) -> List[ValidationResult]:
        """Validate JSON interaction file"""
        results = []
        
        # Check file existence
        if not os.path.exists(json_path):
            results.append(ValidationResult(
                is_valid=False,
                message=f"JSON file not found: {json_path}",
                severity='error',
                suggestion="Check the file path and ensure the interaction JSON file exists"
            ))
            return results
        
        # Parse JSON
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Invalid JSON format: {e}",
                severity='error',
                suggestion="Check the JSON file for syntax errors and ensure it's properly formatted"
            ))
            return results
        
        # Validate JSON structure
        required_keys = ['mouse_interactions', 'keyboard_events']
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Missing required JSON keys: {missing_keys}",
                severity='error',
                suggestion="Ensure the interaction recording captured all required data"
            ))
        
        # Check interaction counts
        mouse_count = len(data.get('mouse_interactions', []))
        keyboard_count = len(data.get('keyboard_events', []))
        
        if mouse_count == 0 and keyboard_count == 0:
            results.append(ValidationResult(
                is_valid=False,
                message="No interactions found in JSON file",
                severity='error',
                suggestion="Re-record the workflow with user interactions"
            ))
        elif mouse_count < 3:
            results.append(ValidationResult(
                is_valid=True,
                message=f"Very few mouse interactions: {mouse_count}",
                severity='warning',
                suggestion="Workflow might be too simple or recording may be incomplete"
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                message=f"Interactions found - Mouse: {mouse_count}, Keyboard: {keyboard_count}",
                severity='info'
            ))
        
        # Check session duration
        session_info = data.get('session_info', {})
        duration = session_info.get('duration', 0)
        
        if duration == 0:
            results.append(ValidationResult(
                is_valid=True,
                message="No session duration info",
                severity='warning',
                suggestion="Session duration helps with timing analysis"
            ))
        elif duration > 600:  # 10 minutes
            results.append(ValidationResult(
                is_valid=True,
                message=f"Long session duration: {duration:.1f} seconds",
                severity='warning',
                suggestion="Long workflows may be complex to process and generate lengthy commands"
            ))
        
        return results
    
    def validate_time_synchronization(self, video_path: str, json_path: str) -> List[ValidationResult]:
        """Check if video and JSON timestamps are synchronized"""
        results = []
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Get session duration from JSON
            json_duration = data.get('session_info', {}).get('duration', 0)
            
            # Get video duration (approximate check using file size)
            video_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            
            # Rough estimate: 1MB per 10 seconds for UI recording
            estimated_video_duration = video_size_mb * 10
            
            if json_duration > 0:
                duration_diff = abs(json_duration - estimated_video_duration)
                if duration_diff > 30:  # More than 30 seconds difference
                    results.append(ValidationResult(
                        is_valid=True,
                        message=f"Potential timing mismatch between video and JSON",
                        severity='warning',
                        suggestion="Verify that video and JSON were recorded in the same session"
                    ))
                else:
                    results.append(ValidationResult(
                        is_valid=True,
                        message="Video and JSON timing appears synchronized",
                        severity='info'
                    ))
            
        except Exception as e:
            results.append(ValidationResult(
                is_valid=True,
                message=f"Could not verify timing synchronization: {e}",
                severity='warning',
                suggestion="Manual verification recommended"
            ))
        
        return results
    
    def validate_workflow_output(self, rpa_commands: str) -> List[ValidationResult]:
        """Validate generated RPA workflow commands"""
        results = []
        
        if not rpa_commands or not rpa_commands.strip():
            results.append(ValidationResult(
                is_valid=False,
                message="No RPA commands generated",
                severity='error',
                suggestion="Check API response and input quality"
            ))
            return results
        
        # Check command length
        if len(rpa_commands) < 100:
            results.append(ValidationResult(
                is_valid=True,
                message="Generated commands are very short",
                severity='warning',
                suggestion="Workflow might be too simple or generation incomplete"
            ))
        elif len(rpa_commands) > 5000:
            results.append(ValidationResult(
                is_valid=True,
                message="Generated commands are very long",
                severity='warning',
                suggestion="Consider breaking into smaller workflow sections"
            ))
        
        # Check for common RPA patterns
        command_lower = rpa_commands.lower()
        
        # Check for login pattern
        if 'login' not in command_lower:
            results.append(ValidationResult(
                is_valid=True,
                message="No login sequence detected",
                severity='warning',
                suggestion="Most Murex workflows start with login - verify if this is intentional"
            ))
        
        # Check for Murex-specific terms
        murex_terms = ['murex', 'click', 'type', 'button', 'field']
        found_terms = [term for term in murex_terms if term in command_lower]
        
        if len(found_terms) < 3:
            results.append(ValidationResult(
                is_valid=True,
                message="Few Murex/UI interaction terms found",
                severity='warning',
                suggestion="Commands might be too generic - verify UI context was captured"
            ))
        
        # Check for placeholder values
        if '[' in rpa_commands and ']' in rpa_commands:
            results.append(ValidationResult(
                is_valid=True,
                message="Placeholder values found in commands",
                severity='info',
                suggestion="Remember to replace placeholder values with actual data before execution"
            ))
        
        results.append(ValidationResult(
            is_valid=True,
            message=f"RPA commands generated successfully ({len(rpa_commands)} characters)",
            severity='info'
        ))
        
        return results
    
    def validate_complete_workflow(self, video_path: str, json_path: str, 
                                 rpa_commands: Optional[str] = None) -> Dict[str, List[ValidationResult]]:
        """Perform complete validation of the workflow generation process"""
        
        print("🔍 Running complete workflow validation...")
        
        validation_results = {
            'video': self.validate_video_file(video_path),
            'json': self.validate_json_file(json_path),
            'synchronization': self.validate_time_synchronization(video_path, json_path)
        }
        
        if rpa_commands:
            validation_results['output'] = self.validate_workflow_output(rpa_commands)
        
        return validation_results
    
    def print_validation_summary(self, validation_results: Dict[str, List[ValidationResult]]):
        """Print a formatted summary of validation results"""
        
        print("\n" + "=" * 60)
        print("🔍 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_errors = 0
        total_warnings = 0
        
        for category, results in validation_results.items():
            print(f"\n📋 {category.upper()}:")
            
            for result in results:
                if result.severity == 'error':
                    icon = "❌"
                    total_errors += 1
                elif result.severity == 'warning':
                    icon = "⚠️"
                    total_warnings += 1
                else:
                    icon = "✅"
                
                print(f"   {icon} {result.message}")
                
                if result.suggestion:
                    print(f"      💡 {result.suggestion}")
        
        print(f"\n📊 SUMMARY:")
        print(f"   • Errors: {total_errors}")
        print(f"   • Warnings: {total_warnings}")
        
        if total_errors == 0:
            print(f"   ✅ Ready for processing!")
        else:
            print(f"   ❌ Please fix errors before proceeding")
        
        print("=" * 60)
        
        return total_errors == 0


def main():
    """Test the validator with sample files"""
    validator = WorkflowValidator()
    
    # Example validation
    video_path = "records/enhanced_multiscreen_20250803_064201.mp4"
    json_path = "records/enhanced_multiscreen_interactions_20250803_064519.json"
    
    results = validator.validate_complete_workflow(video_path, json_path)
    is_valid = validator.print_validation_summary(results)
    
    if is_valid:
        print("✅ All validations passed - ready for RPA generation!")
    else:
        print("❌ Please address the issues above before processing")

if __name__ == "__main__":
    main()