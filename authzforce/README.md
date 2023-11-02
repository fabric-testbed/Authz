# Overview

This directory is used by the test harness, you can put the .jar files from authzforce distribution, like authzforce-ce-core-pdp-cli-20.1.0.jar, into this folder. Note that the test harness uses a combination of the jar files here and the running PDP Docker container.

You can also add javalib/ folder in here to hold any missing java dependencies for starting the CLI jar above. For example

javalib/
├── jaxb-api-2.2.11.jar
├── jaxb-api-2.3.0.jar
└── jaxb-runtime-2.2.11.jar


