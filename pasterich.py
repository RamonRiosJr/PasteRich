import sys
import os
import re
import time
import threading
import subprocess
import tempfile
import json
import logging
import markdown
import keyboard
import pystray
import webbrowser
import urllib.request
import urllib.error
import shutil
from PIL import Image
from typing import Optional, Dict, Any
__version__ = "1.2.2"

# ---------------------------------------------------------
# OS-Specific Imports and Helpers
# ---------------------------------------------------------

IS_WIN: bool = sys.platform == 'win32'
IS_MAC: bool = sys.platform == 'darwin'
IS_LINUX: bool = sys.platform.startswith('linux')

if IS_WIN:
    import win32clipboard
    import win32con
    import win32com.client

# ---------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------

def get_exe_dir() -> str:
    """Returns the directory of the executable or script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# Setup Logging
log_path: str = os.path.join(get_exe_dir(), 'pasterich.log')
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logging.info("PasteRich starting up...")

def get_config_path() -> str:
    """Returns the path to the configuration JSON file."""
    return os.path.join(get_exe_dir(), 'config.json')

def load_config() -> Dict[str, Any]:
    """Loads configuration from config.json, or creates a default if missing."""
    default_config: Dict[str, Any] = {
        "hotkey": "f8" if IS_WIN else "f8",
        "theme": "monokai",
        "plugins": {},
        "has_run_before": False
    }
    config_path: str = get_config_path()
    
    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            logging.info("Created default config.json")
        except Exception as e:
            logging.error(f"Failed to create default config: {e}")
        return default_config
        
    try:
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            return {**default_config, **user_config}
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return default_config

config: Dict[str, Any] = load_config()

# ---------------------------------------------------------
# Clipboard Operations
# ---------------------------------------------------------

def read_clipboard_text() -> Optional[str]:
    """Reads the current text content from the system clipboard."""
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
            logging.error(f"Failed to read clipboard: {e}")
            return None
    elif IS_MAC:
        try:
            return subprocess.check_output(['pbpaste'], text=True)
        except Exception as e:
            logging.error(f"pbpaste error: {e}")
            return None
    elif IS_LINUX:
        try:
            return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'], text=True)
        except Exception as e:
            try:
                return subprocess.check_output(['xsel', '-b', '-o'], text=True)
            except Exception as e2:
                logging.error(f"Linux clipboard read error: {e2}")
                return None
    return None

def write_clipboard_html(text: str, html: str) -> None:
    """Injects HTML and fallback text into the system clipboard formatting."""
    css: str = ""
    custom_css_path: str = os.path.join(get_exe_dir(), 'style.css')
    if os.path.exists(custom_css_path):
        try:
            with open(custom_css_path, 'r') as f:
                css = f"<style>\n{f.read()}\n</style>\n"
        except Exception as e:
            logging.warning(f"Could not load custom css: {e}")
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
        cf_html_bytes = payload.encode('utf-8') + b'\0'
        
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            win32clipboard.SetClipboardText(text)
            format_id = win32clipboard.RegisterClipboardFormat("HTML Format")
            win32clipboard.SetClipboardData(format_id, cf_html_bytes)
            win32clipboard.CloseClipboard()
            logging.info("Successfully injected CF_HTML into Windows clipboard.")
        except Exception as e:
            logging.error(f"Failed to write clipboard: {e}")
            
    elif IS_MAC:
        try:
            fd, html_path = tempfile.mkstemp(suffix='.html')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(f"<html><head>{css}</head><body>{html}</body></html>")
            
            rtf_path = html_path.replace('.html', '.rtf')
            subprocess.run(['textutil', '-format', 'html', '-convert', 'rtf', html_path], check=True)
            
            script = f'''
            set the clipboard to {{text:"{text.replace('"', '\\"')}", «class RTF »:read POSIX file "{rtf_path}" as «class RTF »}}
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            
            os.remove(html_path)
            os.remove(rtf_path)
            logging.info("Successfully injected RTF into macOS clipboard.")
        except Exception as e:
            logging.error(f"Mac clipboard error: {e}")
            
    elif IS_LINUX:
        try:
            payload = f"<html><head>{css}</head><body>{html}</body></html>"
            subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'text/html', '-i'], input=payload.encode('utf-8'), check=True)
            logging.info("Successfully injected HTML into Linux clipboard via xclip.")
        except Exception as e:
            logging.error(f"Linux xclip error: {e}")

def write_clipboard_text(text: str) -> None:
    """Restores plain text back into the system clipboard."""
    if IS_WIN:
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
        except Exception as e:
            logging.error(f"Failed restoring Windows clipboard text: {e}")
    elif IS_MAC:
        try:
            subprocess.run(['pbcopy'], input=text.encode('utf-8'))
        except Exception as e:
            logging.error(f"Failed restoring Mac clipboard text: {e}")
    elif IS_LINUX:
        try:
            subprocess.run(['xclip', '-selection', 'clipboard', '-i'], input=text.encode('utf-8'))
        except Exception as e:
            logging.error(f"Failed restoring Linux clipboard text: {e}")

# ---------------------------------------------------------
# Markdown Logic
# ---------------------------------------------------------

def is_markdown(text: str) -> bool:
    """Detects if the given text contains markdown syntax."""
    patterns = [
        r'```', r'\*\*', r'__', r'^#+\s', r'^\s*[-*+]\s', r'^\s*\d+\.\s', r'\[.*\]\(.*\)', r'>\s'
    ]
    for p in patterns:
        if re.search(p, text, re.MULTILINE):
            return True
    return False

def paste_rich(icon: Optional[Any] = None, item: Optional[Any] = None) -> None:
    """The main routine: reads markdown, parses it, sets clipboard, and simulates a paste keystroke."""
    logging.info("Triggered PasteRich hotkey.")
    text: Optional[str] = read_clipboard_text()
    if not text or not text.strip():
        logging.info("Clipboard is empty.")
        return
        
    if not is_markdown(text):
        logging.info("No markdown detected, passing through native paste.")
        if not item:
            keyboard.send('cmd+v' if IS_MAC else 'ctrl+v')
        return
        
    # Pre-process: Python's markdown requires a blank line before lists.
    text_processed = re.sub(r'([^\n])\n(\s*[-*+]\s+)', r'\1\n\n\2', text)
    text_processed = re.sub(r'([^\n])\n(\s*\d+\.\s+)', r'\1\n\n\2', text_processed)
        
    extensions = ['extra', 'codehilite', 'sane_lists', 'pymdownx.magiclink', 'pymdownx.tasklist', 'pymdownx.tilde']
    html: str = markdown.markdown(text_processed, extensions=extensions, extension_configs={
        'codehilite': {
            'noclasses': True,
            'pygments_style': config.get("theme", "monokai")
        }
    })
    
    write_clipboard_html(text, html)
    time.sleep(0.1) # Sync clipboard
    
    if not item: 
        # Wait for physical modifiers to be released so they don't taint the paste
        while keyboard.is_pressed('ctrl') or keyboard.is_pressed('shift') or keyboard.is_pressed('alt') or keyboard.is_pressed('windows'):
            time.sleep(0.01)
        keyboard.send('cmd+v' if IS_MAC else 'ctrl+v')
        
    def restore() -> None:
        time.sleep(0.5)
        write_clipboard_text(text)
        logging.info("Original clipboard text restored.")
            
    threading.Thread(target=restore, daemon=True).start()

# ---------------------------------------------------------
# Auto-Start Logic
# ---------------------------------------------------------

def get_startup_path() -> Optional[str]:
    """Resolves the OS-specific path for auto-start configurations."""
    if IS_WIN:
        startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        return os.path.join(startup_dir, 'PasteRich.lnk')
    elif IS_MAC:
        return os.path.expanduser('~/Library/LaunchAgents/com.pasterich.plist')
    elif IS_LINUX:
        return os.path.expanduser('~/.config/autostart/pasterich.desktop')
    return None

def is_startup_enabled(icon: Optional[Any] = None, item: Optional[Any] = None) -> bool:
    """Checks if the application is currently configured to run on startup."""
    path = get_startup_path()
    return os.path.exists(path) if path else False

def toggle_startup(icon: Any, item: Any) -> None:
    """Toggles the auto-start functionality based on the OS."""
    path = get_startup_path()
    if not path:
        return
        
    if os.path.exists(path):
        os.remove(path)
        logging.info(f"Removed startup script at {path}")
    else:
        exe_path = get_exe_dir() if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        exe_full_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        if IS_WIN:
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(path)
                shortcut.Targetpath = exe_full_path
                shortcut.WorkingDirectory = exe_path
                shortcut.IconLocation = exe_full_path
                shortcut.save()
                logging.info(f"Created Windows startup shortcut at {path}")
            except Exception as e:
                logging.error(f"Failed to create shortcut: {e}")
        elif IS_MAC:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pasterich</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_full_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(plist_content)
            logging.info(f"Created macOS LaunchAgent at {path}")
        elif IS_LINUX:
            desktop_content = f"""[Desktop Entry]
