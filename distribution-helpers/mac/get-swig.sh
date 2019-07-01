#!/bin/bash

echo Getting SWIG ready

mkdir -p ~/swig
cd ~/swig

echo Installing PCRE
brew install pcre

echo Download SWIG
curl -L "https://osdn.net/frs/g_redir.php?m=kent&f=swig%2Fswig%2Fswig-3.0.12%2Fswig-3.0.12.tar.gz" > swig-3.0.12.tar.gz
tar xvzf swig-3.0.12.tar.gz

echo Compiling SWIG
cd swig-3.0.12
./configure --prefix=/usr
make

echo SWIG is availabךe at `which swig`

