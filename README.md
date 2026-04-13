# Docs Writer - macOS Typing Simulator

## Overview
Docs Writer is a lightweight macOS application built with Python (tkinter + Quartz CGEvents) that automatically types text character-by-character into any application. It simulates human-like typing behavior with randomized delays, pauses, occasional fast bursts, and a freeze effect that mimics natural thinking patterns.

## Features
- **Human-like Typing Simulation**: Generates realistic typing patterns with random delays between characters
- **Advanced Pause System**: Configurable pauses after words, sentences, and paragraphs
- **Freeze Effect**: Simulates human thinking with random pauses (configurable chance, min/max duration)
- **Occasional Speed Bursts**: Realistic typing variations including sudden fast typing
- **User-Friendly GUI**: Built with tkinter featuring:
  - Text input area for content to be typed
  - Start/Stop/Clear control buttons
  - ttk.Spinbox controls for freeze effect configuration (percentage chance, min/max duration in seconds)
- **Global Keyboard Shortcut**: ESC key stops typing globally via pynput Listener
- **Background Threading**: Typing runs in a background thread, UI updates via root.after()

## Requirements
- macOS
- Python 3.x
- Accessibility permissions enabled in macOS System Settings

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Lukynss/docs_writer.git
cd docs_writer
```

2. **Set up virtual environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Grant Accessibility Permissions**:
   - Open System Settings → Privacy & Security → Accessibility
   - Add Terminal or your Python IDE to the allowed apps list

## Usage

Run the application:
```bash
.venv/bin/python docs_writer.py
```

### How to Use
1. Paste or type the text you want to be automatically typed into the text field
2. Click in the target application where you want the text to appear
3. Press the **Start** button in Docs Writer
4. The application will begin typing with human-like patterns
5. Press **Stop** to pause or **ESC** to stop globally
6. Use **Clear** to reset the text field

### Configuration
Use the GUI controls to adjust:
- **Freeze Chance (%)**: Probability of random pauses occurring
- **Freeze Min (sec)**: Minimum duration of pause effect
- **Freeze Max (sec)**: Maximum duration of pause effect

## Development

### Building with py2app
The `setup.py` file is configured for creating a standalone macOS application bundle:
```bash
python setup.py py2app
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please feel free to submit issues and pull requests.

## Support
For issues or questions, please open an issue on the GitHub repository.