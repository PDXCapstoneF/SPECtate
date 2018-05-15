Based on the conversation today at the library, we've decided to go in the direction of having a single JSON file for everything.

# Glossary

## Run

The information needed to perform a single invocation of SpecJBB. This currently looks like the following:

    {
        "template_type" : "HBIR",
        "args" : {
            "arg1" : 5,
            "arg2" : "foobar",
            "arg3" : false
        }
    }

TODO: There's a possibility of adding a third key-value pair to each Run, called `props_extra`. This would provide an opportunity to give fine-tuning capability for each Run. This is not necessary, and we're not even sure if we should put it in. But it's a possibility.

## Template

 The information needed to

* Determine which `args` are needed from the user. (`args`)
* Determine which type each `arg` is. (`types`)
* Determine the correspondence between `args` and `.props` properties. (`translations`)
* Provide default properties that will **always** be written to the `.props` files (`default_props`).
* Provide annotations for each `arg` for dialogue.

An example of this is the following:

    { 
        "args" : [
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

        "types" : { 
          "Tag" : "string",
          "Kit Version" : "string",
          "JDK" : "string",
          "RTSTART" : "integer",
          "JVM Options" : "string",
          "NUMA Nodes" : "integer",
          "Data Collection" : "string",
          "T1" : "integer",
          "T2" : "integer",
          "T3" : "integer"
        },  

        "translations" : { 
          "RTSTART" : "specjbb.controller.rtcurve.start",
          "T1" : "specjbb.forkjoin.workers.Tier1",
          "T2" : "specjbb.forkjoin.workers.Tier2",
          "T3" : "specjbb.forkjoin.workers.Tier3",
          "NUMA Nodes" : "specjbb.group.count"
        },

        "default_props" : {
          "specjbb.controller.type" : "HBIR",
          "specjbb.time.server" : false,
          "specjbb.comm.connect.client.pool.size" : 192,
          "specjbb.comm.connect.selector.runner.count" : 4,
          "specjbb.comm.connect.timeouts.connect" : 650000,
          "specjbb.comm.connect.timeouts.read" : 650000,
          "specjbb.comm.connect.timeouts.write" : 650000,
          "specjbb.comm.connect.worker.pool.max" : 320,
          "specjbb.customerDriver.threads" : 64,
          "specjbb.customerDriver.threads.saturate" : 144,
          "specjbb.customerDriver.threads.probe" : 96,
          "specjbb.mapreducer.pool.size" : 27
        }
    }


### Args

**Run-specific** values that are specified by the user. In a Template, this is an **ordered list** to provide a common order for inputting values inside a dialogue.

### Properties

A property is a single line in the `.props` file that will be passed to SPECjbb.

### Translations

A translation maps an Arg to a Property.

### Annotations

A description maps an Arg to a human-readable description of what the argument actually means.

### Types

A type is the data type that an Arg must be. This is for validation.

## RunList

An **ordered list** of Runs.

For example:

    [
        {
            "template_type" : "HBIR",
            "args" : {
                "arg1" : 5,
                "arg2" : "foobar",
                "arg3" : false
            }
        },

        {
            "template_type" : "HBIR_RT",
            "args" : {
                "arg1" : "muffin"
                "arg2" : 42,
                "arg3" : "spam",
                "arg4" : true
            }
        }
    ]

## TemplateData

A key-value pair that maps **template types** to Templates.

For example:

    {
        "HBIR" : {
            "args" : [],
            "default_props" : {},
            "types" : {},
            "translations" : {}
        },

        "HBIR_RT" : {
            "args" : [],
            "default_props" : {},
            "types" : {},
            "translations" : {}
        }
    }

## TateConfig

A JSON file that contains an object with two values: a TemplateData object and a RunList object.

For example:

    {
        "TemplateData" : {
            "HBIR" : {
                "args" : [],
                "default_props" : {},
                "types" : {},
                "translations" : {}
            },

            "HBIR_RT" : {
                "args" : [],
                "default_props" : {},
                "types" : {},
                "translations" : {}
            }
        },

        "RunList" : [
            {
                "template_type" : "HBIR",
                "args" : {
                    "arg1" : 5,
                    "arg2" : "foobar",
                    "arg3" : false
                }
            },

            {
                "template_type" : "HBIR_RT",
                "args" : {
                    "arg1" : "muffin"
                    "arg2" : 42,
                    "arg3" : "spam",
                    "arg4" : true
                }
            }
        ]
    }

# Dialogue Treatment

* This means that Dialogue programs only have to open one file.

* Most code can remain unchanged; the only difference is that instead of writing to two separate JSON files, the RunList and Template Data objects are saved as values of an overarching TateConfig file.

# Main Program Treatment

This is more complicated. Let's list the interactions.

* Dialogue creates or edits a TateConfig file and saves it.

* Main program opens the TateConfig file.

* Main program parses the RunList and selects a Run.

---

## For each run...

* Main program grabs the `template_type` attribute of the Run.

* Main program goes to the `TemplateData` attribute of the TateConfig file and selects that specific Template.

### For each value in `translations`...

* Get the corresponding value for `arg` from the Run.

* Write it to the `.props` file.

### For each value in `props_default`...

* Write it. No extra stuff needs to happen here.

---

Now that we've written the `.props` file, we can do the JVM invocation.

* Construct the JVM invocation(s). using the Run's `args` and `template_type`.

* Call the JVM.