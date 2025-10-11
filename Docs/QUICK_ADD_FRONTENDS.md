# Quick Add Frontends

This document describes different methods for quick-adding items to your plorp inbox from anywhere on macOS.

All frontends use the same core CLI command: `plorp inbox add <text>`. Choose the method that fits your workflow.

---

## Raycast (Recommended - Free)

**Why Raycast:**
- Free tier includes script commands
- Modern, beautiful UI
- Fast (written in Rust)
- Easy setup
- Native keyboard shortcut support
- Growing developer community

**Setup:**

1. **Install Raycast** (if not already installed):
   ```bash
   # Download from https://raycast.com
   # Or via Homebrew:
   brew install --cask raycast
   ```

2. **Copy the plorp Raycast script**:
   ```bash
   # Create Raycast scripts directory
   mkdir -p ~/Documents/Raycast/Scripts

   # Copy plorp quick-add script
   cp raycast/quick-add-inbox.sh ~/Documents/Raycast/Scripts/
   chmod +x ~/Documents/Raycast/Scripts/quick-add-inbox.sh
   ```

3. **Edit script path** (if needed):
   Open `~/Documents/Raycast/Scripts/quick-add-inbox.sh` and update:
   ```bash
   # Change this line to match your plorp installation:
   PLORP_PATH="/Users/jsd/Documents/plorp/.venv/bin/plorp"

   # To find your path:
   which plorp
   ```

4. **Configure in Raycast**:
   - Open Raycast (⌘Space or your chosen hotkey)
   - Type "Script Commands"
   - Find "Quick Add to Inbox"
   - Click the script, then press ⌘K → "Configure Command"
   - Assign keyboard shortcut: **⌘⌥I** (recommended)

**Usage:**
```
Press ⌘⌥I anywhere on Mac
→ Raycast window appears with "Item to add" prompt
→ Type "Buy milk for office party"
→ Press Enter
→ See "✓ Added: Buy milk for office party" notification
→ Item instantly added to inbox file
```

**Pros:**
- ✅ Free
- ✅ Fast (~2-3 seconds per capture)
- ✅ Beautiful, modern UI
- ✅ System-wide keyboard shortcut
- ✅ Active development and community

**Cons:**
- ❌ Requires separate app installation
- ❌ macOS only

---

## macOS Shortcuts (Native, Free)

**Why Shortcuts:**
- Native to macOS 12+ (Monterey and later)
- No third-party apps needed
- Simple, reliable
- Built-in keyboard shortcut support

**Setup:**

1. **Open Shortcuts app** (pre-installed on macOS 12+)

2. **Create new shortcut**:
   - Click "+" to create new shortcut
   - Name it "plorp Quick Add"

3. **Add actions**:
   - Search for "Ask for Input" and add it
   - Set prompt to: "What to add to inbox?"
   - Search for "Run Shell Script" and add it
   - Paste this script:
     ```bash
     /Users/jsd/Documents/plorp/.venv/bin/plorp inbox add "$1"
     ```
   - Change "Pass input" to "as arguments"
   - Update path to match your plorp installation (`which plorp`)

4. **Add keyboard shortcut**:
   - System Settings → Keyboard → Keyboard Shortcuts → Services
   - Find "plorp Quick Add"
   - Assign: **⌘⌥I** (or your preference)

**Usage:**
```
Press ⌘⌥I anywhere on Mac
→ Dialog appears: "What to add to inbox?"
→ Type text and press OK
→ Item added to inbox
```

**Pros:**
- ✅ Native, no third-party apps
- ✅ Free
- ✅ Simple, reliable
- ✅ Works on all modern Macs

**Cons:**
- ❌ Basic UI (system dialog)
- ❌ Slower than Raycast (~5-7 seconds)
- ❌ Requires macOS 12+

---

## Alfred Workflow (Popular, Paid)

**Why Alfred:**
- Extremely popular among power users
- Beautiful, customizable UI
- Very fast
- Extensive workflow ecosystem

**Note:** Requires **Alfred Powerpack** ($34 one-time purchase) for custom keyboard shortcuts and workflows.

**Setup:**

1. **Install Alfred Powerpack** (if not already purchased):
   - https://www.alfredapp.com/powerpack/

2. **Create new workflow**:
   - Open Alfred Preferences → Workflows
   - Click "+" → Blank Workflow
   - Name: "plorp Quick Add"

3. **Add Hotkey Trigger**:
   - Right-click canvas → Inputs → Hotkey
   - Set hotkey: **⌘⌥I**
   - Leave argument: "No argument"

4. **Add Keyword Input**:
   - Right-click canvas → Inputs → Keyword
   - Keyword: `inbox`
   - Placeholder: "Item to add"
   - Argument: Required

5. **Add Run Script action**:
   - Right-click canvas → Actions → Run Script
   - Language: `/bin/bash`
   - Script:
     ```bash
     /Users/jsd/Documents/plorp/.venv/bin/plorp inbox add "$1"
     ```
   - Update path to match your installation

6. **Add Post Notification**:
   - Right-click canvas → Outputs → Post Notification
   - Title: "plorp"
   - Text: "Added to inbox: {query}"

