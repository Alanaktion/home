# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Uncomment if using Homebrew on Apple Silicon
# eval "$(/opt/homebrew/bin/brew shellenv)"
# FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"

autoload -Uz compinit
compinit

PROMPT_EOL_MARK=''
setopt HIST_IGNORE_SPACE
setopt NO_NOMATCH

# Allow case-insensitive matching
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
setopt MENU_COMPLETE

# # Bind ctrl+arrow keys
# bindkey -e
# bindkey "^[[1;5C" forward-word
# bindkey "^[[1;5D" backward-word

export CLICOLOR=1
export GPG_TTY=$(tty)
alias ll='ls -lF'
alias la='ls -a'
alias g='git'
alias gp='git pull'
alias yt='yt-dlp'
alias yt-1080='yt-dlp -S "res:1080"'
alias yt-720='yt-dlp -S "res:720"'
alias vim='nvim'
alias yeet="rm -rf"
alias btrfs-dedup="rmlint -s 4K -g -o sh:rmlint.sh -c sh:clone"
alias width="identify -format '%w'"

export PATH="$PATH:$HOME/.composer/vendor/bin:$HOME/.rvm/bin"

# Uncomment after installing p10k on Apple Silicon
# source /opt/homebrew/opt/powerlevel10k/powerlevel10k.zsh-theme

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
