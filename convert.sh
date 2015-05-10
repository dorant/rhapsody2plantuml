#!/bin/bash

[ $# -eq 0 ] && { echo "Usage: $0 <path to convert sbs-files>"; exit 1; }
[ ! -d $1 ]  && { echo "Path not existing: $1"; exit 1; }

DIR="$1"

# Search for files containing either
# -IMSC       - Sequence digrams
# -IUCDiagram - Usecase diagrams
# -IDiagrma   - Class/Object digrams
PATTERN='{ IMSC\|{ IUCDiagram\|{ IDiagram'

grep --include *.sbs -rl -e "$PATTERN" $DIR | while read -r file ; do

    # Convert each file
    echo "Converting: $file"
    cat $file | sbs2xml/build/sbs2xml > ${file}.xml
done
