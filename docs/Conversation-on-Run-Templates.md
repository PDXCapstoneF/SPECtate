## Run Types
```
{
  "HBIR": {
    "userargs": [
      "T1"
    ],
    "annotation": {
      "someArg": "This is an example of an argument that gets put into a populated .props file."
    },
    "types": {
      "someArg": "string",
    },
    "translation": {
      "someArg": "com.spec.something"
    }
  }
}
```

TODO: Add more extensive notes.

## Run Lists
Also talked about run lists.

These are the things that SPECtate is going to use to construct a benchmarking run. How many injectors? How many backends? What values go into the `userargs` defined above? etc.
```
[
{
  "tag": "value",
  "runtype": "HBIR",
  "numa_nodes": 4,
  "backends": 20
},
...
]
```