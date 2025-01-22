# Testing `psymple`

`psymple` contains a suite of tests which are automatically run through GitHub.

## Current tests

The link below will take you to the current directory of tests, which are stored in the `/tests` directory.

[Current tests](https://github.com/casasglobal-org/psymple/tree/main/tests){ .md-button }

## Manually running tests

The best way to run the tests is either through an IDE such as [VSCode](https://code.visualstudio.com/), or in the command line using the `tox` package, as follows.

### Requirements

Running Python version `3.10` or higher.

### Running tests

The following commands install `tox`, setup a test suite, and run the tests.

#### Install `tox`

```
pip install tox
```

#### Setting up the test suite

```
tox -vv --notest
```

#### Running the tests

```
tox --skip-pkg-install
```

## Writing new tests

If you would like to contribute a new test, or you have found a feature which is not tested, then feel free to either create an [issue](https://github.com/casasglobal-org/psymple/issues) or [pull request](https://github.com/casasglobal-org/psymple/pulls). All test files must be contained in the `/tests` directory and have a name of the form `test_*.py`.