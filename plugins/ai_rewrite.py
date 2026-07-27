import urllib.request
import urllib.error
import json
import threading
import keyboard
import time

def ai_enhance_paste(plugin_config, pasterich_core):
    """
    Reads the clipboard, rewrites it professionally via OpenAI,
    and pastes it as Rich Text.
    """
    pasterich_core.logging.info("Triggered AI Rewrite Plugin.")
    
    text = pasterich_core.read_clipboard_text()
    if not text or not text.strip():
        pasterich_core.logging.info("Clipboard empty, AI Rewrite aborted.")
        return
        
    api_key = plugin_config.get("openai_api_key")
    if not api_key:
        pasterich_core.logging.error("OpenAI API key missing in config.")
        return
        
    # Wait for modifiers to be released
    while keyboard.is_pressed('ctrl') or keyboard.is_pressed('shift') or keyboard.is_pressed('alt') or keyboard.is_pressed('windows'):
        time.sleep(0.01)
        
    def worker():
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a professional editor. Rewrite the following text to be highly professional and formatted in clear Markdown. Only return the rewritten text, nothing else."},
                    {"role": "user", "content": text}
                ]
            }
            
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                polished_text = result['choices'][0]['message']['content']
                
            # Process Markdown
            extensions = ['extra', 'codehilite', 'sane_lists', 'pymdownx.magiclink', 'pymdownx.tasklist', 'pymdownx.tilde']
            html = pasterich_core.markdown.markdown(polished_text, extensions=extensions)
            
            pasterich_core.write_clipboard_html(polished_text, html)
            time.sleep(0.1)
            keyboard.send('cmd+v' if pasterich_core.IS_MAC else 'ctrl+v')
            
            # Restore original text
            time.sleep(0.5)
            pasterich_core.write_clipboard_text(text)
            pasterich_core.logging.info("AI Rewrite completed and original clipboard restored.")
            
        except Exception as e:
            pasterich_core.logging.error(f"AI Rewrite failed: {e}")

    threading.Thread(target=worker, daemon=True).start()

def register(plugin_config, pasterich_core):
    hotkey = plugin_config.get("hotkey", "f9")
    keyboard.add_hotkey(hotkey, lambda: ai_enhance_paste(plugin_config, pasterich_core), suppress=True)
