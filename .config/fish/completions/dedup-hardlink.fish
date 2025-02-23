complete -c dedup-hardlink -s 'h' -l 'help'
complete -c dedup-hardlink -x -s 's' -l 'min-size' -d 'Miniumum size of file, in bytes'
complete -c dedup-hardlink -x -s 'n' -l 'name' -d 'Match files with this glob pattern'
complete -c dedup-hardlink -l 'dry-run' -d 'List target files without deduplicating'
