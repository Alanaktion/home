function yt-audio --wraps=yt-dlp
  set -f base "https://www.youtube.com"
  set -f filename "%(upload_date>%Y-%m-%d)s - %(title)s [%(id)s].%(ext)s"
  set -f directory "%(uploader)s"

  if string match -q '@*' $argv[1]
    set -a argv "$base/$argv[1]/videos"
  else if string match -q 'PL*' $argv[1]
    and test (string length $argv[1]) -gt 11
    # PL123123 -> playlist by ID
    set -a argv "$base/playlist?list=$argv[1]"
    set -e argv[1]
    set -f directory "%(playlist)s"
  end

  yt-dlp -S 'height:720' --format-sort acodec --format ba --extract-audio --audio-format m4a \
    --output "$directory/$filename" $argv
end
