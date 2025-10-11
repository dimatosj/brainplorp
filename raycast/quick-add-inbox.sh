#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Quick Add to Inbox
# @raycast.mode silent
# @raycast.packageName plorp
# @raycast.icon 📥

# Optional parameters:
# @raycast.argument1 { "type": "text", "placeholder": "Item to add" }

# Documentation:
# @raycast.description Quickly add an item to your plorp inbox
# @raycast.author plorp
# @raycast.authorURL https://github.com/yourusername/plorp

# Configuration
PLORP_PATH="/Users/jsd/Documents/plorp/.venv/bin/plorp"

# Get the item text from argument
ITEM="$1"

# Add to inbox
OUTPUT=$("$PLORP_PATH" inbox add "$ITEM" 2>&1)
EXIT_CODE=$?

# Check result
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Added: $ITEM"
else
    echo "❌ Error: $OUTPUT"
    exit 1
fi
