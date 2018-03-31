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



## Testing

* Unittests 

* Continuous integration


## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/PDXCapstoneF/SPECtate/blob/dev/README.md) file for details

## Authors

