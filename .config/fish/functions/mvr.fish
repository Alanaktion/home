function mvr --wraps rsync
  if test (uname -s) = "Darwin"
    rsync --archive -hh --partial --progress --modify-window=1 --remove-source-files $argv
  else
    rsync --archive -hh --partial --info=stats1,progress2 --modify-window=1 --remove-source-files $argv
  end
end
