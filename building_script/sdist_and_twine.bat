@echo off

cd C:\Users\amcsparron\Desktop\Python_Projects\SQLLite3HelperClass
echo pwd changed to C:\Users\amcsparron\Desktop\Python_Projects\SQLLite3HelperClass
REM need LICENSE.txt README.md setup.cfg setup.py - see https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
REM DONT FORGET TO UPDATE setup.py, push commit to remote, and create a new release!! THEN run this!!!
echo running sdist setup
python setup.py sdist

echo running twine to update pypi
twine upload dist/*

