# Distributed Runs

This page provides a general overview for how to run SPECjbb2015 in distributed mode, using SPECtate.
It assumes that you've read [the SPECjbb2015 user guide](https://www.spec.org/jbb2015/docs/userguide.pdf) and are familiar with setting up a distributed run manually.

## Overview

SPECtate uses [gRPC](https://grpc.io/docs/) to manage different SPECjbb components (backends, transaction injectors, the controller) through other instances of itself.

To set up your system(s) for a distributed run, you need:

- SPECtate with all its dependencies installed on each system.
- SSH access to each system using a non-interactive authentication method.
- Port `50051` open on each machine, to enable SPECtate to configure and manage its own instances.

### Getting Started

#### Configuration
To get started with a run, save a configuration file that might look something like this:

(`example.json`):
```json
{
	"TemplateData": {
		"HBIR": {
			"run_type": "distributed",
			"controller": {
				"hosts": [ 
					"foo:50051"
				]
			},
			"injectors": {
				"hosts": [
					"baz:50051"
				]
			},
			"args": [
				"Tag",
				"Kit Version",
				"JDK",
				"RTSTART",
				"JVM Options",
				"NUMA Nodes",
				"Data Collection",
				"T1",
				"T2",
				"T3"
			],
			"annotations" : {
			  "Tag" : "Name of the run",
			  "Kit Version" : "Version of SpecJBB",
			  "JDK" : "Version of the JVM that will run SpecJBB",
			  "RTSTART" : "What percentage of total output will we start at",
			  "JVM Options" : "What additional arguments, if any, will be passed to the JVM",
			  "NUMA Nodes" : "How many NUMA nodes will SpecJBB use",
			  "Data Collection" : "What data collection process will monitor while running SpecJBB",
			  "T1" : "How many threads does Tier 1 have access to",
			  "T2" : "How many threads does Tier 2 have access to",
			  "T3" : "How many threads does Tier 3 have access to"
			},
			"prop_options": {
				"specjbb.controller.type": "HBIR",
				"specjbb.time.server": false,
				"specjbb.comm.connect.client.pool.size": 192,
				"specjbb.comm.connect.selector.runner.count": 4,
				"specjbb.comm.connect.timeouts.connect": 650000,
				"specjbb.comm.connect.timeouts.read": 650000,
				"specjbb.comm.connect.timeouts.write": 650000,
				"specjbb.comm.connect.worker.pool.max": 320,
				"specjbb.mapreducer.pool.size": 27
			},
			"types": {
				"Tag": "string",
				"Kit Version": "string",
				"JDK": "string",
				"RTSTART": "integer",
				"JVM Options": "string",
				"NUMA Nodes": "integer",
				"Data Collection": "string",
				"T1": "integer",
				"T2": "integer",
				"T3": "integer"
			},
			"translations": {
				"RTSTART": "specjbb.controller.rtcurve.start",
				"T1": "specjbb.forkjoin.workers.Tier1",
				"T2": "specjbb.forkjoin.workers.Tier2",
				"T3": "specjbb.forkjoin.workers.Tier3",
				"NUMA Nodes": "specjbb.group.count"
			}
		},
	},
	"RunList": [{
			"template_type": "HBIR",
			"args": {
				"Tag": "TAG",
				"Kit Version": "15",
				"JDK": 7,
				"RTSTART": "4",
				"JVM Options": "options -x -y",
				"NUMA Nodes": "2",
				"Data Collection": "TRUE",
				"T1": 1,
				"T2": 2,
				"T3": 3
			}
		}
	]
}
```

This Tate config has one distributed run type that will have 2 groups (2 backends), each with the default of 1 injector per group, and injectors will be run on `baz`.
The controller will be run on `foo`.

Make sure that we've got ssh keys or agents setup on our current machine and those keys have been copied to `foo` and `baz`.

#### Running a SPECjbb2015 Distributed Benchmark

In one terminal, on `foo` and on `baz`:

```shell
python mainCLI.py listen
```

In another terminal, on the local machine:

```shell
python mainCLI.py run example.json
```

We should see SPECtate setup the necessary backends on the local machine, and the injectors on `baz` with a lot of output (depending on the level of logging you set).

## Details 
### Template Configuration Keys

More details on each of the templates can be found in the documentation for `src.validate`.

| Name         | Type                                                       | Brief Description                                                                                                              |
|--------------|------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `run_type`   | str (one of either `multi`, `distributed`, or `composite`) | The run type                                                                                                                   |
| `controller` | Component                                                  | SPECtate specific configuration options for the controller                                                                     |
| `injectors`  | Component or int                                           | SPECtate specific configuration options for the injectors. If int is given, it is interpreted as the injector per group count. |
| `backends`   | Component or int                                           | SPECtate specific configuration options for the backends. If int is given, it is interpreted as the backend count.             |
| `java`       | str                                                        | String to invoke the JVM on the local machine (also used as default if `java` isn't specified for any of the other components  |
| `port`       | str                                                        | Port to communicate to other SPECtate instances through                                                                        |

### Component Configuration Keys

| Name       | Type                                       | Description                                                          |
| ------     | ------                                     | -------------                                                        |
| `type`     | str (one of either of the component types) | The type of the component (passed to SPECjbb as `-m COMPONENT_TYPE`) |
| `count`    | int                                        | The number of instances (ignored for controllers)                    |
| `options`  | [str]                                      | A list of options to pass to SPECjbb                                 |
| `jvm_opts` | [str]                                      | A list of options to pass the the JVM for this component type        |
| `hosts`    | [str]                                      | A list of hostnames to use as hosts for these components             |
