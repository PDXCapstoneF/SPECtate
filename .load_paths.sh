#!/usr/bin/env bash
#
# Since pyinstaller doesn't grab the correct import paths
# for our script, we need to do a little bit of screwing around
# with what it sees.
# Adding a pyinstaller spec file will allow us to tell where
# pyinstaller should look for imports and other things.
# 
# See: https://pythonhosted.org/PyInstaller/man/pyi-makespec.html
# for `--paths`: "Multiple paths are allowed, separated by ‘:’, or use this option multiple times"

# This assumes that the version of python that we're using is already
# activated (either by `pipenv shell` or some other virtualenv activation)
# and asks it where its importing its modules.
# It's fair to say that if `python mainCLI.py` doesn't work, then this
# script will fail to grab the correct paths, and everything will fall apart.
cmd='import sys;
print(":".join([p for p in sys.paths if "site" in p]))'

pyi-makespec --onefile --paths "$(cmd)" mainCLI.py
pyinstaller mainCLI.spec
