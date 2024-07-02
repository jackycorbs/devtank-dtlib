#!/bin/bash

set -e

if [[ $# -ne 1 ]] ; then
    echo './create_empty_prod_tester.sh [project_name]'
    exit 0
fi

PRO_NAME=$(basename "$1")
echo Project name = $PRO_NAME

own_dir=$(dirname "$0")
dtlib_dir=$(readlink -f "$own_dir"/../..)
SUBM=$(git --git-dir="$dtlib_dir"/.git remote get-url origin)
echo Submodule - $SUBM
echo dtlib directory = $dtlib_dir
BRANCH=$(git --git-dir="$dtlib_dir"/.git branch --show-current)

{
    mkdir -p "$1"
} || {
    exit 0
}
git init "$1"
cd "$1"
echo Full path = $(readlink -f "$1")

git submodule add -b $BRANCH $SUBM dtlib
git commit -m "Added dtlib submodule to repository."
mkdir apps

echo About to copy examples and cli to apps
cp -R dtlib/apps/gui apps/"$PRO_NAME"_gui
cp -R dtlib/apps/cli apps/"$PRO_NAME"_cli

"$dtlib_dir"/docs/GettingStarted/rename.sh $PRO_NAME apps/

while read linkpath; do ln -sf "$(readlink $linkpath | sed 's|pylibapps|dtlib/pylibapps|g')" "$linkpath"; done <<< "$(find . -type l)"

sed -i 's|LIBDEVTANKROOT:=.*|LIBDEVTANKROOT:=../../dtlib|g' apps/*/Makefile

git add apps

git commit -m "Initial commit for new cookie cut GUI and CLI."

