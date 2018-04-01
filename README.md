| Service        | Master           | Development  |
| ------------- |:-------------:| ------------------:|
| CI Status      | [![Build Status](https://travis-ci.org/PDXCapstoneF/SPECtate.svg?branch=master)](https://travis-ci.org/PDXCapstoneF/SPECtate)    | [![Build Status](https://travis-ci.org/PDXCapstoneF/SPECtate.svg?branch=dev)](https://travis-ci.org/PDXCapstoneF/SPECtate) |


# SPECtate

SPECtate is a configuration tool that interfaces with the benchmarking software [SPECjbb®2015](https://www.spec.org/jbb2015/). SPECtate is designed to to be a more user-friendly alternative for configuring and invoking the SPECjbb®2015 benchmarking software, providing: 

**Interfaces:**
* a graphical-user-interface (GUI) 
* a command-line-interface (CLI)

**Configuration:**
* processes human-readable configuration files (HJSON, JSON, YAML)

**Invocation:**
* a python-equivalent of SPECjbb®2015's `run.sh` file.


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See usage for notes on how to use the project on a live system.

### Prerequisites

* UNIX (Linux, Mac OSX), or Windows
* python >= 2.6
* SPECjbb®2015


### Setup

```
$ git clone https://github.com/PDXCapstoneF/SPECtate.git
$ cd SPECtate/
$ python -m unittest discover -s .
```


## Example CLI Usage

* Generate configurations, including run-type, java options, ... (example session)

* Invoke SPECjbb using json/hjson/yaml file


## Documentation

* SPECtate documentation can be found on the project [wiki](https://github.com/PDXCapstoneF/SPECtate/wiki) page and in the Python scripts themselves. Documentation of SPECtate scripts can be generated directly by using Python's standard library `pydoc`.

Example:

```
$ cd SPECtate/
$ pydoc -w dialogue; open dialogue.html
```

The `-w` flag in the above command will "Write out the HTML documentation for a module to a file in the current directory."

## Testing

* Unittests 

* Travis-CI for Continuous integration testing during development


## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/PDXCapstoneF/SPECtate/blob/dev/README.md) file for details.

## Contact

* [Andrew Waugh](mailto:**************@pdx.edu) (Product Owner)
