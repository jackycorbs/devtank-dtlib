#!/bin/bash

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

dirs=("$(find "$dir" -type d)")
rn "${dirs[@]}"
files=("$(find "$dir" -type f)")
rn "${files[@]}"
sed -i "s/$replace/$name/g" ${files[@]//$replace/$name}
