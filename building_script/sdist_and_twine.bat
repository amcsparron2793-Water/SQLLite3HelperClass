@echo off

cd C:\Users\amcsparron\Desktop\Python_Projects\SQLLite3HelperClass
echo pwd changed to C:\Users\amcsparron\Desktop\Python_Projects\SQLLite3HelperClass

REM DONT FORGET TO UPDATE setup.py, push commit to remote, and create a new release!! THEN run this!!!
echo running sdist setup
python setup.py sdist

echo running twine to update pypi
twine upload dist/*

