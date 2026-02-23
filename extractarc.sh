#!/bin/bash
# Extract archive files into subdirectories based on archive filename.
#
# Usage:
#   ./extractarc.sh            # extract archives found under current directory
#   ./extractarc.sh --delete   # also delete each archive after successful extraction

set -u

DELETE_ON_SUCCESS=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    -d|--delete)
      DELETE_ON_SUCCESS=1
      ;;
    -h|--help)
      echo "Usage: $0 [-d|--delete]"
      echo "Extract archives into subdirectories named after each archive."
      echo "Supported formats: zip, rar, 7z, tar, tar.gz, tgz, tar.bz2, tbz2, tar.xz, txz"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [-d|--delete]" >&2
      exit 1
      ;;
  esac
  shift
done

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

extract_archive() {
  local archive="$1"
  local target_dir="$2"

  shopt -s nocasematch
  case "$archive" in
    *.tar.gz|*.tgz)
      tar -xzf "$archive" -C "$target_dir"
      ;;
    *.tar.bz2|*.tbz2)
      tar -xjf "$archive" -C "$target_dir"
      ;;
    *.tar.xz|*.txz)
      tar -xJf "$archive" -C "$target_dir"
      ;;
    *.tar)
      tar -xf "$archive" -C "$target_dir"
      ;;
    *.zip)
      if have_cmd unzip; then
        unzip -oq "$archive" -d "$target_dir"
      else
        7z x -y -o"$target_dir" "$archive"
      fi
      ;;
    *.rar)
      if have_cmd unrar; then
        unrar x -o+ -idq "$archive" "$target_dir/"
      else
        7z x -y -o"$target_dir" "$archive"
      fi
      ;;
    *.7z)
      7z x -y -o"$target_dir" "$archive"
      ;;
    *)
      shopt -u nocasematch
      return 2
      ;;
  esac
  local rc=$?
  shopt -u nocasematch
  return $rc
}

make_target_dir() {
  local archive="$1"
  local base_no_ext
  local parent_dir
  local target
  local i=1

  parent_dir="$(dirname "$archive")"
  base_no_ext="$(basename "$archive")"

  shopt -s nocasematch
  case "$base_no_ext" in
    *.tar.gz) base_no_ext="${base_no_ext%.[tT][aA][rR].[gG][zZ]}" ;;
    *.tgz)    base_no_ext="${base_no_ext%.[tT][gG][zZ]}" ;;
    *.tar.bz2) base_no_ext="${base_no_ext%.[tT][aA][rR].[bB][zZ]2}" ;;
    *.tbz2)   base_no_ext="${base_no_ext%.[tT][bB][zZ]2}" ;;
    *.tar.xz) base_no_ext="${base_no_ext%.[tT][aA][rR].[xX][zZ]}" ;;
    *.txz)    base_no_ext="${base_no_ext%.[tT][xX][zZ]}" ;;
    *.tar)    base_no_ext="${base_no_ext%.[tT][aA][rR]}" ;;
    *.zip)    base_no_ext="${base_no_ext%.[zZ][iI][pP]}" ;;
    *.rar)    base_no_ext="${base_no_ext%.[rR][aA][rR]}" ;;
    *.7z)     base_no_ext="${base_no_ext%.[7][zZ]}" ;;
  esac
  shopt -u nocasematch

  if [ -z "$base_no_ext" ]; then
    base_no_ext="extracted"
  fi

  target="$parent_dir/$base_no_ext"
  while [ -e "$target" ]; do
    target="$parent_dir/${base_no_ext}_$i"
    i=$((i + 1))
  done

  printf '%s\n' "$target"
}

if ! have_cmd tar; then
  echo "Error: tar is required." >&2
  exit 1
fi

if ! have_cmd 7z && ! have_cmd unzip; then
  echo "Error: need either 7z or unzip to extract .zip files." >&2
  exit 1
fi

if ! have_cmd 7z && ! have_cmd unrar; then
  echo "Error: need either 7z or unrar to extract .rar files." >&2
  exit 1
fi

if ! have_cmd 7z; then
  echo "Warning: 7z not found; .7z extraction will fail." >&2
fi

found=0
ok=0
failed=0

while IFS= read -r -d '' archive; do
  found=1

  target_dir="$(make_target_dir "$archive")"
  mkdir -p "$target_dir"

  echo "Extracting: $archive"
  echo "  -> $target_dir"

  if extract_archive "$archive" "$target_dir"; then
    ok=$((ok + 1))
    if [ "$DELETE_ON_SUCCESS" -eq 1 ]; then
      if rm -f -- "$archive"; then
        echo "  deleted: $archive"
      else
        echo "  warning: delete failed: $archive" >&2
      fi
    fi
  else
    failed=$((failed + 1))
    echo "  failed: $archive" >&2
    rmdir "$target_dir" >/dev/null 2>&1 || true
  fi
done < <(find . -type f \( -iname '*.zip' -o -iname '*.rar' -o -iname '*.7z' -o -iname '*.tar' -o -iname '*.tar.gz' -o -iname '*.tgz' -o -iname '*.tar.bz2' -o -iname '*.tbz2' -o -iname '*.tar.xz' -o -iname '*.txz' \) -print0)

if [ "$found" -eq 0 ]; then
  echo "No archives found."
  exit 0
fi

echo "Done. Success: $ok, Failed: $failed"

if [ "$failed" -gt 0 ]; then
  exit 1
fi
