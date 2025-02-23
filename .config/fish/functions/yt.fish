# Wrap yt-dlp with shorthands for common download targets

function yt --wraps=yt-dlp
  if not set -q argv[1]
    echo 'Usage: yt <term> [options]'
    echo
    echo 'Channels:'
    echo '  @chan            Channel videos'
    echo '  @chan/streams    Channel streams'
    echo '  @chan/playlists  Channel playlists'
    echo '  @chan?query      Channel search'
    echo '  @chan!           Channel videos by popularity'
    echo
    echo 'Playlists:'
    echo '  PL...            Playlist by ID'
    echo
    echo 'Search:'
    echo '  ?query           Search videos for "query"'
    echo '  PL?query         Search playlists for "query"'
    echo
    echo 'Output directory will be auto-adjusted to organize by term'
    return
  end

  set -f base "https://www.youtube.com"
  set -f filename "%(upload_date>%Y-%m-%d)s - %(title)s [%(id)s].%(ext)s"
  set -f directory "%(uploader)s"

  # TODO: loop through all of argv and replace any matching terms?
  # TODO: correctly handle non-matching option arguments

  if string match -q '@*' $argv[1]
    if string match -q '@*/*' $argv[1]
      # @channel/streams
      set -a argv $base/$argv[1]

    else if string match -q '@*\?*' $argv[1]
      # @channel?query -> @channel/search?q=query
      set -l match (string split '?' --max 1 $argv[1])
      set -a argv "$base/$match[1]/search?query=$match[2]"

    else if string match -q '@*!' $argv[1]
      # @channel! -> @channel (sorted by popularity)
      # TODO: verify this sorting still works with updated channel page UI
      set -l match (string trim -c '!' $argv[1])
      set -a argv "$base/$match/videos?view=0&sort=p&flow=grid"

    else
      # @channel -> @channel/videos
      set -a argv $base/$argv[1]/videos

    end
    set -e argv[1]
  else if string match -q '\?*' $argv[1]
    # ?query -> search all videos
    set -l query (string trim -c '?' $argv[1])
    set -e argv[1]
    set -p argv --use-extractors 'default,-youtube:playlist' --no-playlist
    set -a argv "$base/results=search_query=$query&filters=video&lclk=video"
    set -f directory "search/$query"

  else if string match -q 'PL\?*' $argv[1]
    # PL?query -> search all playlists
    set -l match (string split '?' --max 1 $argv[1])
    set -a argv "$base/results=search_query=$match[2]&filters=playlist"
    set -f directory "search/$match[2]/%(playlist)s"

  else if string match -q 'PL*' $argv[1]
    and test (string length $argv[1]) -gt 11
    # PL123123 -> playlist by ID
    set -a argv "$base/playlist?list=$argv[1]"
    set -e argv[1]
    set -f directory "$directory/%(playlist)s"

  end

  yt-dlp --output "$directory/$filename" $argv
end
