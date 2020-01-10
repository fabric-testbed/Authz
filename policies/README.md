## OVERVIEW

This document defines FABRIC authorization policies in semi-formal fashion to help with implementing and evaluating different approaches.

FABRIC will rely on a federated identity model and ABAC (Attribute-Based Access Control). Each identity comes with a mix of attributes, some asserted by the institutional IdP (Identity Provider) and some via a FABRIC-specific mechanism (e.g. CoManage). These attributes can be provided to the authorization system in a secure way in order to allow it to make access decisions to various protected APIs.

FABRIC deployment consists of multiple sites presenting different services focused on provisioning of resources and measurements. Different sites (aggregates) may use different policies with respect to user permissions (provider autonomy). In addition to resources in multiple sites and measurements, permissions must also be managed on various actions within the FABRIC portal. The goal of this document is to define a set of initial policies so they can be implemented in XACML and other mechanisms and properly evaluated.

The document follows the approach defined here in defining the specification.

## INFORMAL SPECIFICATION

Privileges in FABRIC are granted based on grouping. Each group, referred to as a project has a specific set of rights limiting their use of resources on a specific subset of aggregates. Resource provisioning is limited at two levels - that of a control framework broker (could be multiple brokers; brokers are optional in small deployments) and at the level of individual aggregate managers issuing resources. Brokers enforce federation-level policies, while aggregate managers, under the control of their respective owners, enforce individual aggregate-level policies. Federation- or aggregate-level policies use project membership information, alongside other available identity attributes to make their authorization decisions. Policies can additionally use constraints like time-of-day and requested, available and used resource type and unit levels as part of the access decision process.

A control framework controller/orchestrator interacting with brokers and aggregate managers acts as part of a user tool-chain and acts on behalf (speaks-as) the user inheriting her permissions.

Measurements are treated as resources, provisioned via the measurement framework.

Additionally rights are granted to certain users enabling them to create projects and manage project memberships.

A Project Lead can create new projects. Project Lead may add or remove Project Owners to their project. Project Lead becomes project owner by default.

A Project Owner may add or remove project members. Project Owners are also project members.

A Project Member may create slices assigned to the corresponding project. Slice creation requires a membership in a valid project. A project member can provision resources/add slivers into a valid slice subject to resource limits. A slice may contain slivers created by different project members. A sliver can only be modified or deleted by the project member who created it or by a project owner with one exception: slivers belonging to different project members are automatically allowed to be stitched together as necessary (i.e. if adding a sliver from Alice to a slice requires modifying another sliver already created by Bob, permission is automatically granted assuming Alice and Bob are members of the same project).

There are different types of resource limits. All resource limits are by sliver type, size and count (i.e. ‘Alice cannot hold more than 3 large apples, 2 small apples and 5 pears at a time’). Limits can be applied at different scopes (i.e. federation-level and aggregate-level). Limits can be imposed on
Individual principals (based on their specific identity, their home institution, or their group within an institution, as asserted by the institutional IdP, i.e. student, faculty or staff).
Individual projects

Additional constraints for resource provisioning policies can come from
Calendar time or date (i.e. for a specific aggregate ‘during exam week only make resources available only to users from home institution’)
Available resource thresholds (i.e. ‘if fewer than 5 apples are left available, only home institution users can have them’)

## SEMI-FORMAL SPECIFICATION

1. Project Lead can create projects
1. Project Lead can delete the project they created
1. Project Lead can add and remove Project Owners from projects they created
1. Project Lead is also a Project Owner
1. Project Owner can add and remove Project Members from their project
1. Project Owner is also a Project Member
1. Project Member can create slices within a project
1. Project Member can create slivers within any project slice subject to federation- or aggregate-level resource limits
1. Project Member can modify or delete any sliver created by them in any project slice. Modify operations are subject to federation- and aggregate-level resource limits.
1. Project Owner can modify or delete any sliver belonging to a slice created within their project. Modify operations are subject to federation- and aggregate-level resource limits.
1. Project Member can delete a slice they created, as long as no slivers created by other members exist in the slice
1. Facility Operator can remove any project
1. Facility Operator can add and remove Project Owners from any project
1. Facility Operator is also a Project Owner for any project (can add remove members)
1. Facility Operator is also a Project Member for any project (can create/delete slices and slivers)

## ATTRIBUTES

### Available Subject Attributes/Claims

Using CI Logon many of the EduCause attributes should be available, see here.

| Attribute | Values or Type | Claimed by | Notes |
| --- | --- | --- | --- |
| idp_name | String | Institutional IdP | Can be used as stand-in for home institution. |
| name | String | Institutional IdP | Also given_name and family_name are available in many cases |
| affiliation | String employee@unc.edu; staff@unc.edu; member@unc.edu | Institutional IdP | Can be used for basic group membership decisions on resource limits  (faculty > staff > student)  Institution can be inferred from @xyz.edu in addition to using idp_name above. |
| eppn | String, typically institutional email | Institutional IdP | eduPersonPrincipalName |
| email | String | Institutional IdP | |
| cert_subject_dn | String /DC=org/DC=cilogon/C=US/O=University of North Carolina at Chapel Hill/CN=Ilya Baldin T2758558 | CI Logon | Can be useful if we also use CI Logon-issued certs. |
| fabric_role | Project Lead, Project Owner, Project Member | FABRIC/CI Logon |   |
| fabric_project | String | FABRIC/CI Logon |   |

### Resource Attributes

| Attribute | Values or Type | Notes |
| --- | --- | --- |
| auth_resource_type | project, slice, sliver | Top level resource type for authorization |
| sliver_category |     | Applies only to slivers |
| sliver_size     | Integer | Applies only to slivers |
| sliver_count    | Integer | Applies only to slivers |


### Actions and Action Attributes

| Action | Additional action attributes | Notes |
| --- | --- | --- |
| createProject |   |   |
| deleteProject |   |   |
| addOwner      |   |   |
| removeOwner   |   |   |
| addMember     |   |   |
| removeMember  |   |   |

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

policyset sliver {
}
```

## Useful references

- [StackOverflow example](https://stackoverflow.com/questions/41473752/complex-authorization-using-xacml)
- [XACML3 spec](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html#_Toc325047132)
- [FIWARE Tutorial](https://github.com/FIWARE/tutorials.XACML-Access-Rules)
- [Another FIWARE Tutorial](https://fiware-tutorials.readthedocs.io/en/latest/cmds/administrating-xacml/index.html#13-request)
- [WSO Tutorial](https://docs.wso2.com/display/IS560/Fine-grained+Authorization+using+XACML+Requests+in+JSON+Format)
- [Authzforce implementation](https://github.com/authzforce/core)
- [Balana implementation](https://github.com/wso2/balana)
