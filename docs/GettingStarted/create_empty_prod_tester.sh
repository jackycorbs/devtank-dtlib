#!/bin/bash

SUBM=$(git remote get-url origin)
CWD=$(pwd)
mkdir ~/$1
git init ~/$1
cd ~/$1
git submodule add $SUBM dtlib
git commit -m "Added dtlib submodule to repository."
mkdir apps
cd $CWD
cp -R ../../apps/template_gui ~/$1/apps
cp -R ../../apps/template_cli ~/$1/apps
mv ~/$1/apps/template_gui ~/$1/apps/$1_gui
mv ~/$1/apps/template_cli ~/$1/apps/$1_cli
cd ~/$1
./dtlib/docs/GettingStarted/rename.sh $1 apps/
cd apps/$1_cli
rm -r example_lib resources tests
ln -s ../$1_gui/$1_lib
ln -s ../$1_gui/resources
ln -s ../$1_gui/tests
git add Makefile $1_tester_cli.py
cd ../$1_gui
git add $1_lib $1_lib_gui $1_tester_gui.py resources tests Makefile
git commit -m "Initial commit for new template GUI and CLI."
make clean; make; make local_db_clean
