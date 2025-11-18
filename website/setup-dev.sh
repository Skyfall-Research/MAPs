#!/bin/bash

# Setup script for local development
# This script creates symlinks from website/static to shared/ directory

set -e  # Exit on error

echo "Setting up local development environment..."

# Navigate to the script's directory
cd "$(dirname "$0")"

# Define the static directory
STATIC_DIR="static"
# Path to shared dir from script location (for reading)
SHARED_DIR_ABS="../shared"
# Path from static/ to shared/ (for symlink targets - resolved from symlink location)
SHARED_DIR_SYMLINK="../../shared"

# Files to exclude from symlinking
EXCLUDE_PATTERNS=(".DS_Store")

# Function to check if a file should be excluded
should_exclude() {
    local item="$1"
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        if [[ "$item" == "$pattern" ]]; then
            return 0
        fi
    done
    return 1
}

echo "Cleaning up existing non-symlink files/dirs in $STATIC_DIR..."

# Remove any existing files/dirs that aren't symlinks
for item in "$STATIC_DIR"/*; do
    if [ -e "$item" ] && [ ! -L "$item" ]; then
        basename_item=$(basename "$item")
        # Check if this item exists in shared (would be replaced by symlink)
        if [ -e "$SHARED_DIR_ABS/$basename_item" ]; then
            echo "  Removing $item"
            rm -rf "$item"
        fi
    fi
done

echo "Creating symlinks for all shared/ contents..."

# Create symlinks for all files and directories in shared/
for item in "$SHARED_DIR_ABS"/*; do
    if [ -e "$item" ]; then
        basename_item=$(basename "$item")

        # Skip excluded patterns
        if should_exclude "$basename_item"; then
            echo "  Skipping $basename_item (excluded)"
            continue
        fi

        target="$STATIC_DIR/$basename_item"

        if [ ! -e "$target" ]; then
            echo "  Linking $basename_item"
            ln -s "$SHARED_DIR_SYMLINK/$basename_item" "$target"
        elif [ -L "$target" ]; then
            echo "  Skipping $basename_item (already a symlink)"
        else
            # If it exists but is not a symlink, replace it with a symlink
            echo "  Replacing $basename_item with symlink"
            rm -rf "$target"
            ln -s "$SHARED_DIR_SYMLINK/$basename_item" "$target"
        fi

    fi
done

# Clean up .DS_Store files
echo "Cleaning up .DS_Store files..."
find "$STATIC_DIR" -name ".DS_Store" -type f -delete 2>/dev/null || true

echo ""
echo "✓ Setup complete!"
echo ""
echo "Your website/static/ directory now uses symlinks to ../shared/"
echo "Any changes to shared/ will immediately reflect in your local development."
echo ""
echo "To start development, run: npm run dev"
