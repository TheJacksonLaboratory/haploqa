# HOW TO RUN THESE TESTS
----------------------

> Currently the tests folder in the HaploQA project includes only tests that can be run using the python
unittest tool.

> You will run these tests from the project src directory (so that tests is a subdirectory).

> Before you can run these tests, you'll need to put the 'src' directory into your python path:
* * *

    export PYTHONPATH=src/

## Syntax for running tests
______________________

### To run one test file (all classes in the file)

    python -m unittest tests.test_haploqa

### Run in verbose mode *(recommended,  as this shows the test name being run and its relevant comments):*

    python -m unittest -v tests.test_haploqa

### To run one test class

    python -m unittest tests.test_haploqa.TestHaploQA

### To run one test

    python -m unittest tests.test_haploqa.TestHaploQA.test_home_page
