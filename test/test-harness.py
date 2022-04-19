import os
import unittest
import subprocess
import json
import datetime

import tempfile

from fim.authz.attribute_collector import ResourceAuthZAttributes
from fim.slivers.network_node import NodeSliver

import fim.user as fu

TAGPOLICY = 'src-gen/fabricTags.OrchestratorTags.xml'
TAGPOLICYID = 'urn:fabric:authz:xacml:orchestrator:tags'
TAGPDP = 'pdp-tag.xml'
YESPOLICY = 'src-gen/fabricYes.AnyActorYesPolicy.xml'
YESPOLICYID = 'urn:fabric:authz:xacml:actor:ps'
YESPDP = 'pdp-yes.xml'
NOPOLICY = 'src-gen/fabricNo.AnyActorNoPolicy.xml'
NOPOLICYID = 'urn:fabric:authz:xacml:actor:no:ps'
NOPDP = 'pdp-no.xml'

# make sure the CLI executable and appropriate Java version are available
AUTHZFORCECLI = '../authzforce/authzforce-ce-core-pdp-cli-17.1.2.jar'
PERMIT_REQUESTS = [ 
    '../policies/alfa/Requests/orchestrator-request-simplest.json',
    '../policies/alfa/Requests/orchestrator-request-simple.json',
    '../policies/alfa/Requests/orchestrator-request-duration.json',
    '../policies/alfa/Requests/orchestrator-request-notags.json',
    '../policies/alfa/Requests/orchestrator-request.json'
]

def makePDPFile(policyFile, policyID, pdpFile):
    pdp_file = """<?xml version="1.0" encoding="UTF-8"?>
<pdp
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xmlns="http://authzforce.github.io/core/xmlns/pdp/7"
	version="7.1">
	<policyProvider
		id="rootPolicyProvider"
		xsi:type="StaticPolicyProvider">
		<policyLocation>${PARENT_DIR}/../""" + policyFile + \
        """</policyLocation>
	</policyProvider>
	<rootPolicyRef>""" + policyID + \
    """</rootPolicyRef>
	<ioProcChain>
		<requestPreproc>urn:ow2:authzforce:feature:pdp:request-preproc:xacml-json:default-lax</requestPreproc>
		<resultPostproc>urn:ow2:authzforce:feature:pdp:result-postproc:xacml-json:default</resultPostproc>
	</ioProcChain>
</pdp>
        """
    print(f'Generating {pdpFile} file')
    with open(pdpFile, 'w') as f:
        f.write(pdp_file)


class PolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        makePDPFile(TAGPOLICY, TAGPOLICYID, TAGPDP)
        makePDPFile(YESPOLICY, YESPOLICYID, YESPDP)
        makePDPFile(NOPOLICY, NOPOLICYID, NOPDP)

    def tearDown(self) -> None:
        print('Deleting pdp.xml file')
        os.unlink('pdp-tag.xml')
        os.unlink('pdp-yes.xml')
        os.unlink('pdp-no.xml')
        pass

    def runOnAllRequests(self, pdpFile, outcome='Permit', printResponse=False):
        print(f'Running tests on {pdpFile}')

        for r in  PERMIT_REQUESTS:
            print(f'Trying request {r}')
            try:
                completed = subprocess.run([AUTHZFORCECLI, '-p', '-t', 'XACML_JSON', '../test/' + pdpFile, r], 
                                            capture_output=True, check=True)
                print(f'Process output is \n{completed.stdout}')
                authz_decision = json.loads(completed.stdout)
                if printResponse:
                    print(f'Received response: {authz_decision["Response"]}')
                self.assertEqual(authz_decision['Response'][0]['Decision'], outcome, msg=f'Request {r} did not return Permit, '\
                    f'instead {completed.stdout}')
            except subprocess.CalledProcessError as e:
                print(f'Request {r} returned an error {e.returncode}')
                print(f'{e.stderr}')
                self.assertFalse(True, msg=e.stderr)

    def runOnStringRequest(self, request: str, pdpFile: str, response: str='Permit', printResponse=False):

        name=None
        try:
            tf = tempfile.NamedTemporaryFile(delete=False, encoding='utf-8', mode='w+')
            name=tf.name
            print(f'Created temporary file {tf.name}')
            tf.write(request)
            tf.close()
        except: 
            os.unlink(name)

        try:
            completed = subprocess.run([AUTHZFORCECLI, '-p', '-t', 'XACML_JSON', '../test/' + pdpFile, tf.name], 
                                            capture_output=True, check=True)
            print(f'Process output is \n{completed.stdout}')
            authz_decision = json.loads(completed.stdout)
            if printResponse:
                print(f'Received response: {authz_decision["Response"]}')
            self.assertEqual(authz_decision['Response'][0]['Decision'], response, msg=f'Request {tf.name} did not return Permit, '\
                                                                                      f'instead {completed.stdout}')
        except subprocess.CalledProcessError as e:
            print(f'Request {tf.name} returned an error {e.returncode}')
            print(f'{e.stderr}')
            self.assertFalse(True, msg=e.stderr)

        os.unlink(tf.name)

    def testTagPolicyPermits(self) -> None:
        print('Running static Permit tests on tag policy')
        self.runOnAllRequests(TAGPDP)

    def testYesPolicy(self) -> None:
        print('Running static Permit tests on yes policy')
        self.runOnAllRequests(YESPDP)

    def testNoPolicy(self) -> None:
        print('Running static Permit tests on no policy')
        self.runOnAllRequests(NOPDP, outcome='Deny')

    def testOtherActions(self) -> None:
        """
        Create a request dynamically and test that it returns a 'Yes'
        """
        authz = ResourceAuthZAttributes()
        authz.set_action('claim')
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=None)

        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP)

    def testCreateSliceOK(self) -> None:
        """
        Create an ASM
        """
        t = fu.ExperimentTopology()

        n1 = t.add_node(name='n1', site='RENC', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        self.assertEqual(n1.capacities.core, 9)
        c1 = n1.add_component(name='com1', model_type=fu.ComponentModelType.SmartNIC_ConnectX_6)
        n2 = t.add_node(name='n2', site='UKY', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        c2 = n2.add_component(name= 'com2', model_type=fu.ComponentModelType.SmartNIC_ConnectX_6)
        ns1 = t.add_network_service(name='ns1', nstype=fu.ServiceType.L2PTP, interfaces=[n1.interface_list[0],
                                                                                         n2.interface_list[0]])
        authz = ResourceAuthZAttributes()

        now = datetime.datetime.now(datetime.timezone.utc)
        delta = datetime.timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta

        authz.collect_resource_attributes(source=t)
        authz.set_action('create')
        authz.set_lifetime(future)
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.SmartNIC',
            'Slice.Multisite'
        ])
        authz.set_resource_subject_and_project(subject_id='user@google.com', project='MyProject')

        print(authz.transform_to_pdp_request())
        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP)

    def testCreateSliceFail(self) -> None:
        t = fu.ExperimentTopology()

        n1 = t.add_node(name='n1', site='RENC', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        self.assertEqual(n1.capacities.core, 9)
        c1 = n1.add_component(name='com1', model_type=fu.ComponentModelType.SmartNIC_ConnectX_6)
        n2 = t.add_node(name='n2', site='UKY', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        c2 = n2.add_component(name= 'com2', model_type=fu.ComponentModelType.SmartNIC_ConnectX_6)
        ns1 = t.add_network_service(name='ns1', nstype=fu.ServiceType.L2PTP, interfaces=[n1.interface_list[0],
                                                                                         n2.interface_list[0]])
        authz = ResourceAuthZAttributes()

        now = datetime.datetime.now(datetime.timezone.utc)
        delta = datetime.timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta

        authz.collect_resource_attributes(source=t)
        authz.set_action('create')
        authz.set_lifetime(future)
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Slice.Multisite'
        ])
        authz.set_resource_subject_and_project(subject_id='user@google.com', project='MyProject')

        print(authz.transform_to_pdp_request())
        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP, 'Deny')

    def testCreateSliverOK(self) -> None:
        
        t = fu.ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        self.assertEqual(n1.capacities.core, 9)
        c1 = n1.add_component(name='com1', model_type=fu.ComponentModelType.SmartNIC_ConnectX_6)
        c2 = n1.add_component(name='gpu1', model_type=fu.ComponentModelType.GPU_RTX6000)

        # get deep sliver for this node
        node_sliver = t.graph_model.build_deep_node_sliver(node_id=n1.node_id)

        authz = ResourceAuthZAttributes()

        now = datetime.datetime.now(datetime.timezone.utc)
        delta = datetime.timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta

        authz.collect_resource_attributes(source=node_sliver)
        authz.set_action('create')
        authz.set_lifetime(future)
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.SmartNIC',
            'Component.GPU'
        ])
        authz.set_resource_subject_and_project(subject_id='user@google.com', project='MyProject')

        print(authz.transform_to_pdp_request())

        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP)

    def testCreateSliverFail(self) -> None:
        t = fu.ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        self.assertEqual(n1.capacities.core, 9)
        c1 = n1.add_component(name='com1', model_type=fu.ComponentModelType.SmartNIC_ConnectX_6)
        c2 = n1.add_component(name='gpu1', model_type=fu.ComponentModelType.GPU_RTX6000)

        # get deep sliver for this node
        node_sliver = t.graph_model.build_deep_node_sliver(node_id=n1.node_id)

        authz = ResourceAuthZAttributes()

        now = datetime.datetime.now(datetime.timezone.utc)
        delta = datetime.timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta

        authz.collect_resource_attributes(source=node_sliver)
        authz.set_action('create')
        authz.set_lifetime(future)
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.GPU'
        ])
        authz.set_resource_subject_and_project(subject_id='user@google.com', project='MyProject')

        print(authz.transform_to_pdp_request())

        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP, 'Deny')

    def testRenewOK(self) -> None:
        #
        # Note that renew always applies to a resource - if no resource type is set in request, it will return permit
        # Renew checks the duration of renew, and like modify checks the renewer is same as creator or same project
        #
        authz = ResourceAuthZAttributes()

        now = datetime.datetime.now(datetime.timezone.utc)
        # less than two weeks
        delta = datetime.timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta

        authz.set_action('renew')
        authz.set_lifetime(future)
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.GPU'
        ])
        authz.set_resource_subject_and_project(subject_id='user@google.com', project='MyProject')

        print(authz.transform_to_pdp_request())

        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP)

    def testRenewFail(self) -> None:
        #
        # Note that renew always applies to a resource - if no resource type is set in request, it will return permit
        # Renew checks the duration of renew, and like modify checks the renewer is same as creator or same project
        #

        authz = ResourceAuthZAttributes()

        now = datetime.datetime.now(datetime.timezone.utc)
        # more than two weeks
        delta = datetime.timedelta(days=15, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta

        authz.set_action('renew')
        authz.set_lifetime(future)
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.GPU'
        ])
        authz.set_resource_subject_and_project(subject_id='user@google.com', project='MyProject')

        print(authz.transform_to_pdp_request())

        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP, 'Deny')

    def testRenewFail1(self) -> None:
        #
        # Note that renew always applies to a resource - if no resource type is set in request, it will return permit
        # Renew checks the duration of renew, and like modify checks the renewer is same as creator or same project
        #
        authz = ResourceAuthZAttributes()

        now = datetime.datetime.now(datetime.timezone.utc)
        delta = datetime.timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta

        authz.set_action('renew')
        authz.set_lifetime(future)
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.GPU'
        ])
        # different user and project
        authz.set_resource_subject_and_project(subject_id='user1@google.com', project='MyOtherProject')

        print(authz.transform_to_pdp_request())

        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP, 'Deny')

    def testModifyOK(self) -> None:
        #
        # modify always applies to a sliver/slice. it only checks modifier == creator or same project
        #

        t = fu.ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        self.assertEqual(n1.capacities.core, 9)

        authz = ResourceAuthZAttributes()
        authz.collect_resource_attributes(source=t)

        authz.set_action('modify')
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.GPU'
        ])
        # same user different project
        authz.set_resource_subject_and_project(subject_id='user@google.com', project='MyOtherProject')

        print(authz.transform_to_pdp_request())

        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP)

    def testModifyFail(self) -> None:
        #
        # modify always applies to a sliver/slice. it only checks if modifier == creator or same project
        #

        t = fu.ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        self.assertEqual(n1.capacities.core, 9)

        authz = ResourceAuthZAttributes()
        authz.collect_resource_attributes(source=t)

        authz.set_action('modify')
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.GPU'
        ])
        # set a different project and user
        authz.set_resource_subject_and_project(subject_id='user1@google.com', project='MyOtherProject')

        print(authz.transform_to_pdp_request())

        self.runOnStringRequest(authz.transform_to_pdp_request(), TAGPDP, 'Deny')

    def testModifyFail1(self) -> None:
        #
        # modify always applies to a sliver/slice. it only checks if modifier == creator or same project
        # Run this on always No policy to get the Deny
        #

        t = fu.ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=fu.Capacities(ram=20, cpu=1, core=9, disk=110))
        self.assertEqual(n1.capacities.core, 9)

        authz = ResourceAuthZAttributes()
        authz.collect_resource_attributes(source=t)

        authz.set_action('modify')
        authz.set_subject_attributes(subject_id='user@google.com', project='MyProject', project_tag=[
            'VM.NoLimit',
            'Component.GPU'
        ])
        # set a different project and user
        authz.set_resource_subject_and_project(subject_id='user1@google.com', project='MyOtherProject')

        print(authz.transform_to_pdp_request())

        self.runOnStringRequest(authz.transform_to_pdp_request(), NOPDP, 'Deny', printResponse=True)
