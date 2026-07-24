# PasteRich Markdown Test Suite

Use this file to test all the markdown features supported by PasteRich. Simply copy any section below (or the whole document) and press `F8` in your target application (like Word, Outlook, or Teams).

---

## 1. Headers

# H1: Giant Header
## H2: Large Header
### H3: Medium Header
#### H4: Small Header
##### H5: Tiny Header
###### H6: Tiniest Header

---

## 2. Text Formatting

This is a paragraph with **bold text**, *italic text*, and ***bold italic text***.
You can also use __underlines__ for bolding in some editors, but standard markdown treats it as bold.

Here is some `inline code` within a standard paragraph.

---

## 3. Lists (The one we just fixed!)

### Bulleted List
*   **Item 1:** This is the first item.
*   **Item 2:** This is the second item.
    *   *Nested Item A:* You can indent lists.
    *   *Nested Item B:* Like this.
*   **Item 3:** The third item.

### Numbered List
1. Step One
2. Step Two
3. Step Three

---

## 4. Code Blocks with Syntax Highlighting

Thanks to the `Pygments` integration, this Python code should paste with a beautiful dark Monokai theme!

```python
def fetch_data(url: str) -> dict:
    """Fetches data from an API."""
    import requests
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch"}
```

```javascript
// A quick JavaScript test
const greet = (name) => {
  console.log(`Hello, ${name}!`);
};
greet("Anish");
```

---

## 5. Tables (Supported by the 'extra' extension)

| Feature | Status | Priority |
| :--- | :---: | ---: |
| Smart Detection | **Active** | High |
| Code Highlighting | **Active** | Medium |
| Teleportation | *Pending* | Low |

---

## 6. Blockquotes

> "The advance of technology is based on making it fit in so that you don't really even notice it, so it's part of everyday life." 
> — Bill Gates
>
> > You can also nest quotes!

---

## 7. Links and Images

*   **Link:** [Check out my GitHub](https://github.com/)
*   **Image:** 
![Cute Dog](https://images.unsplash.com/photo-1517849845537-4d257902454a?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&q=80)

---

## 8. Definition Lists (Supported by 'extra')

PasteRich
: A lightweight background daemon for Windows.
: Built in Python.

Markdown
: A lightweight markup language for creating formatted text.

---

## 9. Footnotes (Supported by 'extra')

This is a statement that requires a footnote.[^1] 

[^1]: This is the footnote text that will appear at the bottom of the pasted document!
