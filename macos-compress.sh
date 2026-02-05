#!/usr/bin/env bash
set -euo pipefail

# Compress common cache and dependency directories on macOS

compress_dir() {
    local dir="$1"

    if [ ! -d "$dir" ]; then
        return
    fi

    echo "Compressing: $dir"
    ditto --hfsCompression --rsrc "$dir" "$dir"
}

compress_dir_safe() {
    local src="$1"

    if [ ! -d "$src" ]; then
        return
    fi

    local tmp="${src}.compressed.$$"
    local bak="${src}.uncompressed.$$"

    echo "Compressing (safe): $src"

    # Copy with:
    # -a  archive (preserve perms, mtimes, hard links)
    # -c  request APFS compression
    cp -a -c "$src" "$tmp"

    # Atomic-ish swap
    mv "$src" "$bak"
    mv "$tmp" "$src"

    # Clean up
    rm -rf "$bak"
}

# Explicit cache locations
compress_dir_safe "$HOME/.npm/_cacache"
compress_dir_safe "$HOME/Library/Caches/pnpm"

# node_modules under $HOME (pruned)
find "$HOME" -maxdepth 3 -type d -name node_modules -prune 2>/dev/null | while read -r d; do
    compress_dir_safe "$d"
done

# vendor directories under $HOME (pruned)
find "$HOME" -maxdepth 3 -type d -name vendor -prune 2>/dev/null | while read -r d; do
    compress_dir_safe "$d"
done

echo "APFS compression pass complete."
