complete -c flatten -x
complete -c flatten -s 'h' -l 'help'
complete -c flatten -s 'P' -l 'no-prefix' -d 'do not prepend directory name to moved files'
complete -c flatten -s 's' -l 'singles' -d 'only flatten directories with a single file'
complete -c flatten -s 'r' -l 'recursive' -d 'rename files recursively'
complete -c flatten -s 'v' -l 'verbose' -d 'list changes as they are made'
complete -c flatten -s 'd' -l 'dry-run' -d 'list changes but do not actually rename/move'
complete -c flatten -s 'i' -l 'interactive' -d 'prompt for each change before applying'
