# WriteBetter

A lightweight desktop utility that rewrites selected text using an LLM of your choice. Select any text, press a hotkey, and get multiple rewrite variants in a popup — then click one to paste it back instantly.

Works on **Windows** and **macOS**.

---

## How it works

1. Select text in any app (browser, email, editor, anything)
2. Press the hotkey (`Ctrl+Shift+F9` by default)
3. A popup appears with rewrite variants
4. Click a variant to paste it back, or press `1` / `2` / `3` on the keyboard

---

## Requirements

### All platforms
- **Python 3.12 or later** — [python.org/downloads](https://www.python.org/downloads/)
- **uv** — fast Python package manager (replaces pip + venv)
- **An API key** for at least one supported provider (see providers list below)

### Windows
- Windows 10 or Windows 11
- No additional system dependencies

### macOS
- macOS 12 (Monterey) or later
- **Accessibility permission** — required for the hotkey to work (the system will prompt you on first run; you can also grant it manually in System Settings → Privacy & Security → Accessibility)

---

## Supported providers

| Provider | Model (default) | Get a key |
|---|---|---|
| OpenAI | gpt-4o-mini | platform.openai.com |
| Anthropic | claude-sonnet-4-5 | console.anthropic.com |
| Google Gemini | gemini-2.5-flash | aistudio.google.com |
| OpenRouter | claude-sonnet-4-5 | openrouter.ai |
| NVIDIA NIM | llama-3.3-70b-instruct | build.nvidia.com |
| Ollama (local) | llama3.1:8b | ollama.com (free, runs locally) |

You only need a key for the provider you want to use. Ollama requires no key.

---

## Installation

### Step 1 — Install uv

**Windows** (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS** (Terminal):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal after installing.

---

### Step 2 — Download the project

```bash
git clone https://github.com/your-username/writebetter.git
cd writebetter
```

Or download and unzip the project folder, then open a terminal in it.

---

### Step 3 — Install dependencies

```bash
uv sync
```

This creates a virtual environment and installs everything automatically. It takes about 1–2 minutes the first time.

---

### Step 4 — Run the app

**Windows:**
```bash
uv run python main.py
```

**macOS:**
```bash
uv run python main.py
```

The app starts in the background. Look for the **W** icon in:
- Windows: system tray (bottom-right, near the clock)
- macOS: menu bar (top-right)

---

### Step 5 — Add your API key

1. Right-click the tray/menu bar icon → **Settings**
2. Find your provider under **API Keys**
3. Paste your key and click **Save**
4. The app restarts automatically

API keys are stored securely in the OS credential store (Windows Credential Manager on Windows, Keychain on macOS) — never in any file.

---

## Building a Windows executable

You can produce a standalone `WriteBetter.exe` that runs without Python or uv installed. The output is a folder (~660 MB, mostly Qt) that you can copy anywhere.

### Prerequisites

Install dependencies first (including the dev build tool):

```bash
uv sync
```

### Build

```bash
uv run pyinstaller writebetter.spec --noconfirm
```

Output lands in `dist\WriteBetter\`. That folder contains:

```
dist\WriteBetter\
├── WriteBetter.exe   ← double-click to run
├── config.json       ← your settings
└── _internal\        ← Qt DLLs, Python runtime (don't touch)
```

### Run the built exe

Double-click `WriteBetter.exe`, or from a terminal:

```bash
.\dist\WriteBetter\WriteBetter.exe
```

Look for the **W** icon in the system tray (bottom-right, near the clock).

### Notes

- API keys are stored in **Windows Credential Manager**, not in the folder. Re-enter them via Settings if you copy the folder to a different machine.
- The `build\` and `dist\` folders are git-ignored — don't commit them.
- To rebuild after a code change, run the same `pyinstaller` command again. The `--noconfirm` flag overwrites the previous build without prompting.

---

## Configuration

Settings are in `config.json` in the project folder. The Settings UI covers the most common options. You can also edit the file directly:

| Setting | Default | Description |
|---|---|---|
| `trigger` | `hotkey` | `hotkey` fires on the configured key combo; `ctrl_c` fires on every copy |
| `hotkey` | `<ctrl>+<shift>+<f9>` | Key combo (edit via Settings UI) |
| `num_variants` | `3` | How many rewrites to generate (1–9) |
| `active_provider` | `openai` | Which provider to use |
| `default_instructions` | Keep my meaning... | Default rewrite instruction |

Per-provider settings (edit `config.json` directly):

| Setting | Default | Description |
|---|---|---|
| `timeout` | `60` | Request timeout in seconds (NVIDIA NIM may need `180`) |

---

## Project structure

```
writebetter/
├── main.py                  # Entry point — starts tray, hotkey listener, Qt app
├── config.json              # App settings (not API keys)
├── config.example.json      # Reference copy of config with comments
├── pyproject.toml           # Python project metadata and dependencies
│
├── core/
│   ├── config.py            # Load/save config, build provider instances
│   ├── variants.py          # Prompt construction, LLM call, parse variants
│   └── providers/
│       ├── base.py          # Abstract Provider interface
│       ├── openai_compat.py # OpenAI-compatible endpoint (OpenAI, Google, OpenRouter, NVIDIA, Ollama)
│       └── anthropic.py     # Anthropic native API
│
├── desktop/
│   ├── popup.py             # Main rewrite popup window (cards, worker thread)
│   ├── settings.py          # Settings dialog
│   ├── tray.py              # System tray / menu bar icon
│   ├── hotkey.py            # Global hotkey listener (Windows: ctypes hook, Mac: pynput)
│   ├── capture.py           # Simulate copy to get selected text
│   ├── replace.py           # Simulate paste to replace text
│   └── platform_mac.py      # macOS-specific helpers (dock icon, window focus)
│
└── assets/
    ├── icon_18.png          # Menu bar icon for macOS (18×18)
    ├── icon_36.png          # Menu bar icon for macOS Retina (36×36)
    └── icon_72.png          # Menu bar icon for macOS high-DPI (72×72)
```

---

## Keyboard shortcuts (popup)

| Key | Action |
|---|---|
| `1` / `2` / `3` | Pick that variant and paste it |
| `Escape` | Close popup |
| `Enter` (in instructions field) | Regenerate with current instructions |

---

## Troubleshooting

**Hotkey does nothing on macOS**
Grant Accessibility permission: System Settings → Privacy & Security → Accessibility → enable WriteBetter (or your terminal app).

**Popup appears but text is not replaced**
The app pastes via simulated keyboard input. Make sure the original window is still focused when you click a variant.

**NVIDIA NIM times out**
NVIDIA NIM can be slow for large models. Increase the timeout in `config.json` under the nvidia_nim provider entry: `"timeout": 180`.

**App won't start — missing module**
Run `uv sync` again to make sure all dependencies are installed.
