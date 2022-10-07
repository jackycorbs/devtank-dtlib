#!/bin/bash

CWD=$(pwd)
echo $CWD
mkdir ~/$1
git init ~/$1
cd ~/$1
git submodule add git.devtank.co.uk:/git/devtank-dtlib dtlib
mkdir apps
cd $CWD
cp -R ../../apps/template_gui ~/$1/apps
cp -R ../../apps/template_cli ~/$1/apps
cd ~/$1
./dtlib/docs/GettingStarted/rename.sh $1 apps/
cd apps/template_cli
rm -r example_lib resources tests
ln -s ../template_gui/$1_lib
ln -s ../template_gui/resources
ln -s ../template_gui/tests
