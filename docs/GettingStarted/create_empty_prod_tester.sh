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

{
    mkdir -p "$1"
} || {
    exit 0
}
git init "$1"
cd "$1"
echo Full path = $(readlink -f "$1")

git submodule add $SUBM dtlib
git commit -m "Added dtlib submodule to repository."
mkdir apps

echo About to copy template and cli to apps
cp -R "$dtlib_dir"/apps/template_gui apps
cp -R "$dtlib_dir"/apps/template_cli apps
echo $about to move $1/apps/template_gui to $1/apps/"$PRO_NAME"_gui

mv apps/template_gui apps/"$PRO_NAME"_gui
mv apps/template_cli apps/"$PRO_NAME"_cli

"$dtlib_dir"/docs/GettingStarted/rename.sh $PRO_NAME apps/
cd apps/"$PRO_NAME"_cli
rm -r example_lib resources tests
ln -s ../"$PRO_NAME"_gui/"$PRO_NAME"_lib
ln -s ../"$PRO_NAME"_gui/resources
ln -s ../"$PRO_NAME"_gui/tests
git add Makefile "$PRO_NAME"_tester_cli.py
cd ../"$PRO_NAME"_gui
git add "$PRO_NAME"_lib "$PRO_NAME"_lib_gui "$PRO_NAME"_tester_gui.py resources tests Makefile
git commit -m "Initial commit for new template GUI and CLI."
make clean; make; make local_db_clean

