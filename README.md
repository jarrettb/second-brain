# Second Brain

**A private, offline AI chat assistant that runs entirely on your machine.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ollama](https://img.shields.io/badge/powered%20by-Ollama-orange)](https://ollama.com)

No cloud. No accounts. No telemetry. Your conversations and memories stay on your machine in plain text files you can read and delete any time.

---

## Features

- **Fully local** — powered by [Ollama](https://ollama.com); nothing leaves your machine
- **Persistent memory** — say `Remember: X` to store facts across conversations
- **Cross-conversation search** — full-text search over all saved chats
- **Streaming responses** — real-time output as the model generates
- **Multi-model** — switch between any model you have in Ollama
- **Network opt-in** — localhost only by default; enable WiFi access when you want it
- **Plain-text storage** — chats saved as `.txt`, memories as `.json`; no lock-in

---

## Quick Start

### 1. Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/download
```

### 2. Pull a model

```bash
ollama pull llama3
# Other options: mistral, gemma2, phi3, etc.
```

### 3. Clone and install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/second-brain.git
cd second-brain
pip3 install -r requirements.txt
```

### 4. Run

```bash
./start.sh
```

Then open **http://localhost:5000** in your browser.

> **macOS shortcut:** `start.sh` checks for Ollama, downloads the model if needed, installs Python deps, and launches the server — all in one step.

---

## Manual Start

```bash
# Start Ollama (if not already running)
ollama serve

# Start the server (localhost only)
python3 server.py

# Allow access from other devices on your WiFi
python3 server.py --network

# Custom port
python3 server.py --port 5001
```

---

## How It Works

```
Browser  ──►  Flask server (server.py)  ──►  Ollama API (localhost:11434)
                     │
                     ▼
           ~/SecondBrain_Chats/      ← saved conversations (.txt)
           ~/SecondBrain_Memory/     ← persistent memories (.json)
           ~/SecondBrain_Config/     ← settings (.json)
```

All data lives under your home directory. The server never opens outbound connections except to the local Ollama API.

---

## Data Locations

| Purpose      | Path                      |
|--------------|---------------------------|
| Chats        | `~/SecondBrain_Chats/`    |
| Memories     | `~/SecondBrain_Memory/`   |
| Config       | `~/SecondBrain_Config/`   |

Everything is plain text or JSON — open any file in a text editor, move it, back it up, or delete it.

---

## Memory

Say `Remember: X` or `Remember that X` in any message and the fact is stored in `~/SecondBrain_Memory/memories.json`. Relevant memories are automatically injected as context in future chats based on word overlap.

To view or delete memories, use the **Memory** panel in the sidebar, or edit the JSON file directly.

---

## Network Access

By default the server binds to `127.0.0.1` (your machine only). To allow other devices on the same WiFi (e.g. your phone):

```bash
python3 server.py --network
```

Or toggle it in the **Trust & Data** sidebar section and restart the server. Your IP is shown in the terminal output.

---

## Menu Bar Integration (macOS)

See [MENUBAR.md](MENUBAR.md) for instructions on adding Second Brain to your Mac menu bar using SwiftBar, Platypus, or a native Swift app.

---

## Prerequisites

| Requirement   | Version  | Notes                                    |
|---------------|----------|------------------------------------------|
| Python        | 3.8+     | Pre-installed on macOS                   |
| Ollama        | Latest   | https://ollama.com/download              |
| A local model | Any      | `ollama pull llama3` recommended to start|

---

## Troubleshooting

**Ollama not running**
```bash
ollama serve
```

**No models listed in the UI**
```bash
ollama list          # check what's downloaded
ollama pull llama3   # download a model
```

**Can't access from another device**
- Start with `python3 server.py --network`
- Confirm both devices are on the same WiFi network
- Check your firewall allows port 5000

**Port 5000 already in use**
```bash
python3 server.py --port 5001
```

**Conversations lost after restart**
- In-memory conversation state resets on restart; the saved `.txt` files in `~/SecondBrain_Chats/` are permanent and searchable

---

## Contributing

Contributions welcome. Please:

1. Fork the repo and create a feature branch
2. Keep changes focused — one feature or fix per PR
3. Test that the server starts and basic chat works before submitting
4. Open an issue first for large changes so we can discuss approach

---

## License

[MIT](LICENSE) — do whatever you want, no warranty.
