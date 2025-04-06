function yt-playlist --wraps=yt-dlp
  set -l NAME "%(upload_date>%Y-%m-%d)s - %(title)s [%(id)s].%(ext)s"
  if string match -q 'PL*' $argv[1]
    and test (string length $argv[1]) -gt 11
    # PL123123 -> playlist by ID
    set -a argv "https://www.youtube.com/playlist?list=$argv[1]"
    set -e argv[1]
  end
  yt-dlp -S 'height:720' --output "%(uploader)s/%(playlist)s/$NAME" $argv
end
