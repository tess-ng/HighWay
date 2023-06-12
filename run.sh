#!/bin/sh

sudo su
chmod -R a+rw ./*
export LD_LIBRARY_PATH=$PWD:$LD_LIBRARY_PATH
sudo python main.py
