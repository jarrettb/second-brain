# Menu Bar Integration Guide

There are a few ways to add Second Brain to your Mac's menu bar. Here are the easiest options:

## Option 1: SwiftBar (Recommended - Easiest)

SwiftBar lets you create menu bar apps using simple scripts.

### Setup:

1. **Install SwiftBar**
   ```bash
   brew install swiftbar
   ```
   Or download from: https://github.com/swiftbar/SwiftBar/releases

2. **Create the plugin**
   
   Save this as `second-brain.5m.sh` in your SwiftBar plugins folder (usually `~/Library/Application Support/SwiftBar/`):

   ```bash
   #!/bin/bash
   
   # <xbar.title>Second Brain</xbar.title>
   # <xbar.version>v1.0</xbar.version>
   # <xbar.author>You</xbar.author>
   # <xbar.desc>Quick access to your local AI</xbar.desc>
   
   # Check if server is running
   if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
       echo "🧠 | color=white"
       echo "---"
       echo "Open Second Brain | bash='open' param1='http://localhost:5000' terminal=false"
       echo "Server Status: Running | color=green"
       echo "---"
       echo "Stop Server | bash='pkill' param1='-f' param2='server.py' terminal=false refresh=true"
   else
       echo "🧠 | color=gray"
       echo "---"
       echo "Server Status: Stopped | color=red"
       echo "Start Server | bash='cd /path/to/second-brain && ./start.sh' terminal=true"
   fi
   
   echo "---"
   echo "Refresh | refresh=true"
   ```

3. **Make it executable**
   ```bash
   chmod +x ~/Library/Application\ Support/SwiftBar/second-brain.5m.sh
   ```

4. **Update the path** in the script to point to your actual Second Brain folder

5. **Refresh SwiftBar** - You should now see a 🧠 icon in your menu bar!

## Option 2: Platypus

Platypus wraps shell scripts into native Mac apps.

### Setup:

1. **Install Platypus**
   ```bash
   brew install platypus
   ```

2. **Create the app**
   - Open Platypus
   - Script Type: Shell
   - Script: Browse to your `start.sh`
   - Interface: None (Status Menu)
   - Check "Runs in background"
   - Click "Create App"

## Option 3: Native Swift App (Advanced)

For a proper native menu bar app, here's a minimal Swift app structure:

```swift
import Cocoa
import WebKit

@NSApplicationMain
class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!
    var popover: NSPopover!
    
    func applicationDidFinishLaunching(_ aNotification: Notification) {
        // Create status bar item
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        if let button = statusItem.button {
            button.image = NSImage(systemSymbolName: "brain", accessibilityDescription: "Second Brain")
            button.action = #selector(togglePopover)
        }
        
        // Create popover with web view
        popover = NSPopover()
        popover.contentViewController = WebViewController()
        popover.behavior = .transient
    }
    
    @objc func togglePopover() {
        if let button = statusItem.button {
            if popover.isShown {
                popover.performClose(nil)
            } else {
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            }
        }
    }
}

class WebViewController: NSViewController {
    var webView: WKWebView!
    
    override func loadView() {
        webView = WKWebView(frame: NSRect(x: 0, y: 0, width: 400, height: 600))
        view = webView
        
        if let url = URL(string: "http://localhost:5000") {
            webView.load(URLRequest(url: url))
        }
    }
}
```

To build this:
1. Create a new macOS App project in Xcode
2. Replace AppDelegate.swift with the above
3. Build and run

## Option 4: Electron (Cross-platform)

If you want to make a distributable app:

```javascript
// main.js
const { app, BrowserWindow, Tray, Menu } = require('electron');
const path = require('path');

let tray = null;
let window = null;

app.on('ready', () => {
  // Create tray
  tray = new Tray(path.join(__dirname, 'brain-icon.png'));
  
  // Create hidden window
  window = new BrowserWindow({
    width: 400,
    height: 600,
    show: false,
    frame: false,
    webPreferences: {
      nodeIntegration: false
    }
  });
  
  window.loadURL('http://localhost:5000');
  
  // Tray menu
  const contextMenu = Menu.buildFromTemplate([
    { 
      label: 'Open Second Brain', 
      click: () => window.show() 
    },
    { 
      label: 'Quit', 
      click: () => app.quit() 
    }
  ]);
  
  tray.setContextMenu(contextMenu);
  tray.on('click', () => {
    window.isVisible() ? window.hide() : window.show();
  });
});
```

## My Recommendation

**Start with SwiftBar** (Option 1) - it's the fastest way to get a working menu bar integration. It's:
- Easy to set up (5 minutes)
- Easy to customize
- Shows server status
- Quick access to open the web interface

Once you have that working, you can decide if you want to build a more sophisticated native app.

---

## Quick Start with SwiftBar

Here's the full setup in one go:

```bash
# Install SwiftBar
brew install swiftbar

# Create plugins folder if it doesn't exist
mkdir -p ~/Library/Application\ Support/SwiftBar

# Download a brain icon (optional)
# Or the script will use a text emoji

# Create the plugin (update the path!)
cat > ~/Library/Application\ Support/SwiftBar/second-brain.5m.sh << 'EOF'
#!/bin/bash
SECOND_BRAIN_PATH="/path/to/your/second-brain"

if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "🧠 | color=white"
    echo "---"
    echo "Open Second Brain | bash='open' param1='http://localhost:5000' terminal=false"
    echo "Open on Phone | bash='open' param1='http://$(ipconfig getifaddr en0):5000' terminal=false"
    echo "---"
    echo "✓ Running | color=green"
else
    echo "🧠 | color=gray"
    echo "---"
    echo "✗ Offline | color=red"
    echo "Start Server | bash='$SECOND_BRAIN_PATH/start.sh' terminal=true"
fi
EOF

# Make executable
chmod +x ~/Library/Application\ Support/SwiftBar/second-brain.5m.sh

# Launch SwiftBar
open -a SwiftBar
```

Don't forget to update `SECOND_BRAIN_PATH` in the script!

Would you like me to help you set up any of these options?
