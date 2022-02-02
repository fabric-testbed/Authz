# Overview


This is the home for ALFA-generated policies. It contains
- Attribute definitions [standard](standard-attributes.alfa) and [FABRIC-specific](fabric-attributes.alfa)
- [src-gen](src-gen) directory where VS Code ALFA plugin deposits compiled XACML. Note that the XML files are named after the top-level ALFA policy or policy set in corresponding ALFA file
- Directories for different policy implementations:
    - [Test policies](TestPolicies)
    - [Simple always 'yes'](FabricAlwaysYes)
    - [Project-tag based Orchestrator policy](FabricOrchestratorProjectTags)