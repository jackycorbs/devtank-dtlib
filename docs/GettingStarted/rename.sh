#!/bin/bash

# If you get errors, try running this script again.

rn(){
    arr=("$@")
    rename -v "s/$replace/$name/" ${arr[@]}
}

if [ -z "$1" ]; then
    echo "$0 <new-name> [replace-dir]"
    exit -1
fi

replace="example"
name=$1
dir='.'
[ -n "$2" ] && dir="$2"

files=("$(find "$dir" -type f)")
all=("$(find "$dir" -type d)")
all+=("${files[@]}")

rn "${all[@]}"
sed -i "s/$replace/$name/g" ${files[@]//$replace/$name}