7. **Connect the pieces**:
   - Drag from Hotkey → Keyword Input
   - Drag from Keyword Input → Run Script
   - Drag from Run Script → Post Notification

**Usage:**
```
Method 1 (Hotkey):
  Press ⌘⌥I
  → Alfred bar appears
  → Type text
  → Press Enter

Method 2 (Keyword):
  Open Alfred (your hotkey, usually ⌘Space)
  → Type "inbox Buy milk"
  → Press Enter
```

**Pros:**
- ✅ Very fast (~2-3 seconds)
- ✅ Beautiful, customizable UI
- ✅ Large ecosystem of workflows
- ✅ Popular among developers

**Cons:**
- ❌ Requires paid Powerpack ($34)
- ❌ More complex setup than Raycast

---

## Automator Service (Native, Free, All Versions)

**Why Automator:**
- Native to all macOS versions
- No additional installation
- Works on older Macs (pre-Monterey)

**Setup:**

1. **Open Automator**:
   - Applications → Automator
   - Create new → "Quick Action"

2. **Configure workflow settings** (top of window):
   - "Workflow receives": "no input"
   - "in": "any application"

3. **Add AppleScript action**:
   - Search for "Run AppleScript" in the actions list
   - Drag it to the workflow area
   - Replace the default script with:
     ```applescript
     on run {input, parameters}
         set userInput to text returned of (display dialog "Quick add to inbox:" default answer "")
         do shell script "/Users/jsd/Documents/plorp/.venv/bin/plorp inbox add " & quoted form of userInput
         return input
     end run
     ```
   - Update path to match your plorp installation

4. **Save**:
   - File → Save
   - Name: "plorp Quick Add"
   - Location: Services folder (default)

5. **Add keyboard shortcut**:
   - System Settings → Keyboard → Keyboard Shortcuts → Services
   - Under "General", find "plorp Quick Add"
   - Click "add shortcut"
   - Press: **⌘⌥I**

**Usage:**
```
Press ⌘⌥I anywhere on Mac
→ Dialog appears: "Quick add to inbox:"
→ Type text and press OK
→ Item added to inbox
```

**Pros:**
- ✅ Native, works on all macOS versions
- ✅ Free
- ✅ No third-party apps

**Cons:**
- ❌ Ugly system dialog
- ❌ Slowest option (~7-10 seconds)
- ❌ No notifications
- ❌ AppleScript required (less maintainable)

---

## Comparison Table

| Frontend | Cost | Setup Time | Speed | UI Quality | macOS Version | Recommendation |
|----------|------|-----------|-------|-----------|---------------|----------------|
| **Raycast** | Free | 5 min | 2-3 sec | ⭐⭐⭐⭐⭐ | 11+ | **Best overall** |
| **Shortcuts** | Free | 5 min | 5-7 sec | ⭐⭐⭐ | 12+ | Good native option |
| **Alfred** | $34 | 10 min | 2-3 sec | ⭐⭐⭐⭐⭐ | 10.11+ | If you already own it |
| **Automator** | Free | 10 min | 7-10 sec | ⭐⭐ | All | Older Macs only |

---

## Troubleshooting

### "Command not found: plorp"

**Problem:** The script can't find your plorp installation.

**Solution:**
1. Find plorp path:
   ```bash
   which plorp
   ```
2. Update the path in your frontend script/workflow

### "Permission denied"

**Problem:** The Raycast script isn't executable.

**Solution:**
```bash
chmod +x ~/Documents/Raycast/Scripts/quick-add-inbox.sh
```

### "Vault not found"

**Problem:** plorp can't find your Obsidian vault.

**Solution:**
Check your plorp config:
```bash
cat ~/.config/plorp/config.yaml
```

Ensure `vault_path` is correct.

### Keyboard shortcut doesn't work

**Problem:** Another app is using ⌘⌥I.

**Solutions:**
1. Check for conflicts: System Settings → Keyboard → Keyboard Shortcuts
2. Choose a different shortcut (⌘⌥K, ⌘⌥N, etc.)

---

## Advanced: Custom Frontends

You can create your own frontend using any automation tool. Just call:

```bash
/path/to/plorp inbox add "Your item text"
```

**Examples:**
- **BetterTouchTool**: Trigger on specific gesture
- **Karabiner-Elements**: Custom keyboard mapping
- **Hammerspoon**: Lua-based automation
- **Shell alias**: `alias qi='plorp inbox add'`

The CLI command is the universal interface - use any tool that can run a shell command.

---

## Recommended Workflow

**For most users:**
1. Install Raycast (free, modern, fast)
2. Set up ⌘⌥I keyboard shortcut
3. Use `plorp inbox process` daily to organize captured items

**For users without Raycast:**
1. Use macOS Shortcuts (free, native)
2. Accept slightly slower capture speed
3. Same daily processing workflow

**For Alfred users:**
1. Use Alfred if you already have Powerpack
2. Enjoy the beautiful UI and speed
3. Integrate with your existing Alfred workflows

---

## Next Steps

After capturing items, process them with:

```bash
plorp inbox process
```

This is where you:
- Assign projects
- Set due dates
- Add priorities
- Create linked notes

**Pure capture** (inbox add) + **Organized processing** (inbox process) = GTD workflow perfection.
