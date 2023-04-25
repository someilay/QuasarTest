## About
* Test project for Quasar, details [here](Assignment_Python_Developer.pdf)

## Requirements
* Python 3.11+
* Linux (5.10.0++)

## Configuration
* `git clone https://github.com/someilay/QuasarTest.git`
* `cd QuasarTest`
* `python3.11 -m venv venv`
* `source venv/bin/activate`
* `pip install -r requirments`
* If you already have a ready sqLite database copy it to `QuasarTest` as `local.db`,
* Otherwise, run `python3 gen_data.py`

## Run
* `python3 main.py`

## Test 
* `python3 -m unittest test/*.py`

## API Documentation
* [index.html](index.html)
