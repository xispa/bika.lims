==================================
Workflow - Create Analysis Request
==================================

:download:`sample_workflow <../../../../docs/resources/bika_sample_workflow.svg>`
is a DCWorkflow that defines the status an object of type `Sample` can reach,
as well as the transitions allowed from any given state to other states
depending on the user rights for that specific state and other factors verified
by guards.

Although `sample_workflow` applies initially to objects from type `Sample`,
other types such as `AnalysisRequest` and `Analysis` are attached to this
workflow. The aim was to ensure consistence amongst these strongly related
objects. Nevertheless, this approach will be replaced in future:
`AnalysisRequest` and `Analysis` types will be dettached from `sample_workflow`.

Test Setup
==========

Running this test from the buildout directory:

    bin/test -t SampleWorkflow

Needed Imports:

    >>> import re
    >>> from AccessControl.PermissionRole import rolesForPermissionOn
    >>> from bika.lims import api
    >>> from bika.lims.content.analysisrequest import AnalysisRequest
    >>> from bika.lims.content.sample import Sample
    >>> from bika.lims.content.samplepartition import SamplePartition
    >>> from bika.lims.utils.analysisrequest import create_analysisrequest
    >>> from bika.lims.utils.sample import create_sample
    >>> from bika.lims.workflow import doActionFor
    >>> from bika.lims.workflow import getCurrentState
    >>> from bika.lims.workflow import getAllowedTransitions
    >>> from DateTime import DateTime
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from plone.app.testing import setRoles

Functional Helpers:

    >>> def start_server():
    ...     from Testing.ZopeTestCase.utils import startZServer
    ...     ip, port = startZServer()
    ...     return "http://{}:{}/{}".format(ip, port, portal.id)

Variables:

    >>> portal = self.portal
    >>> request = self.request
    >>> bikasetup = portal.bika_setup
    >>> date_now = DateTime().strftime("%Y-%m-%d")

We need to create some basic objects for the test:

    >>> setRoles(portal, TEST_USER_ID, ['LabManager',])
    >>> client = api.create(portal.clients, "Client", Name="Happy Hills", ClientID="HH", MemberDiscountApplies=True)
    >>> contact = api.create(client, "Contact", Firstname="Rita", Lastname="Mohale")
    >>> sampletype = api.create(bikasetup.bika_sampletypes, "SampleType", title="Water", Prefix="W")
    >>> labcontact = api.create(bikasetup.bika_labcontacts, "LabContact", Firstname="Lab", Lastname="Manager")
    >>> department = api.create(bikasetup.bika_departments, "Department", title="Chemistry", Manager=labcontact)
    >>> category = api.create(bikasetup.bika_analysiscategories, "AnalysisCategory", title="Metals", Department=department)
    >>> Cu = api.create(bikasetup.bika_analysisservices, "AnalysisService", title="Copper", Keyword="Cu", Price="15", Category=category.UID(), Accredited=True)
    >>> Fe = api.create(bikasetup.bika_analysisservices, "AnalysisService", title="Iron", Keyword="Fe", Price="10", Category=category.UID())

Analysis Request creation with Sampling Workflow disabled
---------------------------------------------------------

Sampling workflow is a setting that lives in `setup` that enables an additional
route in the workflow to keep track of the sampling process. If the sampling
workflow is disabled, the Sample reaches the state `registered` first and is
transitioned thanks to an `after_transition_event` to `sample_due` state:

    >>> bikasetup.setSamplingWorkflowEnabled(False)

We will test the sample creation with Lab Manager privileges:

    >>> setRoles(portal, TEST_USER_ID, ['LabManager',])

Primary Analysis Request
........................

Crete an Analysis Request, that in turn will create a Sample, a Sample Partition
and the Analyses associated. Since Sampling workflow is disabled, all them will
be automatically transitioned to `sample_due`

    >>> values = {
    ...     'Client': client.UID(),
    ...     'Contact': contact.UID(),
    ...     'DateSampled': date_now,
    ...     'SampleType': sampletype.UID()}
    >>> service_uids = [Cu.UID(), Fe.UID()]
    >>> ar = create_analysisrequest(client, request, values, service_uids)
    >>> getCurrentState(ar)
    'sample_due'

    >>> sample = ar.getSample()
    >>> getCurrentState(sample)
    'sample_due'

    >>> parts = sample.getSamplePartitions()
    >>> [getCurrentState(part) for part in parts]
    ['sample_due']

    >>> analyses = ar.getAnalyses(full_objects=True)
    >>> [getCurrentState(an) for an in analyses]
    ['sample_due', 'sample_due']

Secondary Analysis Request
..........................

If we create a new Analysis Request, but using the same Sample as before, this
new AR will automatically be transitioned to `sample_due` state:

    >>> values['Sample'] = sample.UID()
    >>> ar1 = create_analysisrequest(client, request, values, service_uids)
    >>> getCurrentState(ar1)
    'sample_due'

As well as its associated Sample Partitions:

    >>> parts_ar1 = ar1.getPartitions()
    >>> [getCurrentState(part) for part in parts_ar1]
    ['sample_due']

And its analyses:

    >>> analyses_ar1 = ar1.getAnalyses()
    >>> [getCurrentState(an) for an in analyses_ar1]
    ['sample_due', 'sample_due']

