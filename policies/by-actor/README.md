# Overview

This  folder contains implementations of policies for individual Control Framework actors and example requests in XML and JSON. These are expected to be executed by an XACML [Docker PDP](https://github.com/fabric-testbed/fabric-docker-images/tree/master/authzforce-pdp).

Most of the details for running tests described in the [README](../README.md) file apply here.

Different folders contain different sets of policies applicable to different conditions:

- [Policies that alwаys say 'Yes' (SimpleYes)](SimpleYes) - these policies for Orchestrator, Broker and Aggregate Managers are structured according to the expected categories of attributes for principals, users and actions, however regardless of the request always return 'Permit' so long as the request contains the expected attributes, and produce an error otherwise.
- [Policies that take into account project tags](ProjectTags) - this policy for Orchestrator (Broker and AM assumed to use SimpleYes policies) are structured to support project tags extracted from the user token to allow or not allow specific types of resources or sizes of slices. The principal must be part of a valid project. The policy looks at sliver features and dimensions. Prior to forming the PDP request for the entire slice, for features a logical 'OR' is applied across all slivers (so if any sliver has a feature, the request has a feature), for dimensions a max(all_slivers) are used. 
