function split4g -a file -d 'Split files into 4GB parts' 
  split -b 4GB -a 3 --numeric-suffixes=1 $file "$file." && rm -i $file
end
