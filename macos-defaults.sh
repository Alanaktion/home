#!/bin/sh

# Set better defaults for macOS

# Dock
defaults write com.apple.Dock showhidden -bool YES
defaults write com.apple.dock autohide-delay -float 0
defaults write com.apple.dock autohide-time-modifier -float 0.2
killall Dock

# Finder
defaults write NSGlobalDomain AppleShowAllExtensions -bool true
defaults write com.apple.finder FXEnableExtensionChangeWarning -bool false
defaults write NSGlobalDomain NSTableViewDefaultSizeMode -int 1

# Global
defaults write -g NSDocumentSaveNewDocumentsToCloud -bool false
defaults write -g ApplePressAndHoldEnabled -bool false
defaults write -g InitialKeyRepeat -int 30
defaults write -g KeyRepeat -int 2

# Safari
defaults write com.apple.Safari IncludeInternalDebugMenu -bool TRUE

# Change file associations for code/config files
# https://alexpeattie.com/blog/associate-source-code-files-with-editor-in-macos-using-duti/
brew install duti python-yq

# Use Sublime Text for most files
curl "https://raw.githubusercontent.com/github/linguist/master/lib/linguist/languages.yml" \
  | yq -r "to_entries | (map(.value.extensions) | flatten) - [null] | unique | .[]" \
  | xargs -L 1 -I "{}" duti -s com.sublimetext.4 {} all

# Use VS Code for files that are typically part of a larger project
curl "https://raw.githubusercontent.com/github/linguist/master/lib/linguist/languages.yml" \
  | yq -r '{JavaScript,Python,Java,TypeScript,"C#",PHP,"C++",C,Ruby} | to_entries | (map(.value.extensions) | flatten) - [null] | unique | .[]' \
  | xargs -L 1 -I "{}" duti -s com.microsoft.VSCode {} all
