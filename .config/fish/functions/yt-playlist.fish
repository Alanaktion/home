function yt-playlist --wraps=yt-dlp
  set -l NAME "%(upload_date>%Y-%m-%d)s - %(title)s [%(id)s].%(ext)s"
  yt-dlp -S 'height:720' --output "%(uploader)s/%(playlist)s/$NAME" $argv
end
