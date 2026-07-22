# PasteRich

A lightweight background daemon for Windows that allows you to paste Markdown text as Rich Text (HTML) into any application (Word, Outlook, Google Docs, etc.) using a global hotkey.

## Features
- Background system tray app (no heavy UI).
- Global hotkey interception (Defaults to `Ctrl+Win+V` to avoid conflicting with standard plain-text pasting).
- Native Windows `CF_HTML` clipboard injection.
- Zero-dependency standalone executable.

## How it works
1. Copy raw Markdown to your clipboard.
2. Press `Ctrl+Win+V` in your target application.
3. PasteRich converts the markdown to HTML, wraps it in a Windows-compatible clipboard header, injects it into the clipboard, and simulates a paste keystroke!

## Configuration
When you run the script or executable for the first time, it will generate a `config.json` file in the same directory.
You can edit this file to customize your hotkey and code highlighting theme:
```json
{
    "hotkey": "ctrl+win+v",
    "theme": "monokai"
}
```

## Building
To build a standalone executable from source, ensure you have Python installed, then run:

```powershell
# Install requirements
pip install markdown keyboard pystray pywin32 pyinstaller pillow

# Run the build script
python build.py
```

The resulting `PasteRich.exe` will be found in the `dist` folder.
