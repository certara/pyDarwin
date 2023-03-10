# [pyDarwin](https://certara.github.io/pyDarwin/html/index.html)

Python solution for using several machine learning methods to search a candidate solution space for the optimal population models in NONMEM.

Visit [pyDarwin Documentation](https://certara.github.io/pyDarwin/html/index.html) to learn more.

## System Requirements

* Windows 10
* Windows Server 2018, 2019
* CentOS8/RHEL8
* Ubuntu >= 18.04

###  Grid Computing Support
* Sun Grid Engine (SGE)

## Installation Prerequisites

* Python >= 3.10
* NONMEM >= 7.4.3
* R >= 4.0.0 (optional)

*Note: Requirements are Python and NONMEM installation with nmfe.bat available. R is required if using post-run R penalty function.*


## Installation

First, create a new virtual environment: 

`python -m venv .venv`

This will create a virtual environment in the folder `.venv`

Next, use `pip` to install the `pyDarwin` package from the Certara managed `PyPi` repo:

### Released Version

`pip install pyDarwin-Certara --index-url https://certara.jfrog.io/artifactory/api/pypi/certara-pypi-release-public/simple --extra-index-url https://pypi.python.org/simple/`

### Development Version

`pip install pyDarwin-Certara --index-url https://certara.jfrog.io/artifactory/api/pypi/certara-pypi-develop-local/simple --extra-index-url https://pypi.python.org/simple/`

## Usage

`python -m darwin.run_search <template_path> <tokens_path> <options_path>`

To execute, call the `run_search` function from the `darwin` module and provide the following file paths as arguments:

1. Template file (e.g., template.txt) - basic shell for NONMEM control files
2. Tokens file (e.g., tokens.json) - json file describing the dimensions of the search space and the options in each dimension
3. Options file (e.g., options.json) - json file describing algorithm, run options, and post-run penalty code configurations.

### Example

After cloning https://github.com/certara/pyDarwin from GitHub, navigate to one of the example folders e.g., 

`cd .\pyDarwin\examples\user\Example1`

Then execute:

`python -m darwin.run_search template.txt tokens.json options.json`

*Note: Both absolute and relative file paths are supported.*
