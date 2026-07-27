# PasteRich Internal Architecture & Plugin Engine

PasteRich is engineered as a lightweight, cross-platform system daemon that monitors the global clipboard for Markdown and intercepts paste commands to convert them into Rich Text Format (RTF) or CF_HTML natively on the fly.

## Core Philosophy
1. **Zero-Bloat GUI:** PasteRich utilizes `pystray` for a system tray menu and `Tkinter` for lightweight popups. No heavy Electron wrappers or Chromium engines are permitted.
2. **Telemetry-Free:** The core daemon makes zero external network calls. It is completely isolated to the local OS clipboard.
3. **Cross-Platform Native:**
   - **Windows:** Uses `win32clipboard` and injects `CF_HTML`.
   - **macOS:** Uses `pbpaste`/`pbcopy` and `textutil` to inject Apple `«class RTF »`.
   - **Linux:** Uses `xclip`/`xsel` for X11 clipboard manipulation.

## The Dynamic Plugin Engine
To expand functionality into AI and Local RAG (Retrieval-Augmented Generation) without compromising the "Zero-Bloat" philosophy, PasteRich utilizes a Dynamic Plugin Engine.

Plugins are stored in the `plugins/` directory and are **only loaded if explicitly enabled in `config.json`**. 

### Plugin Architecture
A PasteRich plugin must implement a `register(config, paste_rich_module)` function that binds a specific hotkey to a callback function.

```json
{
    "hotkey": "f8",
    "theme": "monokai",
    "plugins": {
        "ai_rewrite": {
            "enabled": true,
            "hotkey": "f9",
            "openai_api_key": "sk-..."
        },
        "mcp_rag": {
            "enabled": true,
            "hotkey": "f10",
            "mcp_server_command": "npx -y @modelcontextprotocol/server-everything"
        }
    }
}
```

### Official Plugins
1. **`ai_rewrite.py` (AI Enhanced Paste)**: Intercepts the clipboard, sends the raw text to OpenAI's API to rewrite it professionally, and utilizes the core `write_clipboard_html` function to paste the AI's response as Rich Text.
2. **`mcp_rag.py` (Local RAG Injection)**: Intercepts specific tags in the clipboard (e.g., `[[Fetch: Architecture]]`), connects to an MCP (Model Context Protocol) server via stdio, fetches the specific data, and pastes it as Rich Text.

## Future Development
- **Odoo XML-RPC Integration**: Future plugins could use the Odoo API to instantly convert highlighted text in any Windows application into an Odoo Helpdesk Ticket or CRM Lead by pressing `Ctrl+Shift+T`.
