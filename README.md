# Overview

This repository defines FABRIC authorization policies using a combination of CILogon and ALFA and XACML3.0.

FABRIC relies on a federated identity model and a combination of RBAC and ABAC (Role- and Attribute-Based Access Control). RBAC is used for managing user rights, while ABAC is used for authorizing resource allocations by those users. Each identity comes with a mix of attributes, some asserted by the institutional IdP (Identity Provider) and some via a FABRIC-specific mechanism (e.g. CoManage). Resource attributes are collected and provided by the FABRIC Control Framework. These attributes are then provided to the authorization system in a secure way in order to allow it to make access decisions to various protected APIs. Attributes are also attached to resources and other constructs to help the AuthZ system make necessary decisions.

The design of the policies follows the approach defined [here](https://stackoverflow.com/questions/41473752/complex-authorization-using-xacml) in defining the specification.

Privileges in FABRIC are granted based on attributes attached to principals and resources. Some principal attributes reflect membership in sets/groups. Each group, referred to as a `project` has a specific set of rights limiting their use of resources on a specific subset of aggregates. Resource provisioning is limited to two levels - that of a control framework orchestrator (could be multiple orchestrators) and at the level of individual aggregate managers issuing resources. Orchestrators enforce federation-level policies, while aggregate managers, under the control of their respective owners, enforce individual aggregate-level policies. Federation- or aggregate-level policies use project membership information, alongside other available identity attributes and resource attributes to make their authorization decisions. Policies can additionally use constraints like time-of-day and requested, available and used resource type and unit levels as part of the access decision process.

User rights are managed via FABRIC system services and are implemented using procedural code. Resource allocations are managed through FABRIC Control Framework and are defined using policies expressed in ALFA/XACML and enforced using XCAML PDPs (Policy Decision Points). In this document we attempt to specify both types of policies using ALFA for consistency.

Throughout this document we refer to a `slice` as a collection of resources allocated to an experiment in FABRIC. `Slivers` are individual programmable and/or configurable resources constituting a slice. A sliver can be a Virtual Machine, a network service or some other resource.

# RBAC Roles and role predicates

The following logical predicates reflect role assignments in FABRIC (with a view to supporting multiple FABRIC-like facilities):

| Role predicate | Description  |
|---|---|
| projectLead(principal, facility)  |  A project lead can create new projects specific to a given facility. Project Lead may add or remove Project Owners to their project (project they created). Project Lead becomes project owner by default. |
| facilityOperator(principal, facility) | A facility operator can create and delete any project and manage owners and members of any project. Facility operator can create slices in any project subject to project resource constraints. |
| projectOwner(principal, project) | A project Owner may add or remove project members for the projects they own. Project Owners are also project members. |
| projectMember(principal, project) | A project Member may create slices assigned to their corresponding project(s). Slice creation requires a membership in a valid project. A project member can provision resources/add slivers into a valid slice subject to resource federation- or aggregate-level resource constraints. A slice may contain slivers created by different project members. A sliver can only be modified or deleted by the project member who created it or by a project owner with one exception: slivers belonging to different project members are automatically allowed to be stitched together as necessary (i.e. if adding a sliver from Alice to a slice requires modifying another sliver already created by Bob, permission is automatically granted assuming Alice and Bob are members of the same project). |
| tokenHolder(principal, project) | A token holder may create long-lived API tokens |

Projects are bound to specific facilities at the time of creation, thus effectively adding a `facility` parameter to projectOwner and projectMember predicates.

|  Rule  | Implemented in  |
|---|---|
| 1. Project Lead can create projects at a facility  |  CoreAPI |
| 2. Project Lead can delete the project they created at a facility | CoreAPI |
| 3. Facility Operator can remove any project at a facility | CoreAPI |
| 4. Project Lead can add and remove Project Owners from projects they created at a facility | CoreAPI |
| 5. Facility Operator can add and remove Project Owners from any project at a facility | CoreAPI |
| 6. Project Lead includes privileges of a Project Owner | CoreAPI |
| 7. Project Owner can add and remove Project Members from their project at a facility | CoreAPI |
| 8. Facility Operator includes privileges of a Project Owner on a project (can add remove members) | CoreAPI |
| 9. Project Owner includes privileges as Project Member | CoreAPI |
| 10. Project Member can create slices within a project at a facility | XACML PDPs |
| 11. Project Member can delete a slice they created or any slice in their project | XACML PDPs |
| 12. Project Member can create slivers within any project slice subject to federation- or aggregate-level resource constraints at a facility | XACML PDPs |
| 13. Project Owner can modify or delete any sliver belonging to a slice created within their project. Modify operations are subject to federation- and aggregate-level resource constraints. | XACML PDPs |
| 14. Facility Operator is also a Project Member for any project (can create/delete slices and slivers) subject to project resource constraints. | CoreAPI |
| 15. Resource type/project tag based policies | XACML PDPs |

Rules 1-9 of the project management policies above are embedded in the [CoreAPI](https://github.com/fabric-testbed/fabric-core-api) procedural code and CI Logon logic. The remaining rules are federation-level and are implemented using XACML PDPs.

Generation of API tokens for control framework is handled by [Credential Manager](https://github.com/fabric-testbed/CredentialManager).

# Resource provisioning authorizations using ABAC

For the purposes of this document a FABRIC deployment consists of multiple sites presenting different remote API services focused on provisioning of resources and measurements. Different sites (aggregates) may use different policies with respect to user permissions (provider autonomy). In addition to resources in multiple sites and measurements, permissions must also be managed on various actions within the FABRIC portal. The goal of this document is to define a set of  policies so they can be implemented in XACML and other mechanisms.

Much of the resource authorization is done inside Orchestrator, Broker and Aggregate Managers and is based on the types of resources and components included in the slices and the `tags` associated with the project under which the slice with these slivers is being created. Other attributes of consideration can be the
dimensions/sizes of the slivers and the duration for which slivers are being created. Operations related to modifying existing resources require information about the identity of the user invoking the modify operation as well as the user who originally created the resource that is being modified.

Tags are added to a project by Facility Operators based on requests from the Project Owners. The full discussion of how project attributes are communicated to the PDP is outside the scope of this document, however briefly:
- One or more attributes or tags are added to a project within a CoreAPI by Facility Operator
- Prior to requesting to create a slice, experimenter receives a cryptographically signed authorization token that contains relevant project tags
- The PDP received information about requested resource attributes (their type, size, components, duration) as well as the project tags extracted from a validated token.
- In addition the control framework agent invoking the PDP provides identity attributes (e.g. email) of the principal invoking the action and the principal who e.g. created the resource
- The PDP policy renders a decision based on the combination of identity, project and resource attributes (and possibly local time)

There are different types of sliver resource constraints that are expressed via policies. Sliver constraints are by resource type, size and count (i.e. ‘Alice cannot hold more than 3 large apples, 2 small apples and 5 pears at a time’). 
- Constraints can be applied at different scopes (i.e. federation-level and aggregate-level).
- Constraints can be imposed on individual principals (based on their specific identity, their home institution, or their group within an institution, as asserted by the institutional IdP, i.e. student, faculty or staff).
- Constraints can be imposed on individual projects (a more common scenario) based on project tags.

Additional constraints for resource provisioning policies can come from
- Calendar time or date (i.e. for a specific aggregate ‘during exam week only make resources available only to users from home institution’)
- Available resource thresholds (i.e. ‘if fewer than 5 large apples are left available, only home institution users can have them’)

It is important to note that the authorization of dynamic management of PDP policies themselves, including resource constraints in them, (although possible) is not considered API driven for the purposes of this discussion and thus isn't covered by the described policies.

## Attributes

Note that in XACML all attributes are communicated as bags/collections.

### Available Subject Attributes/Claims

Using CI Logon many of the EduCause attributes should be available.

| Attribute | Values or Type | Claimed by | Notes |
| --- | --- | --- | --- |
| idp-name | String | Institutional IdP | Can be used as stand-in for home institution. |
| full-name | String | Institutional IdP | Also given_name and family_name are available in many cases |
| affiliation | String employee@university.edu; staff@university.edu; member@university.edu | Institutional IdP | Can be used for basic group membership decisions on resource limits  (faculty > staff > student). Part of R&S attribute set.  Institution can be inferred from @xyz.edu in addition to using idp_name above. |
| subject-id | String, typically institutional email | Institutional IdP | eduPersonPrincipalName or eppn|
| email | String | Institutional IdP | |
| cert_subject_dn | String /DC=org/DC=cilogon/C=US/O=University of Blah/CN=FirstName LastName T1234567 | CI Logon | Can be useful if we also use CI Logon-issued certs. |
| fabric-role | Project Lead, Project Owner, Project Member | FABRIC/CI Logon | fabric role can be a predicate of arity 1 or 2: projectLead(Alice), but projectOwner(Alice, Project-X).  |
| fabric-project | String | FABRIC/CI Logon |  Needs to relate to fabric role above |

### Project Attributes/Tags

| Attribute | Values or Type | Notes |
| --- | --- | --- |
| project-tag | String |

The following is an incomplete list of possible project tag values:
- VM.NoLimitCPU - allows to create VMs with more than 2 CPU cores
- VM.NoLimitRAM - allows to create VMs with more than 10 GB of RAM
- VM.NoLimitDisk - allows to create VMs with more than 10 GB of disk
- VM.NoLimit - VM.NoLimitCPU | VM.NoLimitRAM | VM.NoLimitDisk
- Component.GPU - allows to provision and attach GPU components
- Component.FPGA - allows to provision and attach FPGA components
- Component.SmartNIC - allows to provision and attach 25G and 100G dedicated SmartNIC components
- Component.Storage - allows to create and attach rotating storage
- Component.NVME - allows to provision and attach NVME components
- Net.NoLimitBW - allows to provision links over 10 Gbps
- Net.FABNetv4Ext - allows to create slices with public connectivity over IPv4
- Net.FABNetv6Ext - allows to create slices with public connectivity over IPv6
- Net.PortMirroring - allows to create slices that include port mirroring
- Net.FacilityPort.XXX - allows to create slices with stitch port with short name XXX
- Net.AllFacilityPorts - allows to create slices with any stitchport
- Slice.Multisite - allows to create slices spanning multiple sites
- Slice.Measurements - allows to provision measurement VMs
- Slice.NoLimitLifetime - allows to create slices with a lifetime beyond default limit X time units without the need to renew
- Project.Educational - tags the project as educational restricting it to a subset of resources


### Actions, Scopes and Action Attributes

| Action | Scope | Additional attributes |
| --- | --- | --- |
| createProject | project  |   |
| deleteProject | project  |   |
| addOwner      | project  |   |
| removeOwner   | project  |   |
| addMember     | project  |   |
| removeMember  | project  |   |
| create, delete, modify, query, status, redeem, POA, renew, demand, update, close, claim, reclaim, ticket, extend, relinquish  | slice, sliver  |   |

### Common FABRIC Request Structure

FABRIC policies require many different attributes to make decisions. This document provides up-to-date list of attributes required across all policies (Orchestrator, AM or others).

Some of the attributes are standard XACML attributes, some are specific to FABRIC. A JSON [template](policies/alfa/Requests/orchestrator-request-template.json) of a request with all attributes present is available.

#### Resource Attributes

Category ID: urn:oasis:names:tc:xacml:3.0:attribute-category:resource

| Attribute ID | Attribute Values | Attribute Description | 
| --- | --- | --- |
| urn:fabric:xacml:attributes:resource-type | "slice", "sliver", "project" | |
| urn:fabric:xacml:attributes:resource-vmcpus | Integer | Number of CPU cores in VM |
| urn:fabric:xacml:attributes:resource-vmram | Integer | Gygabytes of RAM in VM |
| urn:fabric:xacml:attributes:resource-vmdisk | Integer | Gygabytes of Disk in VM |
| urn:fabric:xacml:attribute:resource-component | "FPGA", "SmartNIC", "SharedNIC", "GPU" | |
| urn:fabric:xacml:attribute:resource-site | String | Site acronym |
| urn:fabric:xacml:attribute:resource-stitch-port | String | Name of stitch port |
| urn:fabric:xacml:attribute:resource-peersite | String | Name of peer site |
| urn:fabric:xacml:attribute:resource-link-bw | Integer | Bandwidth in Gbps |
| urn:fabric:xacml:attribute:resource-with-measurements | Boolean | Whether measurement resources are being requested |
| urn:fabric:xacml:attributes:resource-subject | String | User unique identifer like EPPN |
| urn:fabric:xacml:attributes:resource-project | String | Project unique identifier like GUID |

#### Action Attributes

Category ID: urn:oasis:names:tc:xacml:3.0:attribute-category:action

| Attribute ID | Attribute Values | Attribute Description | 
| --- | --- | --- |
| urn:oasis:names:tc:xacml:1.0:action:action-id | create, delete, modify, query, status, redeem, POA, renew, demand, update, close, claim, reclaim, ticket, extend, relinquish | Action on a sliver or slice by AM, Orchestrator or Broker |
| urn:fabric:xacml:attributes:resource-lifetime | TimeDuration | Sliver or slice lifetime request |

#### Access Subject Attributes

Category ID: urn:oasis:names:tc:xacml:1.0:subject-category:access-subject

| Attribute ID | Attribute Values | Attribute Description | 
| --- | --- | --- |
| urn:oasis:names:tc:xacml:1.0:subject:subject-id | String | User unique identifier like EPPN, must be same type as resource-subject |
| urn:fabric:xacml:attributes:subject-project | String | Project unique identifier like GUID |
| urn:fabric:xacml:attributes:project-tag | String | Permission tags associated with the project (see [README.md](../../../README.md))

#### Environment Attributes 

Category ID: urn:oasis:names:tc:xacml:3.0:attribute-category:environment

| Attribute ID | Attribute Values | Attribute Description | 
| --- | --- | --- |

# Available Policy Implementations/Defining new policies

FABRIC policies and associated example requests are defined in the [policies](policies) subdirectory.

Policies used in production (on Orchestrator, AMs and Broker) are specified in ALFA and utilize [VS Code ALFA extension](https://marketplace.visualstudio.com/items?itemName=Axiomatics.alfa) to compile ALFA to XACML. This is the recommended way for creating
and updating FABRIC PDP policies. You must install [VS Code](https://code.visualstudio.com/) and then add the extension to it from Marketplace. 

- [ALFA Policies](policies/alfa)

Within this folder compiled policies can be found in [src-gen](src-gen) folder (the plugin automatically deposits them there). Common attribute
definitions are located in [fabric-attributes.alfa](alfa/fabric-attributes.alfa).

There are some test and deprecated policies preserved for historical reasons.

Deprecated policies:
- Example per actor policies are located in [by-actor](by-actor) folder
- Example project level policies and example requests in [project/](project) (Note: these are not used and implemented as procedural code in ProjectRegistry instead)
- Example sliver level policies and example requests in [sliver/](sliver) (Note: provided as examples only)

Note that each folder typically contains policies as well as example requests both in XML and in JSON.

# Testing with Authzforce server

Note1: As of Java 9, jaxb libraries have been removed from standard JDK distributions and thus will not work according to instructions here (which only apply to Java8) - appropriate jars must be added to classpath externally. When in doubt use the pre-packaged [PDP Docker Images](https://github.com/fabric-testbed/fabric-docker-images/tree/master/authzforce-pdp) which include command tools in addition to the RESTful PDP server.

Note2: OpenJDK 11 and up does not have the problem described in Note1. Newer version of AuthzForce (17+) work with OpenJDK11

## Testing manually

1. Download the latest [authzforce-ce-core-pdp-cli-X.Y.Z](https://github.com/authzforce/core) and follow instructions
1. Download the latest [configuration and example policy folder](https://github.com/authzforce/core/tree/develop/pdp-cli/src/test/resources/conformance/xacml-3.0-core/mandatory)
1. Modify pdp.xml to (a) point to the policy XML file you are testing and (b) make sure `rootPolicyRef` element URN matches that of the `PolicySetId` at the top of your policy
1. Execute as follows and observe the result:
```
$ ./authzforce-ce-core-pdp-cli-X.Y.Z.jar -p pdp.xml <request path>/requestfile.xml
```
1. To try JSON instead of XML the following command should produce the result:
```
$ ./authzforce-ce-core-pdp-cli-X.Y.Z.jar -p -t XACML_JSON pdp.xml <request path>/requestfile.json
```

If you have a PDP RESTful server running in a [Docker container](https://github.com/fabric-testbed/fabric-docker-images/tree/master/authzforce-pdp) you can issue curl requests as follows to test:
1. XML requests and responses:
```
$ curl --include --header "Content-Type: application/xacml+xml" --data @policies/orchestrator-request.xml http://localhost:8080/services/pdp | tidy -xml -i -
```
1. JSON requests and responses:
```
curl --include --header "Content-Type: application/xacml+json" --data @policies/orchestrator-request.json http://localhost:8080/services/pdp
```
(The above example assumes the use of [orchestrator-yes.xml policy](by-actor/SimpleYes/orchestrator-yes.xml), the same directory contains example requests both in XML and JSON).

## Using a test harness

Make sure that `./authzforce-ce-core-pdp-cli-X.Y.Z.jar ` is present under `authzforce/` directory. Update `test/test-harness.py` appropriately, be sure to use a virtenv that has the latest (or appropriate) version of fabric-fim library, then run:
```
$ cd test/
$ pytest test-harness.py
```
This will run all available requests for available policies.

# Useful references

- [XACML 3.0 spec](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html)
- [VS Code ALFA Plugin](https://marketplace.visualstudio.com/items?itemName=Axiomatics.alfa)
- [ALFA documentation](https://axiomatics.github.io/alfa-vscode-doc/)
- [StackOverflow example](https://stackoverflow.com/questions/41473752/complex-authorization-using-xacml)
- [XACML3 spec](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html#_Toc325047132)
- [FIWARE Tutorial](https://github.com/FIWARE/tutorials.XACML-Access-Rules)
- [Another FIWARE Tutorial](https://fiware-tutorials.readthedocs.io/en/latest/cmds/administrating-xacml/index.html#13-request)
- [WSO Tutorial](https://docs.wso2.com/display/IS560/Fine-grained+Authorization+using+XACML+Requests+in+JSON+Format)
- [Authzforce implementation](https://github.com/authzforce/core)
- [Balana implementation](https://github.com/wso2/balana)
