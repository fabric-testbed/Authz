import os
import unittest
import subprocess
import json

TAGPOLICY = 'src-gen/fabricTags.OrchestratorTags.xml'
TAGPOLICYID = 'urn:fabric:authz:xacml:orchestrator:tags'
# make sure the CLI executable and appropriate Java version are available
AUTHZFORCECLI = '../authzforce/authzforce-ce-core-pdp-cli-17.1.2.jar'
PERMIT_REQUESTS = [ 
    '../policies/alfa/FabricOrchestratorProjectTags/orchestrator-request-simplest.json',
    '../policies/alfa/FabricOrchestratorProjectTags/orchestrator-request-simple.json',
    '../policies/alfa/FabricOrchestratorProjectTags/orchestrator-request-duration.json',
    '../policies/alfa/FabricOrchestratorProjectTags/orchestrator-request.json'
]

class PolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        pdp_file = """<?xml version="1.0" encoding="UTF-8"?>
<pdp
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xmlns="http://authzforce.github.io/core/xmlns/pdp/7"
	version="7.1">
	<policyProvider
		id="rootPolicyProvider"
		xsi:type="StaticPolicyProvider">
		<policyLocation>${PARENT_DIR}/../""" + TAGPOLICY + \
        """</policyLocation>
	</policyProvider>
	<rootPolicyRef>""" + TAGPOLICYID + \
    """</rootPolicyRef>
	<ioProcChain>
		<requestPreproc>urn:ow2:authzforce:feature:pdp:request-preproc:xacml-json:default-lax</requestPreproc>
		<resultPostproc>urn:ow2:authzforce:feature:pdp:result-postproc:xacml-json:default</resultPostproc>
	</ioProcChain>
</pdp>
        """
        print(f'Generating pdp.xml file')
        with open('pdp.xml', 'w') as f:
            f.write(pdp_file)


    def tearDown(self) -> None:
        #print('Deleting pdp.xml file')
        #os.unlink('pdp.xml')
        pass

    def testPermits(self) -> None:
        print('Running tests')

        for r in  PERMIT_REQUESTS:
            print(f'Trying request {r}')
            try:
                completed = subprocess.run([AUTHZFORCECLI, '-p', '-t', 'XACML_JSON', '../test/pdp.xml', r], 
                                            capture_output=True, check=True)
                print(f'Process output is \n{completed.stdout}')
                authz_decision = json.loads(completed.stdout)
                self.assertEqual(authz_decision['Response'][0]['Decision'], 'Permit', msg=f'Request {r} did not return Permit, '\
                    'instead {completed.stdout}')
            except subprocess.CalledProcessError as e:
                print(f'Request {r} returned an error {e.returncode}')
                print(f'{e.stderr}')
                self.assertFalse(True, msg=e.stderr)
