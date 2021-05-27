#! /bin/bash

if [ $# -ne 1 ]; then
    echo "1 argument expected"
    exit -1
fi
name=$1

find . -type d -exec rename -v "s/example/$name/" {} +
#echo "Replaced directory names with : '$name'"

find . -type f -exec rename -v "s/example/$name/" {} +
#echo "Replaced filenames with : '$name'"

find . -type f -exec sed -i -e "s/example/$name/g" {} +
#echo "Replaced contents with : '$name'"
