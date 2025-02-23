function gifv --description 'Convert GIF to WebM'
  # Requires my imgfind python package
  teeny -r --glob '*.gif' --gif webm .
end
