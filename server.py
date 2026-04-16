#!/usr/bin/env python3
"""
Local AI Chat Server - Your Second Brain
Connects to Ollama running locally and provides a web interface.
Trust boundaries: private, single-device, network opt-in only.
"""

import argparse
from flask import Flask, render_template, request, jsonify, Response
import requests
import json
from datetime import datetime
import os
from pathlib import Path

app = Flask(__name__)

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3"

# User-owned data paths under home directory
CHAT_DIR = Path.home() / "SecondBrain_Chats"
MEMORY_DIR = Path.home() / "SecondBrain_Memory"
CONFIG_DIR = Path.home() / "SecondBrain_Config"
CONFIG_FILE = CONFIG_DIR / "config.json"

CHAT_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)


def load_config():
    """Load user config. Network defaults to False (localhost only)."""
    defaults = {"network_enabled": False}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**defaults, **json.load(f)}
        except (json.JSONDecodeError, IOError):
            pass
    return defaults


def save_config(config):
    """Save user config."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


MEMORY_FILE = MEMORY_DIR / "memories.json"


def load_memories():
    """Load memories from JSON file."""
    if not MEMORY_FILE.exists():
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_memory(content):
    """Append a memory and save."""
    import re
    # Extract content after "Remember:" or "Remember that"
    for pattern in [r"remember\s*:\s*(.+)", r"remember\s+that\s+(.+)"]:
        m = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if m:
            text = m.group(1).strip()
            if len(text) > 5:
                memories = load_memories()
                memories.append({"content": text, "created": datetime.now().isoformat()})
                with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(memories, f, indent=2)
                return text
    return None


def get_relevant_memories(message, limit=5):
    """Get memories relevant to the current message. Simple word-overlap or last N."""
    memories = load_memories()
    if not memories:
        return []
    msg_words = set(w.lower() for w in message.split() if len(w) > 3)
    scored = []
    for m in memories:
        cnt = m.get("content", "")
        words = set(w.lower() for w in cnt.split() if len(w) > 3)
        overlap = len(msg_words & words) if msg_words else 0
        scored.append((overlap, m))
    # Sort by overlap (desc), then by recency (newest first)
    scored.sort(key=lambda x: (-x[0], x[1].get("created", "")), reverse=True)
    return [m for _, m in scored[:limit]]

# Store conversation history in memory (persists while server runs)
conversations = {}
conversation_metadata = {}  # Store titles and timestamps

@app.route('/')
def index():
    """Serve the main chat interface"""
    config = load_config()
    return render_template(
        'index.html',
        chat_dir=str(CHAT_DIR),
        memory_dir=str(MEMORY_DIR),
        network_enabled=config.get("network_enabled", False),
    )


@app.route('/api/trust', methods=['GET'])
def get_trust_info():
    """Return trust boundaries and data paths for UI"""
    config = load_config()
    return jsonify({
        "chat_dir": str(CHAT_DIR),
        "memory_dir": str(MEMORY_DIR),
        "network_enabled": config.get("network_enabled", False),
        "message": "Restart the server to apply network changes." if config.get("network_enabled") else None,
    })


@app.route('/api/trust/network', methods=['POST'])
def toggle_network():
    """Toggle network access (0.0.0.0 vs 127.0.0.1). Requires server restart to take effect."""
    config = load_config()
    data = request.json or {}
    enabled = data.get("enabled", not config.get("network_enabled"))
    config["network_enabled"] = bool(enabled)
    save_config(config)
    return jsonify({
        "network_enabled": config["network_enabled"],
        "message": "Restart the server to apply. New access: " + ("WiFi devices" if enabled else "localhost only"),
    })

def save_conversation_to_file(conversation_id):
    """Save conversation to a text file"""
    if conversation_id not in conversations or not conversations[conversation_id]:
        return
    
    metadata = conversation_metadata.get(conversation_id, {})
    title = metadata.get('title', 'Untitled Chat')
    timestamp = metadata.get('created', datetime.now().isoformat())
    
    # Create filename from timestamp and title
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title[:50]  # Limit length
    filename = f"{timestamp[:10]}_{safe_title}.txt"
    filepath = CHAT_DIR / filename
    
    # Write conversation to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Second Brain Conversation\n")
        f.write(f"Title: {title}\n")
        f.write(f"Created: {timestamp}\n")
        f.write(f"=" * 60 + "\n\n")
        
        for msg in conversations[conversation_id]:
            role = msg['role'].upper()
            content = msg['content']
            f.write(f"{role}:\n{content}\n\n")
            f.write("-" * 60 + "\n\n")
    
    return str(filepath)

def generate_conversation_title(messages):
    """Generate a title from the first user message"""
    for msg in messages:
        if msg['role'] == 'user':
            content = msg['content']
            # Take first 50 chars or up to first newline
            title = content.split('\n')[0][:50]
            if len(content) > 50:
                title += "..."
            return title
    return "New Chat"

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available models from Ollama"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({'models': [m['name'] for m in models]})
        return jsonify({'models': [DEFAULT_MODEL]})
    except:
        return jsonify({'models': [DEFAULT_MODEL]})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests with streaming response"""
    data = request.json
    message = data.get('message', '')
    model = data.get('model', DEFAULT_MODEL)
    conversation_id = data.get('conversation_id', 'default')
    
    # Get or create conversation history
    if conversation_id not in conversations:
        conversations[conversation_id] = []
        conversation_metadata[conversation_id] = {
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat(),
            'title': 'New Chat'
        }
    
    # Check for explicit memory: "Remember: X" or "Remember that X"
    memory_saved = save_memory(message)

    # Add user message to history
    conversations[conversation_id].append({
        'role': 'user',
        'content': message
    })
    
    # Update title if this is the first message
    if len(conversations[conversation_id]) == 1:
        conversation_metadata[conversation_id]['title'] = generate_conversation_title(conversations[conversation_id])
    
    # Update timestamp
    conversation_metadata[conversation_id]['updated'] = datetime.now().isoformat()
    
    def generate():
        """Stream the response from Ollama"""
        try:
            full_response = ""
            messages_to_send = list(conversations[conversation_id])
            # Inject relevant memories as system context
            relevant = get_relevant_memories(message)
            if relevant:
                memory_text = "Relevant things the user has asked you to remember:\n" + "\n".join(
                    f"- {m['content']}" for m in relevant
                )
                messages_to_send = [{"role": "system", "content": memory_text}] + messages_to_send

            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    'model': model,
                    'messages': messages_to_send,
                    'stream': True
                },
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'message' in json_response:
                        content = json_response['message'].get('content', '')
                        if content:
                            full_response += content
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    
                    if json_response.get('done', False):
                        # Save assistant response to history
                        conversations[conversation_id].append({
                            'role': 'assistant',
                            'content': full_response
                        })
                        
                        # Save to file after each exchange
                        filepath = save_conversation_to_file(conversation_id)
                        done_data = {"done": True, "saved_to": str(filepath)}
                        if memory_saved:
                            done_data["memory_saved"] = True
                        yield f"data: {json.dumps(done_data)}\n\n"
                        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get conversation history"""
    return jsonify({
        'messages': conversations.get(conversation_id, []),
        'metadata': conversation_metadata.get(conversation_id, {})
    })

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    """List all conversations with metadata"""
    conv_list = []
    for conv_id, metadata in conversation_metadata.items():
        conv_list.append({
            'id': conv_id,
            'title': metadata.get('title', 'Untitled'),
            'created': metadata.get('created'),
            'updated': metadata.get('updated'),
            'message_count': len(conversations.get(conv_id, []))
        })
    
    # Sort by updated time, most recent first
    conv_list.sort(key=lambda x: x.get('updated', ''), reverse=True)
    return jsonify({'conversations': conv_list})

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    import uuid
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = []
    conversation_metadata[conversation_id] = {
        'created': datetime.now().isoformat(),
        'updated': datetime.now().isoformat(),
        'title': 'New Chat'
    }
    return jsonify({
        'conversation_id': conversation_id,
        'metadata': conversation_metadata[conversation_id]
    })


@app.route('/api/conversations/import', methods=['POST'])
def import_conversation():
    """Import a conversation from saved chat file (for search results)."""
    import uuid
    data = request.json or {}
    title = data.get("title", "Imported Chat")
    messages = data.get("messages", [])
    if not isinstance(messages, list):
        return jsonify({"error": "Invalid messages"}), 400
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = messages
    conversation_metadata[conversation_id] = {
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "title": title[:80],
    }
    return jsonify({
        "conversation_id": conversation_id,
        "metadata": conversation_metadata[conversation_id],
    })

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Clear conversation history"""
    if conversation_id in conversations:
        del conversations[conversation_id]
    return jsonify({'success': True})

