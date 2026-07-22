import sys
import os
import re
import time
import threading
import subprocess
import tempfile
import json
import markdown
import keyboard
import pystray
from PIL import Image

# ---------------------------------------------------------
# OS-Specific Imports and Helpers
# ---------------------------------------------------------

IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

if IS_WIN:
    import win32clipboard
    import win32con
    import win32com.client

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    return os.path.join(get_exe_dir(), 'config.json')

def load_config():
    default_config = {
        "hotkey": "ctrl+win+v" if IS_WIN else "cmd+ctrl+v",
        "theme": "monokai"
    }
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
        except Exception as e:
            print(f"Failed to create default config: {e}")
        return default_config
        
    try:
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            # Merge with defaults
            return {**default_config, **user_config}
    except Exception as e:
        print(f"Failed to load config: {e}")
        return default_config

config = load_config()

# ---------------------------------------------------------
# Clipboard Operations
# ---------------------------------------------------------

def read_clipboard_text():
    if IS_WIN:
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                text = win32clipboard.GetClipboardData(win32con.CF_TEXT).decode('utf-8')
            else:
                text = None
            win32clipboard.CloseClipboard()
            return text
        except Exception as e:
            print(f"Failed to read clipboard: {e}")
            return None
    elif IS_MAC:
        try:
            return subprocess.check_output(['pbpaste'], text=True)
        except:
            return None
    elif IS_LINUX:
        try:
            # Try xclip first
            return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'], text=True)
        except:
            try:
                # Fallback to xsel
                return subprocess.check_output(['xsel', '-b', '-o'], text=True)
            except:
                return None

