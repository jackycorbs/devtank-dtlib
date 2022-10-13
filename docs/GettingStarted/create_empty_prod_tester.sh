#!/bin/bash
if [[ $# -eq 0 ]] ; then
    echo './create_empty_prod_tester.sh [project_name]'
    exit 0
fi

PRO_NAME=$(basename $1)
echo Project name = $PRO_NAME

SUBM=$(git remote get-url origin)
CWD=$(pwd)
echo current working directory = $CWD

{
    mkdir $1
} || {
    exit 0
}
git init $1
cd $1
echo Full path = $1

git submodule add $SUBM dtlib
git commit -m "Added dtlib submodule to repository."
mkdir apps
cd $CWD

echo About to copy template and cli to apps
cp -R ../../apps/template_gui $1/apps
cp -R ../../apps/template_cli $1/apps
echo $about to move $1/apps/template_gui to $1/apps/"$PRO_NAME"_gui

mv $1/apps/template_gui $1/apps/"$PRO_NAME"_gui
mv $1/apps/template_cli $1/apps/"$PRO_NAME"_cli
cd $1
./dtlib/docs/GettingStarted/rename.sh $PRO_NAME apps/
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

