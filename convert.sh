#!/bin/bash

# Reset in case getopts has been used previously in the shell.
OPTIND=1

FORCE=0
FORCE_FAILURES=0
FORCE_FILES=()

# Search for files containing either
# - IMSC       - Sequence digrams
# - IUCDiagram - Usecase diagrams
# - IDiagram   - Class/Object digrams
PATTERN='{ IMSC\|{ IUCDiagram\|{ IDiagram'

while getopts "h?f" opt; do
    case "$opt" in
        h|\?)
            echo "Usage: $0 <path to convert sbs-files>"
            echo ""
            echo " Arguments:"
            echo " -f continue even there is parser failures"
            exit 1
            ;;
        f)  FORCE=1
            ;;
    esac
done

shift $((OPTIND-1))
DIR="$1"
[ ! -d $DIR ]  && { echo "Path not existing: $DIR"; exit 1; }

while read -r file ; do

    # Convert each sbs to xml
    echo "Converting: $file"
    cat $file | sbs2xml/build/sbs2xml > ${file}.xml

    if [ $? -ne 0 ]; then
        if [ $FORCE -ne 0 ]; then
            FORCE_FAILURES=$((FORCE_FAILURES + 1))
            FORCE_FILES+=($file)
            echo "  Failed to convert file to xml. Forced continuation.."
        else
            echo "  Failed to convert file to xml!!"
            echo ""
            echo "Check end of file for more detail:"
            echo ${file}.xml
            exit 1
        fi
    fi

    # Convert each sbs.xml to diagrams
    echo "Parsing: ${file}.xml"
    xml2plant/xml2plant.py -g ${file}.xml

    if [ $? -ne 0 ]; then
        if [ $FORCE -ne 0 ]; then
            FORCE_FAILURES=$((FORCE_FAILURES + 1))
            FORCE_FILES+=($file)
            echo "  Failed to parse file. Forced continuation.."
        else
            echo "  Failed to parse file!!"
            echo ""
            exit 1
        fi
    else
        # Remove temporary file
        rm ${file}.xml
    fi

done < <(grep --include *.sbs -rl -e "$PATTERN" $DIR )  # process substitution

# Show results
echo ""
if [ $FORCE -ne 0 ] && [ $FORCE_FAILURES -ne 0 ]; then
    echo "Number of failures: ${FORCE_FAILURES}"
    printf '%s\n' "${FORCE_FILES[@]}"
else
    echo "Done"
fi
echo ""
