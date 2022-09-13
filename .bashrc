# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias ll='ls -laF'
alias yt='yt-dlp'
PS1='[\u@\h \W]\$ '

EDITOR=/usr/bin/vim

export PATH="$PATH:$HOME/.rvm/bin"
