# Working in Virtual Environments

`SPECtate` uses [`pipenv`](https://github.com/pypa/pipenv) to manage python installs and dependencies.

There's a fairly straightforward [wiki here, which is more or less the GitHub readme with some additional comments from the maintainers](https://docs.pipenv.org/).

The whole idea boils down to:

- You want to know what to install
- You want to know what versions to require
- You want builds and installs to be deterministic (no chance for setup failure)
- You don't want to manage all the details that require the above to work

`pipenv` more or less works as a [`yarn`](https://yarnpkg.com/lang/en/docs/getting-started/) or a [`dep`](https://gist.github.com/subfuzion/12342599e26f5094e4e2d08e9d4ad50d) for python, providing lockfiles and install commands for easy setup.

## Basic Workflow

1. Clone the repo
1. `pipenv shell` - drops you into a shell where you're using `SPECtate`'s version of python and its dependencies
1. `pipenv check` - ensures you have everything you need (resolve conflicts, error on wrong versions of python, etc)

Installing additional packages is as easy as `pipenv install <package>`. 
`pipenv --help` can give you more information and specifics, if you need to do something more involved.