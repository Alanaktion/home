set -x MANPAGER "less -R --use-color -Dd+r -Du+b"
set -x PLAYDATE_SDK_PATH $HOME/.config/PlaydateSDK
set -x DOTNET_ROOT $HOME/.dotnet

if not status is-interactive
    return
end

abbr -a yt yt-dlp
abbr -a gdl gallery-dl
abbr -a dc docker compose
abbr -a artisan php artisan
abbr -a tinker php artisan tinker
abbr -a ncdu ncdu -x
abbr -a dh dedup-hardlink
abbr -a ddD dedup -D
abbr -a usage du -sh
abbr -a su sudo su -
abbr -a iotop sudo iotop
abbr -a serve python3 -m http.server
