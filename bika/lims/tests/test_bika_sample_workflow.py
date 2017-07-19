# coding=utf-8

from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login, logout

from bika.lims.testing import BIKA_FUNCTIONAL_TESTING
from bika.lims.tests.base import BikaFunctionalTestCase
from bika.lims.utils.analysisrequest import create_analysisrequest
from bika.lims.workflow import doActionFor
from bika.lims.workflow import getCurrentState

try:
    import unittest2 as unittest
except ImportError: # Python 2.7
    import unittest


class TestBikaSampleWorkflow(BikaFunctionalTestCase):
    layer = BIKA_FUNCTIONAL_TESTING

    def setUp(self):
        super(TestBikaSampleWorkflow, self).setUp()
        login(self.portal, TEST_USER_NAME)
        self.portal.bika_setup.setPrintingWorkflowEnabled(False)
        self.portal.bika_setup.setSamplingWorkflowEnabled(False)
        self.portal.bika_setup.setScheduleSamplingEnabled(False)

    def tearDown(self):
        super(TestBikaSampleWorkflow, self).tearDown()
        self.portal.bika_setup.setPrintingWorkflowEnabled(False)
        self.portal.bika_setup.setSamplingWorkflowEnabled(False)
        self.portal.bika_setup.setScheduleSamplingEnabled(False)
        logout()

    def test_workflow_01(self):
        ar = self._create_simple_analysis_request()
        self._assert_statuses(ar, 'sample_due')
        self._assert_transition(ar, 'receive', 'sample_received')
        self._assert_transition(ar, 'expire', 'expired')
        self._assert_transition(ar, 'dispose', 'disposed')

    def test_workflow_02(self):
        ar = self._create_simple_analysis_request()
        self._assert_statuses(ar, 'sample_due')
        self._assert_transition(ar, 'receive', 'sample_received')
        self._assert_transition(ar, 'expire', 'expired')
        self._assert_transition(ar, 'reject', 'rejected')

    def test_workflow_03(self):
        ar = self._create_simple_analysis_request()
        self._assert_statuses(ar, 'sample_due')
        self._assert_transition(ar, 'receive', 'sample_received')
        self._assert_transition(ar, 'reject', 'rejected')

    def test_workflow_04(self):
        ar = self._create_simple_analysis_request()
        self._assert_statuses(ar, 'sample_due')
        self._assert_transition(ar, 'reject', 'rejected')

    def _assert_transition(self, ar, transition_id, end_status):
        doActionFor(ar, transition_id)
        self._assert_statuses(ar, end_status)

    def _assert_statuses(self, ar, status):
        sample = ar.getSample()
        parts = ar.getPartitions()
        analyses = ar.getAnalyses()
        self.assertEquals(getCurrentState(ar), status)
        self.assertEquals(getCurrentState(sample), status)
        for part in parts:
            self.assertEquals(getCurrentState(part), status)
        for analysis in analyses:
            self.assertEquals(getCurrentState(analysis), status)

    def _create_simple_analysis_request(self):
        # Client:       Happy Hills
        # SampleType:   Apple Pulp
        # Contact:      Rita Mohale
        # Analyses:     [Calcium, Copper]
        client = self.portal.clients['client-1']
        sample_type = self.portal.bika_setup.bika_sampletypes['sampletype-1']
        values = {'Client': client.UID(),
                  'Contact': client.getContacts()[0].UID(),
                  'SamplingDate': '2015-01-01',
                  'SampleType': sample_type.UID()}
        request = {}
        services = [s.UID() for s in self.services]
        return create_analysisrequest(client, request, values, services)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBikaSampleWorkflow))
    suite.layer = BIKA_FUNCTIONAL_TESTING
    return suite
