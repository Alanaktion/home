#!/usr/bin/env bash
#
# dedupe-repos.sh — consolidate duplicate git clones into git worktrees.
#
# Compatible with bash 3.2 (the version that ships with macOS).
#
set -euo pipefail

DRY_RUN=0
ASSUME_YES=0
ROOT="."

usage() {
  cat <<'EOF'
Usage: dedupe-repos.sh [-d DIR] [-n] [-y] [-h]

  -d DIR   directory to scan (default: current directory)
  -n       dry run: print the plan, change nothing
  -y       skip the confirmation prompt
  -h       show this help
EOF
}

say()  { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }

while getopts ":d:nyh" opt; do
  case "$opt" in
    d) ROOT=$OPTARG ;;
    n) DRY_RUN=1 ;;
    y) ASSUME_YES=1 ;;
    h) usage; exit 0 ;;
    :) printf 'error: option -%s requires an argument\n' "$OPTARG" >&2; exit 2 ;;
    \?) printf 'error: unknown option -%s\n' "$OPTARG" >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))

[ -d "$ROOT" ] || { printf 'error: not a directory: %s\n' "$ROOT" >&2; exit 1; }
ROOT=$(cd -- "$ROOT" && pwd)

# ---- url normalization -----------------------------------------------------

normalize_url() {
  local u=$1
  u=${u%.git}
  u=${u%/}
  if [[ $u != *"://"* && $u == *:* ]]; then
    u=${u#*@}
    u=${u%%:*}/${u#*:}
  fi
  u=${u#*://}
  u=${u##*@}
  u=${u%.git}
  u=${u%/}
  # bash 3.2 has no ${var,,}
  printf '%s\n' "$u" | tr '[:upper:]' '[:lower:]'
}

# ---- temp workspace --------------------------------------------------------

tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/dedupe-repos.XXXXXX")
trap 'rm -rf "$tmpdir"' EXIT

# ---- collect clones --------------------------------------------------------

find "$ROOT" -type d -name .git -prune -print 2>/dev/null | sort > "$tmpdir/gitdirs"

: > "$tmpdir/repos.tsv"
while IFS= read -r gitdir; do
  repo=${gitdir%/.git}
  url=$(git -C "$repo" remote get-url origin 2>/dev/null) || continue
  [ -n "$url" ] || continue
  key=$(normalize_url "$url")
  printf '%s\t%s\n' "$key" "$repo" >> "$tmpdir/repos.tsv"
done < "$tmpdir/gitdirs"

sort -u "$tmpdir/repos.tsv" > "$tmpdir/repos.sorted"

# ---- build plan ------------------------------------------------------------
# Group identical remotes by walking the sorted TSV. No associative array
# needed — we just remember the previous key and accumulate a group.

: > "$tmpdir/plan.tsv"
plan_count=0
prev_key=""
group=()

while IFS=$'\t' read -r key repo; do
  if [ -n "$prev_key" ] && [ "$key" != "$prev_key" ]; then
    if [ ${#group[@]} -gt 1 ]; then
      primary=${group[0]}
      i=1
      while [ $i -lt ${#group[@]} ]; do
        printf '%s\t%s\n' "$primary" "${group[$i]}" >> "$tmpdir/plan.tsv"
        plan_count=$((plan_count + 1))
        i=$((i + 1))
      done
    fi
    group=()
  fi
  group+=("$repo")
  prev_key=$key
done < "$tmpdir/repos.sorted"

if [ -n "$prev_key" ] && [ ${#group[@]} -gt 1 ]; then
  primary=${group[0]}
  i=1
  while [ $i -lt ${#group[@]} ]; do
    printf '%s\t%s\n' "$primary" "${group[$i]}" >> "$tmpdir/plan.tsv"
    plan_count=$((plan_count + 1))
    i=$((i + 1))
  done
fi

if [ "$plan_count" -eq 0 ]; then
  say "No duplicate clones found under $ROOT."
  exit 0
fi

say "Found $plan_count duplicate clone(s) under $ROOT:"
while IFS=$'\t' read -r p d; do
  say ""
  say "  keep:  $p"
  say "  fold:  $d   ->  worktree"
done < "$tmpdir/plan.tsv"
say ""

if [ "$DRY_RUN" -eq 1 ]; then
  say "Dry run: nothing changed."
  exit 0
fi

if [ "$ASSUME_YES" -eq 0 ]; then
  printf 'Proceed? [y/N] '
  read -r reply || reply=""
  case "$reply" in
    [yY]*) ;;
    *) say "Aborted."; exit 1 ;;
  esac
fi

# ---- fold duplicates -------------------------------------------------------

fold_duplicate() {
  local primary=$1 dup=$2

  if [ -n "$(git -C "$dup" status --porcelain 2>/dev/null)" ]; then
    warn "skipping $dup: working tree has uncommitted changes"
    return 1
  fi

  local head
  if ! head=$(git -C "$dup" rev-parse --verify HEAD 2>/dev/null); then
    warn "skipping $dup: repository has no commits"
    return 1
  fi

  if ! git -C "$primary" fetch --quiet --no-tags "$dup" \
        '+refs/heads/*:refs/dedupe-tmp/*' \
        '+HEAD:refs/dedupe-tmp/HEAD' 2>/dev/null; then
    warn "skipping $dup: could not import objects into $primary"
    return 1
  fi

  # Recreate each branch in the primary, renaming on conflict.
  # Parallel arrays stand in for an associative map (bash 3.2 has no -A).
  local map_src map_dst
  map_src=()
  map_dst=()

  local ref b sha target n
  while IFS= read -r ref; do
    [ -n "$ref" ] || continue
    b=${ref#refs/dedupe-tmp/}
    if [ "$b" = "HEAD" ]; then
      continue
    fi
    sha=$(git -C "$primary" rev-parse --verify "refs/dedupe-tmp/$b")
    target=$b
    if git -C "$primary" show-ref --verify --quiet "refs/heads/$target"; then
      if [ "$(git -C "$primary" rev-parse "refs/heads/$target")" = "$sha" ]; then
        map_src+=("$b")
        map_dst+=("$target")
        continue
      fi
      target="$b-$(basename -- "$dup")"
      n=2
      while git -C "$primary" show-ref --verify --quiet "refs/heads/$target"; do
        target="$b-$(basename -- "$dup")-$n"
        n=$((n + 1))
      done
    fi
    git -C "$primary" branch "$target" "$sha"
    map_src+=("$b")
    map_dst+=("$target")
  done < <(git -C "$primary" for-each-ref --format='%(refname)' refs/dedupe-tmp/)

  # Pick the branch (or detached HEAD) the worktree should land on.
  local branch target primary_branch use_detach=0 i
  branch=$(git -C "$dup" symbolic-ref --quiet --short HEAD || true)

  target=""
  if [ -n "$branch" ]; then
    i=0
    while [ $i -lt ${#map_src[@]} ]; do
      if [ "${map_src[$i]}" = "$branch" ]; then
        target=${map_dst[$i]}
        break
      fi
      i=$((i + 1))
    done
  fi

  if [ -n "$target" ]; then
    primary_branch=$(git -C "$primary" symbolic-ref --quiet --short HEAD || true)
    if [ "$target" = "$primary_branch" ]; then
      use_detach=1
    fi
  else
    use_detach=1
  fi

  # Drop temporary refs (branches we created above keep the objects alive).
  while IFS= read -r ref; do
    [ -n "$ref" ] || continue
    git -C "$primary" update-ref -d "$ref"
  done < <(git -C "$primary" for-each-ref --format='%(refname)' refs/dedupe-tmp/)

  # Swap the duplicate for a worktree.
  local backup="${dup}.dedupe-backup.$$"
  mv -- "$dup" "$backup"

  local ok=1
  if [ "$use_detach" -eq 1 ]; then
    git -C "$primary" worktree add --detach "$dup" "$head" || ok=0
  else
    git -C "$primary" worktree add "$dup" "$target" || ok=0
  fi

  if [ "$ok" -eq 1 ]; then
    rm -rf -- "$backup"
    if [ "$use_detach" -eq 1 ]; then
      say "  folded $dup  (detached at ${head:0:8})"
    else
      say "  folded $dup  (branch $target)"
    fi
  else
    mv -- "$backup" "$dup"
    git -C "$primary" worktree prune
    warn "failed to create worktree at $dup; original restored"
    return 1
  fi
}

# ---- run -------------------------------------------------------------------

failures=0
while IFS=$'\t' read -r p d; do
  ( fold_duplicate "$p" "$d" ) || failures=$((failures + 1))
done < "$tmpdir/plan.tsv"

say ""
if [ "$failures" -eq 0 ]; then
  say "Done. Folded $plan_count clone(s) into worktrees."
else
  say "Done with $failures failure(s)."
fi
