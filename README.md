# SPECTate

This uses python 3.6.4.

## Developing

Use [`pipenv`](https://docs.pipenv.org/): `pip install pipenv`.

```
$ pipenv install
$ pipenv check
$ pipenv shell
$ # hack away
```

## Contributing

Using a git-flow workflow. Minimum 2 PR to get into `dev`, releases on `master`:

1. Create new feature branch
1. Do work, commit
1. Make sure you're up to date with `dev`
1. Submit a PR request in the GitHub UI to `dev` (optionally tag people that would be interested in the PR)
1. Wait for any two or more people to come along and do code review 
1. Merge into `dev`
1. Delete the feature branch
