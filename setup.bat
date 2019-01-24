@echo off
rmdir /s /q build
rmdir /s /q appointed2.egg-info
rmdir /s /q dist
python setup.py install