def search_chats(query):
    """Full-text search over saved chat files in CHAT_DIR. Returns list of matches with snippets."""
    if not query or len(query.strip()) < 2:
        return []
    query_lower = query.strip().lower()
    results = []
    for filepath in sorted(CHAT_DIR.glob("*.txt"), reverse=True):
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (IOError, OSError):
            continue
        if query_lower not in content.lower():
            continue
        # Extract title from file (first line after "Title: ")
        title = filepath.stem
        for line in content.split("\n"):
            if line.startswith("Title: "):
                title = line[7:].strip()
                break
        # Find snippet around match (up to 120 chars)
        pos = content.lower().find(query_lower)
        start = max(0, pos - 40)
        end = min(len(content), pos + len(query) + 80)
        snippet = content[start:end]
        if start > 0:
            snippet = "…" + snippet
        if end < len(content):
            snippet = snippet + "…"
        snippet = " ".join(snippet.split())  # normalize whitespace
        results.append({
            "file": filepath.name,
            "title": title[:80],
            "snippet": snippet[:200],
            "path": str(filepath),
        })
    return results[:50]  # limit results


def load_chat_file(filename):
    """Load a saved chat file and parse into messages. Returns (title, messages) or None."""
    filepath = CHAT_DIR / filename
    if not filepath.exists() or filepath.suffix != ".txt":
        return None
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (IOError, OSError):
        return None
    # Format: header with Title/Created, then "USER:\n...\n\n---\n\nASSISTANT:\n..."
    lines = content.split("\n")
    title = "Imported Chat"
    messages = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("Title: "):
            title = line[7:].strip()
        if line.strip() in ("=" * 60, "-" * 60):
            i += 1
            continue
        if line.upper().startswith("USER:"):
            text = line[5:].strip() if len(line) > 5 else ""
            i += 1
            while i < len(lines) and not lines[i].upper().startswith(("ASSISTANT:", "USER:")) and lines[i].strip() not in ("-" * 60, "=" * 60):
                text += "\n" + lines[i]
                i += 1
            if text.strip():
                messages.append({"role": "user", "content": text.strip()})
            continue
        if line.upper().startswith("ASSISTANT:"):
            text = line[9:].strip() if len(line) > 9 else ""
            i += 1
            while i < len(lines) and not lines[i].upper().startswith(("ASSISTANT:", "USER:")) and lines[i].strip() not in ("-" * 60, "=" * 60):
                text += "\n" + lines[i]
                i += 1
            if text.strip():
                messages.append({"role": "assistant", "content": text.strip()})
            continue
        i += 1
    return (title, messages) if messages else None


