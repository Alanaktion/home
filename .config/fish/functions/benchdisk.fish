function benchdisk --description 'Benchmark the current disk'
  rm -f tempfile
  # Create temp file to test write speed
  echo Write speed:
  time dd if=/dev/zero of=tempfile bs=1M count=256 conv=fdatasync,notrunc status=progress
  # Clear buffer cache
  echo 3 | sudo tee /proc/sys/vm/drop_caches
  # Test read speed
  echo Uncached read speed:
  time dd if=tempfile of=/dev/null bs=1M count=256 status=progress
  # Test cached read speed
  echo Cached read speed:
  time dd if=tempfile of=/dev/null bs=1M count=256 status=progress
  rm tempfile
end
