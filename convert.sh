#!/bin/bash

[ $# -eq 0 ] && { echo "Usage: $0 <path to convert sbs-files>"; exit 1; }
[ ! -d $1 ]  && { echo "Path not existing: $1"; exit 1; }

DIR="$1"

# Search for files containing either
# - IMSC       - Sequence digrams
# - IUCDiagram - Usecase diagrams
# - IDiagram   - Class/Object digrams
PATTERN='{ IMSC\|{ IUCDiagram\|{ IDiagram'

grep --include *.sbs -rl -e "$PATTERN" $DIR | while read -r file ; do

    # Convert each sbs to xml
    echo "Converting: $file"
    cat $file | sbs2xml/build/sbs2xml > ${file}.xml

    if [ $? -ne 0 ]; then
        echo "  Failed to convert file to xml!!"
        echo ""
        echo "Check end of file for more detail:"
        echo ${file}.xml
        exit 1
    fi

    # Convert each sbs.xml to diagrams
    echo "Parsing: ${file}.xml"
    xml2plant/xml2plant.py -g ${file}.xml

    if [ $? -ne 0 ]; then
        echo "  Failed to parse file!!"
        echo ""
        exit 1
    fi

done
