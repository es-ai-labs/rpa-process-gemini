# RPA Process Gemini

Enhanced RPA Process Generator using Gemini AI for Murex workflows - Screen recording and video processing with AI-powered workflow generation.

## 🚀 Features

- **Multi-Screen Recording**: Capture screen interactions with visual highlights
- **AI-Powered Analysis**: Uses Google Gemini to analyze video and generate RPA commands
- **Complete Video Processing**: Ensures no workflow steps are missed
- **Enhanced UI Detection**: Contextual understanding of UI elements
- **Workflow Validation**: Comprehensive input and output validation
- **Human-Readable Output**: Structured commands that humans can easily modify

## 📁 Project Structure

```
├── enhanced_rpa_recorder_multiscreen_fixed.py  # Main screen recorder
├── complete_video_processor.py                 # Main video processor
├── enhanced_murex_rpa_generator.py            # Enhanced RPA generator
├── simple_rpa_generator.py                    # Base RPA generator
├── workflow_validator.py                      # Validation system
├── rpa_config.py                              # Configuration management
├── requirements.txt                           # Dependencies
├── records/                                   # Video recordings and interaction data
├── generated_rpa_commands/                    # Output RPA commands
└── rpa_commands_sample/                       # Sample command formats
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/es-ai-labs/rpa-process-gemini.git
   cd rpa-process-gemini
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file with your Gemini API key:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

## 🎯 Usage

### 1. Screen Recording
```bash
python enhanced_rpa_recorder_multiscreen_fixed.py
```
- Records screen interactions with visual highlights
- Captures mouse clicks, keyboard input, and app switches
- Saves video and interaction data to `records/` folder

### 2. Video Processing
```bash
python complete_video_processor.py
```
- Processes recorded videos using Gemini AI
- Generates human-readable RPA commands
- Outputs structured workflow files to `generated_rpa_commands/`

## 🔧 Configuration

Edit `rpa_config.py` to customize:
- API settings and timeouts
- Video processing parameters
- Output directory paths
- Processing limits

## 📋 Requirements

- Python 3.8+
- Google Gemini API key
- macOS (for screen recording features)
- See `requirements.txt` for full dependency list

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Repository**: https://github.com/es-ai-labs/rpa-process-gemini
- **Issues**: https://github.com/es-ai-labs/rpa-process-gemini/issues

## 📝 Notes

- The `development_iterations_backup.zip` contains all development iterations and experimental code
- Video files in `records/` are examples of recorded workflows
- Generated RPA commands in `generated_rpa_commands/` show the AI output format
