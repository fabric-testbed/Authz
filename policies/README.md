## Overview

This document defines FABRIC authorization policies to help with implementing production policies using a combination of CILogon and XACML3.0.

FABRIC will rely on a federated identity model and ABAC (Attribute-Based Access Control). Each identity comes with a mix of attributes, some asserted by the institutional IdP (Identity Provider) and some via a FABRIC-specific mechanism (e.g. CoManage). These attributes can be provided to the authorization system in a secure way in order to allow it to make access decisions to various protected APIs. Policies will be specified in XACML and each RESTful API endpoint will be protected by an XACML-capable PDP (Policy Decision Point)

For the purposes of this document a FABRIC deployment consists of multiple sites presenting different RESTful services focused on provisioning of resources and measurements. Different sites (aggregates) may use different policies with respect to user permissions (provider autonomy). In addition to resources in multiple sites and measurements, permissions must also be managed on various actions within the FABRIC portal. The goal of this document is to define a set of initial policies so they can be implemented in XACML and other mechanisms and properly evaluated.

The document follows the approach defined [here](https://stackoverflow.com/questions/41473752/complex-authorization-using-xacml) in defining the specification.

## Informal Specification

Privileges in FABRIC are granted based on grouping. Each group, referred to as a project has a specific set of rights limiting their use of resources on a specific subset of aggregates. Resource provisioning is limited at two levels - that of a control framework broker (could be multiple brokers; brokers are optional in small deployments) and at the level of individual aggregate managers issuing resources. Brokers enforce federation-level policies, while aggregate managers, under the control of their respective owners, enforce individual aggregate-level policies. Federation- or aggregate-level policies use project membership information, alongside other available identity attributes to make their authorization decisions. Policies can additionally use constraints like time-of-day and requested, available and used resource type and unit levels as part of the access decision process.

A control framework controller/orchestrator interacting with brokers and aggregate managers acts as part of a user tool-chain and acts on behalf (speaks-as) the user inheriting her permissions. Measurements are treated as resources, provisioned via the measurement framework. Additionally rights are granted to certain users enabling them to create projects and manage project memberships.

The following logical predicates reflect role assignments in FABRIC (with a view to supporting multiple FABRIC-like facilities):

| Role predicate | Description  |
|---|---|
| projectLead(principal, facility)  |  A project lead can create new projects specific to a given facility. Project Lead may add or remove Project Owners to their project (project they created). Project Lead becomes project owner by default. |
| facilityOperator(principal, facility) | A facility operator can create and delete any project and manage owners and members of any project. Facility operator can create slivers in any project subject to project resource constraints. |
| projectOwner(principal, project) | A project Owner may add or remove project members for the projects they own. Project Owners are also project members. |
| projectMember(principal, project) | A project Member may create slices assigned to their corresponding project(s). Slice creation requires a membership in a valid project. A project member can provision resources/add slivers into a valid slice subject to resource federation- or aggregate-level resource constraints. A slice may contain slivers created by different project members. A sliver can only be modified or deleted by the project member who created it or by a project owner with one exception: slivers belonging to different project members are automatically allowed to be stitched together as necessary (i.e. if adding a sliver from Alice to a slice requires modifying another sliver already created by Bob, permission is automatically granted assuming Alice and Bob are members of the same project). |

Projects are bound to specific facilities at the time of creation.

There are different types of resource constraints. All resource constraints are by sliver type, size and count (i.e. ‘Alice cannot hold more than 3 large apples, 2 small apples and 5 pears at a time’). Constraints can be applied at different scopes (i.e. federation-level and aggregate-level).
- Constraints can be imposed on individual principals (based on their specific identity, their home institution, or their group within an institution, as asserted by the institutional IdP, i.e. student, faculty or staff).
- Constraints can be imposed on individual projects (a more common scenario) based on project name

Additional constraints for resource provisioning policies can come from
- Calendar time or date (i.e. for a specific aggregate ‘during exam week only make resources available only to users from home institution’)
- Available resource thresholds (i.e. ‘if fewer than 5 large apples are left available, only home institution users can have them’)

It is important to note that the authorization of dynamic management of PDP policies themselves, including resource constraints in them, (although possible) is not considered API driven for the purposes of this discussion and thus isn't covered by the described policies.

## Semi-Formal Specification


|  Rule  | Implemented in  |
|---|---|
| 1. Project Lead can create projects at a facility  |  ProjectRegistry |
| 2. Project Lead can delete the project they created at a facility | ProjectRegistry |
| 3. Facility Operator can remove any project at a facility | ProjectRegistry |
| 4. Project Lead can add and remove Project Owners from projects they created at a facility | ProjectRegistry |
| 5. Facility Operator can add and remove Project Owners from any project at a facility | ProjectRegistry |
| 6. Project Lead is also a Project Owner | ProjectRegistry |
| 7. Project Owner can add and remove Project Members from their project at a facility | ProjectRegistry |
| 8. Facility Operator is also a Project Owner for any project (can add remove members) | ProjectRegistry |
| 9. Project Owner is also a Project Member | ProjectRegistry |
| 10. Project Member can create slices within a project at a facility | XACML PDPs |
| 11. Project Member can delete a slice they created, as long as no slivers created by other members exist in the slice at a facility | XACML PDPs |
| 12. Project Member can create slivers within any project slice subject to federation- or aggregate-level resource constraints at a facility | XACML PDPs |
| 13. Project Member can modify or delete any sliver created by them in any project slice. Modify operations are subject to federation- and aggregate-level resource constraints. | XACML PDPs |
| 14. Project Owner can modify or delete any sliver belonging to a slice created within their project. Modify operations are subject to federation- and aggregate-level resource constraints. | XACML PDPs |
| 15. Facility Operator is also a Project Member for any project (can create/delete slices and slivers) subject to project resource constraints. | XACML PDPs |

Some project management policies above are embedded in the [ProjectRegistry](https://github.com/fabric-testbed/project-registry) and CI Logon logic and are only included in this list for completeness. On the other hand policies related to resource provisioning are described using XACML 3.0 and embedded with PDPs attached to individual actors - Orchestrator, Broker and Aggregate Managers. Examples of their implementations can be found below.

## Attributes

### Available Subject Attributes/Claims

Using CI Logon many of the EduCause attributes should be available, see here.

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

### Resource Attributes

| Attribute | Values or Type | Notes |
| --- | --- | --- |
| resource-type | project, slice, sliver | Top level resource type for authorization |
| resource-creator | String |  |
| sliver-type |     | Applies only to slivers |
| sliver-size     | Integer | Applies only to slivers |
| sliver-count    | Integer | Applies only to slivers |


### Actions and Action Attributes

| Action | Subject resource type | Additional attributes |
| --- | --- | --- |
| createProject | project  |   |
| deleteProject | project  |   |
| addOwner      | project  |   |
| removeOwner   | project  |   |
| addMember     | project  |   |
| removeMember  | project  |   |
| create   | slice, sliver  |   |
| delete   | slice, sliver  |   |
| modify   | slice, sliver  |   |

## Formal Specification

Uses ALFA-like syntax (but we are not using ALFA, as it appears defunct at this point - actual policies will be written in XACML3.0)

```
/* project policy set */
policyset project {
    target clause objectType == “project”
    apply firstApplicable

    policy createProject {
        target clause actionId == “createProject”
        apply denyUnlessPermit
        rule leadOrOperator {
            permit
            condition (user.fabric_role == “projectLead” or user.fabric_role == “facilityOperator”)
        }
    }

    policy deleteProject {
        apply denyUnlessPermit
        target clause actionId == “deleteProject”
        rule lead {
            permit
            condition user.fabric_role == “projectLead” and project.creator == user.eppn
        }
        rule operator {
            permit
            condition user.fabric_role == “facilityOperator”
        }
    }

    /* manage project owners */
    policy manageProjectOwner {
        target clause actionId anyOf “addOwner”, “removeOwner”
        apply denyUnlessPermit
        rule addOwner {
            permit
            condition project.creator == user.eppn and
            user.fabric_role == “projectLead”
        }
        rule addOwnerAsOperator {
            permit
            condition user.fabric_role == “facilityOperator”
        }
    }

    /* manage project members */
    policy manageProjectMember {
        target clause actionId anyOf “addMember”, “removeMember”
        apply denyUnlessPermit
        rule addMemberAsOwner {
            permit
            /* perhaps there is a better way to deal with predicates of arity 2;
            the implied predicate here is projectOwner(principal, project) */
            condition concat(“projectOwner:”, project.name) == user.fabric_role or (user.fabric_role == “projectLead” and user.eppn == project.creator)
        }
        rule addMemberAsOperator {
            permit
            condition user.fabric_role == “facilityOperator”
        }
    }

    /* alternatively (if we don't want to mess with concat
    and arity 2 predicates); requires adding resource.owner property */
    policy manageProjectMember {
        target clause actionId anyOf “addMember”, “removeMember”
        apply denyUnlessPermit
        rule addMemberAsOwner {
            permit
            condition (user.fabric_role == projectOwner and project.owner == user.eppn) or (user.fabric_role == “projectLead” and user.eppn == project.creator)
        }
        rule addMemberAsOperator {
            permit
            condition user.fabric_role == “facilityOperator”
        }
    }
  }

/* slice policy set */
policyset slice {
    target clause objectType == “slice”
    apply firstApplicable

    policy createSlice {
        target clause actionId == “create”
        apply firstApplicable
        rule
    }
}

/* this is an example that sets some limits on resources and uses calendar */
policyset sliver {
  target clause objectType == "sliver"
  apply firstApplicable

  policy createSliver {
      target clause actionId "create"
      apply denyUnlessPermit
      rule createSliver {
        /* can create within any project slice */
        target clause profile "simple"
        permit
        (condition user.fabric_role == concat("projectMember:", slice.project_name) or
          user.fabric_role == concat("projectOwner:", slice.project_name))

      }
      rule createSliverWithCalendarLimits {
        target clause profile "calendarLimit"
        /* can create within any project slice, home institution 9-5  */
        permit
        condition (user.fabric_role == concat("projectMember:", slice.project_name) or
          user.fabric_role == concat("projectOwner:", slice.project_name)) and
          (user.institution == "UNC" and current_time before 9am or after 5pm )
      }
      rule createSliverWithResourceLimits {
        target clause profile "resourceLimit"
        permit
        condition (user.fabric_role == concat("projectMember:",slice.project_name) or
          user.fabric_role == concat("projectOwner:", slice.project_name)) and
          (project.bandwidth + sliver.bandwidth < project.bandwidth_limit)
      }
  }

  policy modifySliver {
    target clause actionId "modify"
    apply denyUnlessPermit
    rule modifySliver {
      permit
      condition
    }
    rule modifySliverWithLimits {
      permit
      condition
    }
  }

  policy deleteSliver {
    target clause actionId "delete"
    apply denyUnlessPermit
    rule deleteSliver {
        permit
        condition
    }
  }
}
```

## Available Policy Implementations

Policies and associated example requests are defined in the following subdirectories:
- Per actor policies used in *actual deployments* are located in [by-actor](by-actor) folder
- Example project level policies and example requests in [project/](project) (Note: these are not used and implemented as precedural code in ProjectRegistry instead)
- Example sliver level policies and example requests in [sliver/](sliver) (Note: provided as examples only)

Note that each folder typically contains policies as well as example requests both in XML and in JSON.

## Testing with Authzforce server

Note that as of Java 9, jaxb libraries have been removed from standard JDK distributions and thus will not work according to instrucitons above (which only apply to Java8) - appropriate jars must be added to classpath externally. When in doubt use the pre-packaged [PDP Docker Images](https://github.com/fabric-testbed/fabric-docker-images) which include command tools in addition to the PDP server.

1. Download the latest [authzforce-ce-core-pdp-cli-X.Y.Z](https://github.com/authzforce/core) and follow instructions
1. Download the latest [configuration and example policy folder](https://github.com/authzforce/core/tree/develop/pdp-cli/src/test/resources/conformance/xacml-3.0-core/mandatory)
1. Modify pdp.xml to (a) point to the policy XML file you are testing and (b) make sure `rootPolicyRef` element URN matches that of the `PolicySetId` at the top of your policy
1. Execute as follows and observe the result:
```
$ ./authzforce-ce-core-pdp-cli-14.0.1.jar -p pdp.xml <request path>/requestfile.xml
```
1. To try JSON instead of XML the following command should produce the result:
```
$ ./authzforce-ce-core-pdp-cli-14.0.0.jar -p -t XACML_JSON pdp.xml <request path>/requestfile.json
```

If you have a PDP RESTful server running in a [Docker container](https://github.com/fabric-testbed/fabric-docker-images) you can issue curl requests as follows to test:
1. XML requests and responses:
```
$ curl --include --header "Content-Type: application/xacml+xml" --data @policies/orchestrator-request.xml http://localhost:8080/services/pdp | tidy -xml -i -
```
1. JSON requests and responses:
```
curl --include --header "Content-Type: application/xacml+json" --data @policies/orchestrator-request.json http://localhost:8080/services/pdp
```
(The above example assumes the use of [orchestrator-yes.xml policy](by-actor/SimpleYes/orchestrator-yes.xml), the same directory contains example requests both in XML and JSON).

## Useful references

- [XACML 3.0 spec](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html)
- [StackOverflow example](https://stackoverflow.com/questions/41473752/complex-authorization-using-xacml)
- [XACML3 spec](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html#_Toc325047132)
- [FIWARE Tutorial](https://github.com/FIWARE/tutorials.XACML-Access-Rules)
- [Another FIWARE Tutorial](https://fiware-tutorials.readthedocs.io/en/latest/cmds/administrating-xacml/index.html#13-request)
- [WSO Tutorial](https://docs.wso2.com/display/IS560/Fine-grained+Authorization+using+XACML+Requests+in+JSON+Format)
- [Authzforce implementation](https://github.com/authzforce/core)
- [Balana implementation](https://github.com/wso2/balana)
