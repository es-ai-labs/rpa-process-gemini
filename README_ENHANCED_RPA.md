# Enhanced Murex RPA Workflow Generator

A sophisticated tool that combines JSON UI interactions with video analysis using Google Gemini to generate contextual, human-readable RPA commands for Murex workflows.

## 🚀 Key Features

- **Video-Aware Analysis**: Uses Gemini's video capabilities to understand UI elements and context
- **Optimized Frame Rate**: Reduced to 0.8 fps for efficient UI processing
- **Contextual Mapping**: Correlates video frames with interaction timestamps  
- **Human-Editable Output**: Structured commands that humans can easily modify
- **Generic Design**: Works across multiple Murex modules and workflows
- **Robust Validation**: Comprehensive input and output validation
- **Cost-Optimized**: Efficient token usage for video processing

## 📁 Project Structure

```
enhanced_murex_rpa_generator.py  # Main enhanced generator
workflow_validator.py           # Validation and error handling
test_enhanced_generator.py     # Testing and demonstration
generic_murex_processor.py     # Original processor (for reference)
rpa_commands_sample/           # Example RPA command formats
```

## 🛠️ Installation & Setup

1. Ensure you have the base dependencies:
   ```bash
   pip install requests
   ```

2. Set up your Google Gemini API key in your environment or config file

3. Ensure you have the base classes:
   - `SimpleRpaGenerator` (parent class)
   - `RpaConfig` (configuration management)

## 🎯 Usage

### Basic Usage

```bash
python enhanced_murex_rpa_generator.py video.mp4 interactions.json
```

### With Validation

```bash
python test_enhanced_generator.py test
```

### Validation Only

```bash
python test_enhanced_generator.py validate video.mp4 interactions.json
```

### Programmatic Usage

```python
from enhanced_murex_rpa_generator import EnhancedMurexRpaGenerator
from workflow_validator import WorkflowValidator

# Validate inputs
validator = WorkflowValidator()
validation_results = validator.validate_complete_workflow(video_path, json_path)
is_valid = validator.print_validation_summary(validation_results)

# Generate workflow
if is_valid:
    generator = EnhancedMurexRpaGenerator()
    commands = generator.process_enhanced_workflow(video_path, json_path)
```

## 📋 Input Requirements

### Video File
- **Format**: MP4, MOV, or AVI
- **Size**: Under 100MB (recommended under 50MB)
- **Content**: UI interactions in Murex application
- **Quality**: Standard resolution sufficient for UI elements

### JSON File
- **Structure**: Must contain `mouse_interactions` and `keyboard_events`
- **Timing**: Synchronized with video recording
- **Content**: Captured user interactions with timestamps

### Example JSON Structure
```json
{
  "session_info": {
    "duration": 120.5
  },
  "mouse_interactions": [
    {
      "type": "mouse_press",
      "button": "left", 
      "timestamp": 5.2,
      "position": {"x": 100, "y": 200}
    }
  ],
  "keyboard_events": [
    {
      "type": "key_press",
      "key_name": "a",
      "timestamp": 6.1,
      "is_character": true
    }
  ]
}
```

## 📤 Output Format

### Generated RPA Commands
The tool generates human-readable commands like:

```
Login to Murex application using username MUREXFO and password MUREX, then click Login button. 
Click on the FO_AM group and click Start. 
On the main page, type 'Revaluation rate curves' in the search field and press Enter. 
In the currency list, type 'ANG' in the search filter and press Enter. 
Double-click on the 'ANG' option in the results list.
```

### Structured Output File
```
# Enhanced Murex RPA Workflow Commands
# Generated: 2025-08-03 12:34:56
# Source Video: workflow_recording.mp4
# Source JSON: workflow_interactions.json
# Processing Mode: Enhanced Video-Aware Analysis
# Total Interactions: 15
# Frame Rate Used: 0.8 fps (optimized for UI)

[Generated RPA commands here]

# END OF WORKFLOW
```

## 🔍 Validation Features

The system validates:

- **Video Files**: Size, format, existence
- **JSON Files**: Structure, content, interaction counts
- **Synchronization**: Video and JSON timing alignment
- **Output Quality**: Command structure and content

### Validation Results
- ✅ **Info**: Normal status updates
- ⚠️ **Warning**: Issues that may affect quality but don't prevent processing
- ❌ **Error**: Critical issues that prevent processing

## 🎛️ Configuration

### Video Processing Settings
```python
ui_video_config = {
    "fps": 0.8,  # Lower frame rate for UI interactions
    "sample_key_moments": True,
    "focus_on_changes": True
}
```

### API Configuration
```python
ui_analysis_config = {
    "temperature": 0.2,  # Lower for consistent UI identification
    "topK": 3,
    "topP": 0.8,
    "maxOutputTokens": 6000,
    "responseMimeType": "text/plain"
}
```

## 🔧 Customization

### Extending for New UI Patterns
1. Modify the `extract_enhanced_interactions()` method
2. Update the prompt in `create_enhanced_prompt()`
3. Adjust validation rules in `workflow_validator.py`

### Changing Output Format
1. Modify `_create_structured_output()` method
2. Update the prompt to specify your desired format
3. Adjust validation rules for new format

## 🚨 Troubleshooting

### Common Issues

**Video too large**
- Compress video or reduce recording duration
- Use lower resolution for UI recordings

**No interactions found**
- Check JSON file structure
- Verify recording captured user actions
- Ensure timing synchronization

**Poor command quality**
- Check video clarity of UI elements
- Verify interaction timing
- Review validation warnings

**API errors**
- Check Gemini API key and quota
- Verify network connectivity
- Check file size limits

## 📊 Performance Optimization

### For Large Workflows
- Break into smaller sections
- Use time windows for processing
- Consider parallel processing for multiple videos

### Cost Optimization
- Reduced frame rate (0.8 fps) saves tokens
- Optimized prompts reduce processing time
- Validation prevents wasted API calls

## 🔄 Migration from Generic Processor

If upgrading from the generic processor:

1. **Backup**: Save existing configurations
2. **Update imports**: Use new enhanced classes
3. **Add validation**: Implement validation checks
4. **Test output**: Verify command quality improvements
5. **Update workflows**: Leverage new contextual features

## 🎯 Best Practices

### Recording Quality
- Ensure clear UI element visibility
- Use consistent timing between actions
- Record complete workflows from start to finish
- Avoid rapid mouse movements

### Processing
- Always validate inputs before processing
- Review generated commands before execution
- Test workflows in sections
- Keep backup of working commands

### Maintenance
- Regularly update prompts for new UI patterns
- Monitor API costs and optimize as needed
- Update validation rules for new requirements
- Document custom modifications

## 📞 Support

For issues or questions:
1. Check validation output for specific error messages
2. Review troubleshooting section
3. Test with sample data
4. Verify input file quality

## 🔮 Future Enhancements

Planned improvements:
- Multi-language support for UI elements
- Advanced workflow pattern recognition
- Integration with more RPA engines
- Real-time validation during recording