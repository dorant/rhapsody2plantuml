#!/bin/bash
BASEDIR=$(dirname $0)

# Reset in case getopts has been used previously in the shell.
OPTIND=1

VERBOSE=0
FORCE=0
RENAME=0
DEBUG=0
FORCE_FAILURES=0
FORCE_FILES=()
NO_OF_FILES=0

# Search for files containing either
# - IMSC       - Sequence digrams
# - IUCDiagram - Usecase diagrams
# - IDiagram   - Class/Object digrams
PATTERN='{ IMSC\|{ IUCDiagram\|{ IDiagram'

while getopts "h?vfrd" opt; do
    case "$opt" in
        h|\?)
            echo "Usage: $0 <path to convert sbs-files>"
            echo ""
            echo " Arguments:"
            echo " -v  Verbose log loutput"
            echo " -f  Continue even there is parser failures"
            echo " -r  Rename destination paths to a folder without the postfix '_rpy'"
            echo " -d  Debug: temporary xml-files not removed"
            exit 1
            ;;
        v)  VERBOSE=1
            ;;
        f)  FORCE=1
            ;;
        r)  RENAME=1
            ;;
        d)  DEBUG=1
            ;;
    esac
done

shift $((OPTIND-1))
FILE_OR_DIR="$1"

[[ $VERBOSE -ne 0 ]] && verbose_flag="-v"
[[ $RENAME -ne 0 ]] && rename_flag="-r"


function convert_file() {
    file=$1

    # Convert each sbs to xml
    echo "Converting: $file"
    cat $file | $BASEDIR/sbs2xml/build/sbs2xml > ${file}.xml
    NO_OF_FILES=$((NO_OF_FILES + 1))

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
    echo "   Parsing: ${file}.xml"
    $BASEDIR/xml2plant/xml2plant.py ${verbose_flag} ${rename_flag} -g ${file}.xml

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
        if [ $DEBUG -ne 1 ]; then
            # Remove temporary file
            rm ${file}.xml
        fi
    fi
}


if [ -d $FILE_OR_DIR ]; then
    while read -r file ; do
        convert_file $file
    done < <(grep --include *.sbs -rl -e "$PATTERN" $FILE_OR_DIR )  # process substitution
elif [ -f $FILE_OR_DIR ]; then
    convert_file $FILE_OR_DIR
else
    echo ""
    echo "The given path is not a valid directory or file:"; echo $FILE_OR_DIR; echo "";
    exit 1;
fi

# Show results
echo ""
if [ $FORCE -ne 0 ] && [ $FORCE_FAILURES -ne 0 ]; then
    echo "Number of failures: ${FORCE_FAILURES} of ${NO_OF_FILES}"
    printf '%s\n' "${FORCE_FILES[@]}"
else
    echo "Done. ${NO_OF_FILES} files converted."
fi
echo ""
