# Contributing to SARPy

SARPy is a Python package that is intended to simplify working with the NGA SAR
standards: Compensated Phase History Data (CPHD), Sensor Independent Complex
Data (SICD), and Sensor Independent Derived Data (SIDD).

The package has three subpackages with different roles.

- standards: A reference implementation of the NGA standards with minimal external dependencies to maximize useability in many contexts.
- verification: Uses additional dependencies to test compliance with the NGA standards.  These additional dependencies are not needed to work with the formats.
- processing: Contains SAR processing that is not defined in a standard, but has proven to be useful and commonplace.

## Getting started with development

### Setup

#### Clone the sarpy2\_prototype repository

```bash
git clone git@github.com:ngageoint/sarpy2_prototype.git
cd sarpy2_prototype
```

#### Create and activate an environment for SARPy

The default and supported way to create an environment for SARPy is creating
a python virtual environment.

```bash
python -m venv ./venv
source ./venv/bin/activate
```

Other environment managers, such as conda, may be used to create and activate
an environment.  For simplicity, examples will use the built-in Python virtual
environments.

#### Package installation

Once a SARPy environment is created and activated, you can install the packages
into your environment with pip from the package root.

```bash
python -m pip install .
```

Installing without packaging extras will only ensure that sarpy.standards
is fully supported.  Other packages will have reduced functionality.

The packaging extras are listed below:

- verification
- processing
- all
- dev-lint
- dev-test
- dev

Any union of these dependencies can be installed simultaneously by specifying
the individual dependency groups in brackets, comma delimited.  The dependencies
for the standards subpackage is installed by default, as that is the core
functionality.

The following install command would install all dependencies for
the standards subpackage and allow for linting and testing.  mypy works best with
an editable install.

```bash
python -m pip install --editable .[dev]
```

It is recommended that, whenever possible, contributors install all optional
dependencies so that all unit tests can be run prior to submission of a
Pull Request.

```bash
python -m pip install --editable .[all,dev]
```

### Running tests

In the development environment, SARPy unit tests can be run with pytest.

```bash
pytest tests
```

Unit tests are organized by subpackage so that the unit tests for the standards
can be run as below.

```bash
pytest tests/standards
```

### Building distributions

A wheel can be created using pip and the included pyproject.toml.
The specified backend is pdm-backend, so that must either be installed
or available through pip channels.

After the following command is run successfully, the wheel will be located
in ./dist

```bash
pip wheel . --no-deps -w dist
```

## Submitting changes

Even more excellent than a good bug report is a fix for a bug, or the
implementation of a much-needed new feature. We'd love to have
your contributions.

### Pre-PR checking

Prior to submitting your contribution through a Pull Request, the lint and
unit tests should be run and pass cleanly.

The linting will require the `dev-lint` dependencies to be installed and can
be done with the following:

```bash
ruff check
mypy sarpy
```

If the linting does not pass cleanly, the following commands can be used to
automatically fix some formatting errors.

```bash
ruff check --fix
ruff format
```

### Pull Request process

We use the usual GitHub pull-request flow, which may be familiar to
you if you've contributed to other projects on GitHub.  For the mechanics,
see [GitHub's documentation](https://help.github.com/articles/using-pull-requests/).

Anyone interested in SARPy may review your code.  One of the SARPy core
developers will merge your pull request when they think it's ready.

If your change will be a significant amount of work
to write, we highly recommend starting by opening an issue laying out
what you want to do.  That lets a conversation happen early in case
other contributors disagree with what you'd like to do or have ideas
that will help you do it.

The best pull requests are focused, clearly describe what they're for
and why they're correct, and contain tests for whatever changes they
make to the code's behavior.  As a bonus these are easiest for someone
to review, which helps your pull request get merged quickly!  Standard
advice about good pull requests for open-source projects applies.

Also, do not squash your commits after you have submitted a pull request, as this
erases context during review. We will squash commits when the pull request is merged.
