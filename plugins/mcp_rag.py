import subprocess
import json
import threading
import keyboard
import time
import re

def mcp_rag_paste(plugin_config, pasterich_core):
    """
    Reads the clipboard for a fetch tag, queries a local MCP server,
    and pastes the returned context as Rich Text.
    Example tag: [[Fetch: Server Config]]
    """
    pasterich_core.logging.info("Triggered MCP RAG Plugin.")
    
    text = pasterich_core.read_clipboard_text()
    if not text or not text.strip():
        return
        
    match = re.search(r'\[\[Fetch:\s*(.*?)\]\]', text, re.IGNORECASE)
    if not match:
        pasterich_core.logging.info("No [[Fetch: ...]] tag found in clipboard.")
        return
        
    query = match.group(1)
    mcp_command = plugin_config.get("mcp_server_command")
    if not mcp_command:
        pasterich_core.logging.error("mcp_server_command missing in config.")
        return
        
    while keyboard.is_pressed('ctrl') or keyboard.is_pressed('shift') or keyboard.is_pressed('alt') or keyboard.is_pressed('windows'):
        time.sleep(0.01)
        
    def worker():
        try:
            # Here we spawn the MCP server via stdio and send a JSON-RPC request.
            # (In a full implementation, you'd use the mcp SDK, but for a lightweight daemon, 
            # we send a raw JSON-RPC payload to standard input and read standard output)
            
            # This is a conceptual standard MCP tool execution via stdio
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "search_knowledge_base",
                    "arguments": {"query": query}
                }
            }
            
            process = subprocess.Popen(
                mcp_command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send RPC payload
            stdout, stderr = process.communicate(input=json.dumps(rpc_payload) + "\n", timeout=10)
            
            # Parse response (assuming server returns standard MCP JSON-RPC response)
            response = json.loads(stdout.strip())
            retrieved_text = response.get('result', {}).get('content', [{"text": f"Error: No results found for '{query}'"}])[0]['text']
            
            # Replace tag in original text with retrieved data
            final_text = text.replace(match.group(0), retrieved_text)
            
            extensions = ['extra', 'codehilite', 'sane_lists']
            html = pasterich_core.markdown.markdown(final_text, extensions=extensions)
            
            pasterich_core.write_clipboard_html(final_text, html)
            time.sleep(0.1)
            keyboard.send('cmd+v' if pasterich_core.IS_MAC else 'ctrl+v')
            
            time.sleep(0.5)
            pasterich_core.write_clipboard_text(text)
            
        except Exception as e:
            pasterich_core.logging.error(f"MCP RAG execution failed: {e}")

    threading.Thread(target=worker, daemon=True).start()

def register(plugin_config, pasterich_core):
    hotkey = plugin_config.get("hotkey", "f10")
    keyboard.add_hotkey(hotkey, lambda: mcp_rag_paste(plugin_config, pasterich_core), suppress=True)