@app.route('/api/search', methods=['GET'])
def search():
    """Full-text search over saved chats. Returns results with snippet and file info."""
    q = request.args.get("q", "").strip()
    results = search_chats(q)
    return jsonify({"results": results})


@app.route('/api/chats/load/<filename>', methods=['GET'])
def load_chat(filename):
    """Load a saved chat file and return parsed messages. Used to open search results."""
    # Only allow safe filenames (no path traversal)
    if ".." in filename or "/" in filename or "\\" in filename or not filename.endswith(".txt"):
        return jsonify({"error": "Invalid file"}), 400
    parsed = load_chat_file(filename)
    if not parsed:
        return jsonify({"error": "Could not load chat"}), 404
    title, messages = parsed
    return jsonify({"title": title, "messages": messages, "file": filename})


@app.route('/api/memories', methods=['GET'])
def list_memories():
    """List stored memories."""
    return jsonify({"memories": load_memories()})


@app.route('/api/memories', methods=['DELETE'])
def delete_memory():
    """Delete a memory by index."""
    data = request.json or {}
    idx = data.get("index")
    if idx is None:
        return jsonify({"error": "index required"}), 400
    memories = load_memories()
    if 0 <= idx < len(memories):
        memories.pop(idx)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=2)
    return jsonify({"memories": memories})


@app.route('/api/health', methods=['GET'])
def health():
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return jsonify({
            'ollama_running': response.status_code == 200,
            'server_running': True
        })
    except:
        return jsonify({
            'ollama_running': False,
            'server_running': True
        })

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Second Brain - Local AI Chat")
    parser.add_argument("--network", action="store_true", help="Enable network access (0.0.0.0) for WiFi devices")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on (default: 5000)")
    args = parser.parse_args()

    # Default: localhost only. Use --network or config to allow WiFi access
    config = load_config()
    use_network = args.network or config.get("network_enabled", False)
    host = "0.0.0.0" if use_network else "127.0.0.1"

    print("=" * 60)
    print("🧠 Second Brain Server Starting...")
    print("=" * 60)
    print(f"Web Interface: http://localhost:{args.port}")
    if use_network:
        print(f"Network Access: http://YOUR_MAC_IP:{args.port} (WiFi devices)")
    else:
        print("Network: localhost only (use --network for WiFi access)")
    print("=" * 60)
    print(f"💾 Chats: {CHAT_DIR}")
    print(f"🧠 Memory: {MEMORY_DIR}")
    print("=" * 60)
    print("\nMake sure Ollama is running: ollama serve")
    print("=" * 60)

    app.run(host=host, port=args.port, debug=False)
