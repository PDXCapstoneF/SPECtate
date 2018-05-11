# Distributed Runs

This page provides a general overview for how to run SPECjbb2015 in distributed mode, using SPECtate.
It assumes that you've read [the SPECjbb2015 user guide](https://www.spec.org/jbb2015/docs/userguide.pdf) and are familiar with setting up a distributed run manually.

## Overview

SPECtate uses [gRPC](https://grpc.io/docs/) to manage different SPECjbb components (backends, transaction injectors, the controller) through other instances of itself.

To set up your system(s) for a distributed run, you need:
- SPECtate with all its dependencies installed on each system.
- SSH access to each system using a non-interactive authentication method.
- Port `50051` open on each machine, to enable SPECtate to configure and manage its own instances.

### Configuration Keys

| Name         | Type                                                       | Brief Description                                                                                                              |
|--------------|------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `run_type`   | str (one of either `multi`, `distributed`, or `composite`) | The run type                                                                                                                   |
| `controller` | Component                                                  | SPECtate specific configuration options for the controller                                                                     |
| `injectors`  | Component or int                                           | SPECtate specific configuration options for the injectors. If int is given, it is interpreted as the injector per group count. |
| `backends`   | Component or int                                           | SPECtate specific configuration options for the backends. If int is given, it is interpreted as the backend count.             |
| `java`       | str                                                        | String to invoke the JVM on the local machine (also used as default if `java` isn't specified for any of the other components  |
| `port`       | str                                                        | Port to communicate to other SPECtate instances through                                                                        |
