# Home

A collection of random files that I sometimes keep in my home directory. Includes scripts I use for things, various config files, etc.

## Scripts

Most of the .sh files do things related to ffmpeg, imagemagick, yt-dlp, or btrfs. Most should work on any Unixy system with those things installed, but I mostly use them on macOS and Arch.

### macOS tools

```bash
brew install ffmpeg imagemagick python
pip install -U yt-dlp
```

### Arch Linux tools

```bash
pacman -S --needed ffmpeg imagemagick yt-dlp btrfs-progs
```

## Config

Config files are mostly for things like Git and zsh/[powerlevel10k](https://github.com/romkatv/powerlevel10k), but could be whatever.
