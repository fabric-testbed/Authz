# Overview
This folder contains various implementation of test and production policies. All production policies are located in the [alfa](alfa) folder. Other policies are provided as examples. 

# Specification

We use ALFA-like syntax to sketch the policies defined here. 

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