Type=Application
Exec={exe_full_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=PasteRich
Comment=Start PasteRich daemon"""
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(desktop_content)
            logging.info(f"Created Linux desktop autostart entry at {path}")

# ---------------------------------------------------------
# Auto-Update Logic
# ---------------------------------------------------------

def cleanup_old_executable() -> None:
    """Removes the old executable left behind by a previous update."""
    if getattr(sys, 'frozen', False) and IS_WIN:
        exe_path = sys.executable
        old_exe_path = f"{exe_path}.old"
        if os.path.exists(old_exe_path):
            try:
                os.remove(old_exe_path)
                logging.info(f"Cleaned up old executable: {old_exe_path}")
            except Exception as e:
                logging.error(f"Failed to cleanup old executable: {e}")

def check_for_updates_wrapper(icon: Optional[Any] = None, item: Optional[Any] = None) -> None:
    threading.Thread(target=check_for_updates, args=(True,), daemon=True).start()

def check_for_updates(manual: bool = False) -> None:
    """Checks the GitHub repository for new releases."""
    repo_url = "https://api.github.com/repos/RamonRiosJr/PasteRich/releases/latest"
    try:
        req = urllib.request.Request(repo_url, headers={'User-Agent': 'PasteRich'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "").lstrip("v")
            
            if not latest_version:
                if manual:
                    show_message_box("Update Check", "Could not determine the latest version.")
                return

            current_tuple = tuple(map(int, __version__.split('.')))
            latest_tuple = tuple(map(int, latest_version.split('.')))

            if latest_tuple > current_tuple:
                logging.info(f"New version found: {latest_version}")
                prompt_update(data, latest_version)
            else:
                if manual:
                    show_message_box("Update Check", f"You are on the latest version ({__version__}).")
                logging.info("Already on the latest version.")
    except Exception as e:
        logging.error(f"Error checking for updates: {e}")
        if manual:
            show_message_box("Update Check", f"Failed to check for updates: {e}")

def prompt_update(release_data: dict, new_version: str) -> None:
    """Prompts the user to update and initiates the download."""
    msg = f"A new version of PasteRich (v{new_version}) is available. Would you like to download and install it now?"
    if show_prompt_box("Update Available", msg):
        threading.Thread(target=perform_update, args=(release_data,), daemon=True).start()

def show_message_box(title: str, msg: str) -> None:
    """Shows a native message box."""
    if IS_WIN:
        ps = f"Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('{msg}', '{title}')"
        subprocess.run(["powershell", "-Command", ps], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
    elif IS_MAC:
        script = f'display dialog "{msg}" with title "{title}" buttons {{"OK"}} default button "OK"'
        subprocess.run(["osascript", "-e", script])

def show_prompt_box(title: str, msg: str) -> bool:
    """Shows a yes/no prompt and returns True if user chose Yes."""
    if IS_WIN:
        ps = f"Add-Type -AssemblyName PresentationFramework; $res = [System.Windows.MessageBox]::Show('{msg}', '{title}', 'YesNo'); if ($res -eq 'Yes') {{ exit 0 }} else {{ exit 1 }}"
        return subprocess.run(["powershell", "-Command", ps], creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0).returncode == 0
    elif IS_MAC:
        script = f'display dialog "{msg}" with title "{title}" buttons {{"Yes", "No"}} default button "Yes"'
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return "button returned:Yes" in res.stdout
    return False

def perform_update(release_data: dict) -> None:
    """Downloads and applies the update."""
    assets = release_data.get("assets", [])
    target_asset = None
    
    # Simple heuristic to pick the right asset based on OS
    for asset in assets:
        name = asset.get("name", "").lower()
        if IS_WIN and name.endswith(".exe"):
            target_asset = asset
            break
        elif IS_MAC and ("mac" in name or "darwin" in name):
            target_asset = asset
            break
        elif IS_LINUX and ("linux" in name):
            target_asset = asset
            break

    if not target_asset:
        logging.error("No suitable asset found for this OS in the latest release.")
        show_message_box("Update Failed", "No suitable asset found for this OS in the latest release.")
        return

    download_url = target_asset.get("browser_download_url")
    logging.info(f"Downloading update from {download_url}...")
    
    try:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, target_asset.get("name"))
        
        req = urllib.request.Request(download_url, headers={'User-Agent': 'PasteRich'})
        with urllib.request.urlopen(req) as response, open(temp_file, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        logging.info("Download complete. Applying update...")
        
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            if IS_WIN:
                old_exe_path = f"{exe_path}.old"
                if os.path.exists(old_exe_path):
                    os.remove(old_exe_path)
                os.rename(exe_path, old_exe_path)
                shutil.copy2(temp_file, exe_path)
            else:
                shutil.copy2(temp_file, exe_path)
                os.chmod(exe_path, 0o755)
                
            logging.info("Update applied. Restarting...")
            subprocess.Popen([exe_path])
            os._exit(0)
        else:
            show_message_box("Update Complete", "PasteRich is running as a script. Update downloaded to temp folder, please apply manually.")
            
    except Exception as e:
        logging.error(f"Failed to perform update: {e}")
        show_message_box("Update Error", f"An error occurred during update: {e}")

def periodic_update_check() -> None:
    """Checks for updates once a day."""
    while True:
        time.sleep(86400) # 24 hours
        check_for_updates(manual=False)

# ---------------------------------------------------------
# App Main
# ---------------------------------------------------------

def create_image() -> Image.Image:
    """Generates or loads the application icon for the system tray."""
    if getattr(sys, 'frozen', False):
        bundled_icon = os.path.join(sys._MEIPASS, 'assets', 'icon.ico')
        if os.path.exists(bundled_icon):
            return Image.open(bundled_icon)
            
    icon_path = os.path.join(get_exe_dir(), 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        return Image.open(icon_path)
        
    logging.warning("No icon.ico found in assets, falling back to generated image.")
    image = Image.new('RGB', (64, 64), color=(138, 43, 226))
    return image

def quit_app(icon: pystray.Icon, item: Any) -> None:
    """Terminates the application."""
    logging.info("Shutting down PasteRich.")
    icon.stop()

def prompt_hotkey_change(icon: pystray.Icon, item: Any) -> None:
    """Spawns a native UI popup to change the hotkey dynamically."""
    default_hotkey = config.get('hotkey', 'f8')
    ps = f"Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.Interaction]::InputBox('Enter new hotkey (e.g., f8):', 'Change Hotkey', '{default_hotkey}')"
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    new_hotkey = result.stdout.strip()
    
    if new_hotkey and new_hotkey.strip():
        new_hotkey = new_hotkey.strip().lower()
        config['hotkey'] = new_hotkey
        
        try:
            with open(get_config_path(), 'w') as f:
                json.dump(config, f, indent=4)
            
            keyboard.unhook_all_hotkeys()
            keyboard.add_hotkey(new_hotkey, paste_rich, suppress=True)
            logging.info(f"Hotkey dynamically changed to {new_hotkey}")
        except Exception as e:
            logging.error(f"Failed to change hotkey: {e}")

def open_url(url: str):
    def inner(icon, item):
        webbrowser.open(url)
    return inner

def show_about_window() -> None:
    import tkinter as tk
    from tkinter import font
    
    root = tk.Tk()
    root.title("About PasteRich")
    root.geometry("450x380")
    root.configure(bg="#0D1117") # Dark mode background
    root.attributes('-topmost', True)
    root.resizable(False, False)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) / 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) / 2
    root.geometry(f"+{int(x)}+{int(y)}")

    title_font = font.Font(family="Segoe UI", size=24, weight="bold")
    tk.Label(root, text="PasteRich", font=title_font, fg="#58A6FF", bg="#0D1117").pack(pady=(30, 5))
    tk.Label(root, text=f"Version {__version__} | Daemon Active", font=("Segoe UI", 10), fg="#8B949E", bg="#0D1117").pack()
    tk.Label(root, text="The ultimate cross-platform Markdown clipboard daemon.", 
             font=("Segoe UI", 10), fg="#C9D1D9", bg="#0D1117", wraplength=350, justify="center").pack(pady=(15, 20))
             
    btn_style = {"bg": "#21262D", "fg": "#C9D1D9", "activebackground": "#30363D", "activeforeground": "#FFFFFF", 
                 "font": ("Segoe UI", 10, "bold"), "relief": "flat", "cursor": "hand2", "width": 25, "bd": 0, "pady": 5}
                 
    tk.Button(root, text="How To / Documentation", command=lambda: webbrowser.open("https://github.com/RamonRiosJr/PasteRich?tab=readme-ov-file"), **btn_style).pack(pady=5)
    tk.Button(root, text="Developer: RamonRios.net", command=lambda: webbrowser.open("https://ramonrios.net"), **btn_style).pack(pady=5)
    tk.Button(root, text="Support Helpdesk", command=lambda: webbrowser.open("https://ramonrios.net/helpdesk"), **btn_style).pack(pady=5)
    tk.Button(root, text="MIT License", command=lambda: webbrowser.open("https://github.com/RamonRiosJr/PasteRich?tab=MIT-1-ov-file"), **btn_style).pack(pady=5)
    
    root.mainloop()

def show_about(icon: pystray.Icon, item: Any) -> None:
    threading.Thread(target=show_about_window, daemon=True).start()

def show_welcome_window() -> None:
    import tkinter as tk
    from tkinter import font
    
    root = tk.Tk()
    root.title("Welcome to PasteRich")
    root.geometry("450x450")
    root.configure(bg="#0D1117")
    root.attributes('-topmost', True)
    root.resizable(False, False)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) / 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) / 2
    root.geometry(f"+{int(x)}+{int(y)}")

    title_font = font.Font(family="Segoe UI", size=24, weight="bold")
    tk.Label(root, text="Welcome to PasteRich!", font=title_font, fg="#58A6FF", bg="#0D1117").pack(pady=(30, 5))
    
    hotkey = config.get("hotkey", "f8")
    tk.Label(root, text=f"Your current hotkey is: {hotkey.upper()}", font=("Segoe UI", 12, "bold"), fg="#C9D1D9", bg="#0D1117").pack(pady=(10, 5))
    
    tk.Label(root, text="Instructions:", font=("Segoe UI", 12, "underline"), fg="#8B949E", bg="#0D1117").pack(pady=(10, 0))
    tk.Label(root, text=f"1. Copy any Markdown text.\n2. Press {hotkey.upper()} to paste it as rich formatted text.\n3. Check the system tray icon for more options and settings.", 
             font=("Segoe UI", 10), fg="#C9D1D9", bg="#0D1117", wraplength=350, justify="left").pack(pady=(5, 15))
             
    # Check update status
    lbl_update = tk.Label(root, text="Checking for updates...", font=("Segoe UI", 10, "italic"), fg="#8B949E", bg="#0D1117")
    lbl_update.pack(pady=(10, 5))
    
    btn_style = {"bg": "#21262D", "fg": "#C9D1D9", "activebackground": "#30363D", "activeforeground": "#FFFFFF", 
                 "font": ("Segoe UI", 10, "bold"), "relief": "flat", "cursor": "hand2", "width": 15, "bd": 0, "pady": 5}
                 
    update_btn = tk.Button(root, text="Download Update", bg="#238636", fg="#ffffff", activebackground="#2EA043", 
                           activeforeground="#FFFFFF", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", width=20, bd=0, pady=5)

    def check_updates_bg():
        repo_url = "https://api.github.com/repos/RamonRiosJr/PasteRich/releases/latest"
        try:
            req = urllib.request.Request(repo_url, headers={'User-Agent': 'PasteRich'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "").lstrip("v")
                
                if latest_version:
                    current_tuple = tuple(map(int, __version__.split('.')))
                    latest_tuple = tuple(map(int, latest_version.split('.')))
                    if latest_tuple > current_tuple:
                        lbl_update.config(text=f"Update Available: v{latest_version}", fg="#3FB950", font=("Segoe UI", 10, "bold"))
                        update_btn.config(command=lambda: [root.destroy(), threading.Thread(target=perform_update, args=(data,), daemon=True).start()])
                        update_btn.pack(pady=5)
                        return
                lbl_update.config(text=f"PasteRich is up to date (v{__version__}).", fg="#8B949E", font=("Segoe UI", 10))
        except Exception as e:
            logging.error(f"Error checking updates on welcome screen: {e}")
            lbl_update.config(text="Could not check for updates.")

    threading.Thread(target=check_updates_bg, daemon=True).start()
    
    tk.Button(root, text="Get Started", command=root.destroy, **btn_style).pack(pady=(15, 20))
    root.mainloop()

def show_welcome(icon: Optional[pystray.Icon] = None, item: Optional[Any] = None) -> None:
    threading.Thread(target=show_welcome_window, daemon=True).start()

def load_plugins() -> None:
    """Dynamically loads and registers enabled plugins from the plugins/ directory."""
    plugins_cfg = config.get("plugins", {})
    if not plugins_cfg:
        return
        
    plugins_dir = os.path.join(get_exe_dir(), 'plugins')
    if not os.path.exists(plugins_dir):
        return
        
    if plugins_dir not in sys.path:
        sys.path.insert(0, plugins_dir)
        
    import importlib
    for plugin_name, p_config in plugins_cfg.items():
        if p_config.get("enabled", False):
            try:
                module = importlib.import_module(plugin_name)
                # Pass the plugin-specific config and a reference to the main pasterich module
                module.register(p_config, sys.modules[__name__])
                logging.info(f"Successfully loaded and registered plugin: {plugin_name}")
            except Exception as e:
                logging.error(f"Failed to load plugin {plugin_name}: {e}")

def rebind_hotkey(icon: Optional[Any] = None, item: Optional[Any] = None) -> None:
    """Refreshes the hotkey binding."""
    try:
        hotkey = config.get("hotkey", 'f8' if IS_WIN else 'f8')
        keyboard.unhook_all_hotkeys()
        keyboard.add_hotkey(hotkey, paste_rich, suppress=True)
        logging.info(f"Successfully rebound hotkey: {hotkey}")
    except Exception as e:
        logging.error(f"Failed to rebind hotkey: {e}")

def periodic_refresh() -> None:
    """Periodically refreshes the hotkey binding to prevent it from dropping."""
    while True:
        time.sleep(600)  # Refresh every 10 minutes
        try:
            rebind_hotkey()
        except Exception:
            pass

def main() -> None:
    if "--paste" in sys.argv:
        paste_rich()
        sys.exit(0)

    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem(lambda text: f"Hotkey: {config.get('hotkey')}", lambda icon, item: None, enabled=False),
        pystray.MenuItem('Paste Rich', paste_rich),
        pystray.MenuItem('Change Hotkey', prompt_hotkey_change),
        pystray.MenuItem('Refresh Hotkey', rebind_hotkey),
        pystray.MenuItem('Check for Updates', check_for_updates_wrapper),
        pystray.MenuItem('Run on Startup', toggle_startup, checked=is_startup_enabled),
        pystray.MenuItem(pystray.Menu.SEPARATOR, None),
        pystray.MenuItem('About PasteRich', show_about),
        pystray.MenuItem('How To / Docs', open_url("https://github.com/RamonRiosJr/PasteRich?tab=readme-ov-file")),
        pystray.MenuItem('Support', open_url("https://ramonrios.net/helpdesk")),
        pystray.MenuItem('License', open_url("https://github.com/RamonRiosJr/PasteRich?tab=MIT-1-ov-file")),
        pystray.MenuItem('Developer', open_url("https://ramonrios.net")),
        pystray.MenuItem(pystray.Menu.SEPARATOR, None),
        pystray.MenuItem('Quit', quit_app)
    )
    
    icon = pystray.Icon("PasteRich", image, "PasteRich", menu)
    
    # Clean up old executable on startup
    cleanup_old_executable()
    
    # Start background threads
    threading.Thread(target=periodic_refresh, daemon=True).start()
    threading.Thread(target=periodic_update_check, daemon=True).start()
    
    try:
        hotkey = config.get("hotkey", 'f8' if IS_WIN else 'f8')
        keyboard.add_hotkey(hotkey, paste_rich, suppress=True)
        logging.info(f"Successfully bound hotkey: {hotkey}")
        
        # Load external plugins after main hotkey is bound
        load_plugins()
        
        # Check for first run
        if not config.get("has_run_before", False):
            config["has_run_before"] = True
            try:
                with open(get_config_path(), 'w') as f:
                    json.dump(config, f, indent=4)
                show_welcome()
            except Exception as e:
                logging.error(f"Failed to save first run state: {e}")
                
    except Exception as e:
        logging.error(f"Failed to bind hotkey: {e}")
        
    icon.run()

if __name__ == '__main__':
    main()
