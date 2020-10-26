# Overview

This  folder contains implementations of policies for individual Control Framework actors and example requests in XML and JSON. These are expected to be executed by an XACML [Docker PDP](https://github.com/fabric-testbed/fabric-docker-images/tree/master/authzforce-pdp).

Most of the details for running tests described in the [README](../README.md) file apply here.

Different folders contain different sets of policies applicable to different conditions:

- [Policies that alwаys say 'Yes' (SimpleYes)](SimpleYes) - these policies for Orchestrator, Broker and Aggregate Managers are structured according to the expected categories of attributes for principals, users and actions, however regardless of the request always return 'Permit' so long as the request contains the expected attributes, and produce an error otherwise.