def write_clipboard_html(text, html):
    # Try to load custom CSS or use default GitHub style
    css = ""
    custom_css_path = os.path.join(get_exe_dir(), 'style.css')
    if os.path.exists(custom_css_path):
        try:
            with open(custom_css_path, 'r') as f:
                css = f"<style>\n{f.read()}\n</style>\n"
        except: pass
    else:
        css = """
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.5; color: #1F2328; }
pre { background-color: #f6f8fa; border-radius: 6px; padding: 16px; overflow: auto; }
code { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; background-color: rgba(175,184,193,0.2); padding: 0.2em 0.4em; border-radius: 6px; font-size: 85%; }
pre code { background-color: transparent; padding: 0; }
blockquote { padding: 0 1em; color: #656d76; border-left: 0.25em solid #d0d7de; margin: 0; }
table { border-collapse: collapse; margin-bottom: 16px; }
table th, table td { padding: 6px 13px; border: 1px solid #d0d7de; }
table tr:nth-child(2n) { background-color: #f6f8fa; }
</style>
"""

    if IS_WIN:
        # Format for Windows CF_HTML
        prefix = (
            "Version:0.9\r\n"
            "StartHTML:{0:09d}\r\n"
            "EndHTML:{1:09d}\r\n"
            "StartFragment:{2:09d}\r\n"
            "EndFragment:{3:09d}\r\n"
        )
        html_prefix = f"<html>\r\n<head>\r\n{css}</head>\r\n<body>\r\n<!--StartFragment-->\r\n"
        html_suffix = "\r\n<!--EndFragment-->\r\n</body>\r\n</html>"
        
        prefix_len = len(prefix.format(0,0,0,0).encode('utf-8'))
        html_prefix_len = len(html_prefix.encode('utf-8'))
        fragment_len = len(html.encode('utf-8'))
        html_suffix_len = len(html_suffix.encode('utf-8'))
        
        start_html = prefix_len
        start_fragment = start_html + html_prefix_len
        end_fragment = start_fragment + fragment_len
        end_html = end_fragment + html_suffix_len
        
        header = prefix.format(start_html, end_html, start_fragment, end_fragment)
        payload = header + html_prefix + html + html_suffix
        cf_html_bytes = payload.encode('utf-8')
        
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            win32clipboard.SetClipboardText(text)
            format_id = win32clipboard.RegisterClipboardFormat("HTML Format")
            win32clipboard.SetClipboardData(format_id, cf_html_bytes)
            win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"Failed to write clipboard: {e}")
            
    elif IS_MAC:
        # Mac requires RTF via textutil and osascript to set clipboard natively without pyobjc
        try:
            # 1. Write HTML to temp file
            fd, html_path = tempfile.mkstemp(suffix='.html')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(f"<html><body>{html}</body></html>")
            
            # 2. Convert to RTF via textutil
            rtf_path = html_path.replace('.html', '.rtf')
            subprocess.run(['textutil', '-format', 'html', '-convert', 'rtf', html_path], check=True)
            
            # 3. Inject to clipboard using AppleScript
            # The POSIX file path must be passed properly.
            script = f'''
            set the clipboard to {{text:"{text.replace('"', '\\"')}", «class RTF »:read POSIX file "{rtf_path}" as «class RTF »}}
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            
            # Cleanup
            os.remove(html_path)
            os.remove(rtf_path)
        except Exception as e:
            print(f"Mac clipboard error: {e}")
            
    elif IS_LINUX:
        # Linux xclip supports HTML natively
        try:
            subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'text/html', '-i'], input=html.encode('utf-8'), check=True)
        except:
            print("Linux xclip error or not installed.")

def write_clipboard_text(text):
    if IS_WIN:
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
        except:
            pass
    elif IS_MAC:
        try:
            subprocess.run(['pbcopy'], input=text.encode('utf-8'))
        except:
            pass
    elif IS_LINUX:
        try:
            subprocess.run(['xclip', '-selection', 'clipboard', '-i'], input=text.encode('utf-8'))
        except:
            pass

# ---------------------------------------------------------
# Markdown Logic
# ---------------------------------------------------------

def is_markdown(text):
    patterns = [
        r'```', r'\*\*', r'__', r'^#+\s', r'^\s*[-*+]\s', r'^\s*\d+\.\s', r'\[.*\]\(.*\)', r'>\s'
    ]
    for p in patterns:
        if re.search(p, text, re.MULTILINE):
            return True
    return False

def paste_rich(icon=None, item=None):
    text = read_clipboard_text()
    if not text or not text.strip():
        return
        
    # Smart Detection
    if not is_markdown(text):
        if not item:
            keyboard.send('cmd+v' if IS_MAC else 'ctrl+v')
        return
        
    # Pre-process: Python's markdown requires a blank line before lists.
    text_processed = re.sub(r'([^\n])\n(\s*[-*+]\s+)', r'\1\n\n\2', text)
    text_processed = re.sub(r'([^\n])\n(\s*\d+\.\s+)', r'\1\n\n\2', text_processed)
        
    # Convert markdown to HTML
    extensions = ['extra', 'codehilite', 'sane_lists', 'pymdownx.magiclink', 'pymdownx.tasklist', 'pymdownx.tilde']
    html = markdown.markdown(text_processed, extensions=extensions, extension_configs={
        'codehilite': {
            'noclasses': True,
            'pygments_style': config.get("theme", "monokai")
        }
    })
    
    write_clipboard_html(text, html)
    
    time.sleep(0.1) # Sync clipboard
    
    # Simulate paste
    if not item: 
        keyboard.send('cmd+v' if IS_MAC else 'ctrl+v')
        
    # Restore clipboard in background
    def restore():
        time.sleep(0.5)
        write_clipboard_text(text)
            
    threading.Thread(target=restore, daemon=True).start()

# ---------------------------------------------------------
# Auto-Start Logic
# ---------------------------------------------------------

def get_exe_path():
    return sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)

def get_startup_path():
    if IS_WIN:
        startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        return os.path.join(startup_dir, 'PasteRich.lnk')
    elif IS_MAC:
        return os.path.expanduser('~/Library/LaunchAgents/com.pasterich.plist')
    elif IS_LINUX:
        return os.path.expanduser('~/.config/autostart/pasterich.desktop')
    return None

def is_startup_enabled(icon=None, item=None):
    path = get_startup_path()
    return os.path.exists(path) if path else False

def toggle_startup(icon, item):
    path = get_startup_path()
    if not path:
        return
        
    if os.path.exists(path):
        os.remove(path)
    else:
        exe_path = get_exe_path()
        if IS_WIN:
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = exe_path
                shortcut.save()
            except Exception as e:
                print(f"Failed to create shortcut: {e}")
        elif IS_MAC:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pasterich</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(plist_content)
        elif IS_LINUX:
            desktop_content = f"""[Desktop Entry]
Type=Application
Exec={exe_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=PasteRich
Comment=Start PasteRich daemon"""
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(desktop_content)

# ---------------------------------------------------------
# App Main
# ---------------------------------------------------------

def create_image():
    if getattr(sys, 'frozen', False):
        # PyInstaller bundles data in sys._MEIPASS
        bundled_icon = os.path.join(sys._MEIPASS, 'assets', 'icon.ico')
        if os.path.exists(bundled_icon):
            return Image.open(bundled_icon)
            
    icon_path = os.path.join(get_exe_dir(), 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        return Image.open(icon_path)
        
    image = Image.new('RGB', (64, 64), color=(138, 43, 226))
    return image

def quit_app(icon, item):
    icon.stop()

def main():
    # Handle manual CLI execution (e.g. for Linux binding)
    if "--paste" in sys.argv:
        paste_rich()
        sys.exit(0)

    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem('Paste Rich', paste_rich),
        pystray.MenuItem('Run on Startup', toggle_startup, checked=is_startup_enabled),
        pystray.MenuItem('Quit', quit_app)
    )
    
    icon = pystray.Icon("PasteRich", image, "PasteRich", menu)
    
    try:
        hotkey = config.get("hotkey", 'ctrl+win+v' if IS_WIN else 'cmd+ctrl+v')
        keyboard.add_hotkey(hotkey, paste_rich, suppress=True)
        print(f"Listening on {hotkey}")
    except Exception as e:
        print(f"Failed to bind hotkey (sudo required on Linux?): {e}")
        print("Run with --paste argument to trigger manually if background hotkey fails.")
        
    icon.run()

if __name__ == '__main__':
    main()
