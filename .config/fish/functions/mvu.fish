function mvu --description 'Move files and change owner; usage: mvu -u USER src [src...] dest'
    set -l owner ''
    set -l positional

    # Parse flags
    set -l i 1
    while test $i -le (count $argv)
        switch $argv[$i]
            case -u --user
                set i (math $i + 1)
                if test $i -gt (count $argv)
                    echo "mvu: -u requires an argument" >&2
                    return 1
                end
                set owner $argv[$i]
            case --
                set i (math $i + 1)
                while test $i -le (count $argv)
                    set -a positional $argv[$i]
                    set i (math $i + 1)
                end
                break
            case '-*'
                echo "mvu: unknown option: $argv[$i]" >&2
                return 1
            case '*'
                set -a positional $argv[$i]
        end
        set i (math $i + 1)
    end

    # Validate
    if test -z "$owner"
        echo "mvu: -u USER is required" >&2
        return 1
    end
    if test (count $positional) -lt 2
        echo "mvu: at least one source and a destination are required" >&2
        return 1
    end

    set -l dest $positional[-1]
    set -l sources $positional[1..-2]

    # Move
    sudo mv -- $sources $dest
    or return $status

    # Resolve actual destination paths for chown
    set -l targets
    if test -d $dest
        for src in $sources
            set -a targets $dest/(basename $src)
        end
    else
        set targets $dest
    end

    # Chown
    sudo chown -- $owner $targets
    or return $status
end
