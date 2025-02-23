# Home

A collection of random files that I sometimes keep in my home directory. Includes scripts I use for things, various config files, etc.

## Scripts

If you want to easily use most of the utility scripts, add the `bin` directory from this repo to your PATH. Completions are available for fish, too:

```fish
fish_add_path ./bin
set -Ua fish_complete_path (pwd)/.config/fish/completions
```

Some of the .sh and .py files do things related to ffmpeg, graphicsmagick, yt-dlp, etc. Most should work on any Unixy system with those things installed, but I mostly use them on macOS and Arch.

### macOS tools

```bash
brew install ffmpeg graphicsmagick python yt-dlp
```

### Arch Linux tools

```bash
pacman -S --needed ffmpeg graphicsmagick python yt-dlp fdupes
```

## Config

Config files are mostly for things like Git, fish, and zsh/[powerlevel10k](https://github.com/romkatv/powerlevel10k), but could be whatever.
