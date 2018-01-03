==============================================
Sample Workflow - Sampling Workflow Transition
==============================================

:download:`sample_workflow <../../../../docs/resources/bika_sample_workflow.svg>`
is a DCWorkflow that defines the status an object of type `Sample` can reach,
as well as the transitions allowed from any given state to other states
depending on the user rights for that specific state and other factors verified
by guards.

Some of the statuses and transitions set in `sample_workflow`, especially those
related with the initial statuses of a Sample until it gets received, are in
sync with transitions set in `ar_workflow` and in `analysis_workflow`. For
example, if a Sample is transitioned to `sampled` state, the Analysis Requests
associated to this sample will also be transitioned to the same status, as well
as its associated analyses.

`sampling_workflow` transition is automatically triggered once a Sample is
created (status `sample_registered`), but only if the sampling workflow setting
in Setup is enabled. In turn, after `sampling_workflow` is performed to the
Sample, the same transition is automatically triggered to its children (Sample
Partitions, Analysis requests and Analyses). As a result, all these objects,
including the Sample itself, reach the status `to_be_sampled`.

This doctest validates the transition `sampling_workflow` for a Sample, as well
 as its status and transition integrity with its strongly related objects, such
as Sample Partitions, Analysis Requests and Analyses.


Test Setup
==========

Running this test from the buildout directory:

    bin/test -t WorkflowSampleNoSamplingWorkflow

Needed Imports:

    >>> import re
    >>> from AccessControl.PermissionRole import rolesForPermissionOn
    >>> from plone import api as ploneapi
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
    ...
    >>> def get_current_states(objects):
    ...     states = [getCurrentState(obj) for obj in objects]
    ...     return sorted(set(states))
    ...
    >>> def get_allowed_transitions(objects):
    ...     allowed = [getAllowedTransitions(obj) for obj in objects]
    ...     allowed = [item for sublist in allowed for item in sublist]
    ...     return sorted(set(allowed))

Variables:

    >>> portal = self.portal
    >>> request = self.request
    >>> bikasetup = portal.bika_setup
    >>> date_now = DateTime().strftime("%Y-%m-%d")
    >>> date_future = (DateTime() + 5).strftime("%Y-%m-%d")

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
    >>> sampler_contact = api.create(bikasetup.bika_labcontacts, "Sampler", Firstname="Test", Lastname="Sampler")
    >>> sampler = ploneapi.user.create(email="sampler@example.com", username="sampler", password=TEST_USER_PASSWORD, properties=dict(fullname="Test Sampler"))
    >>> setRoles(portal, 'sampler', ['Sampler', ])
    >>> sampler_contact.setUser(sampler)

We will test with Lab Manager privileges:

    >>> setRoles(portal, TEST_USER_ID, ['LabManager',])

Sampling workflow is a setting that lives in Setup and enables an additional
route in the workflow to keep track of the sampling process. If the sampling
workflow is enabled, the Sample reaches the state `registered` first and then,
automatically transitioned thanks to an `after_transition_event` to
`to_be_sampled` status, throgh `sampling_workflow` transition:

    >>> bikasetup.setSamplingWorkflowEnabled(True)
    >>> bikasetup.getSamplingWorkflowEnabled()
    True


Primary Analysis Request
========================

Create a primary Analysis Request:

    >>> values = {
    ...     'Client': client.UID(),
    ...     'Contact': contact.UID(),
    ...     'SamplingDate': date_now,
    ...     'SampleType': sampletype.UID()}
    >>> service_uids = [Cu.UID(), Fe.UID()]
    >>> ar = create_analysisrequest(client, request, values, service_uids)

Because sampling workflow is enabled, the current state of the Analysis Request
is `to_be_sampled`:

    >>> getCurrentState(ar)
    'to_be_sampled'

As well as the Sample object the Analysis Request relates to, Sample Partitions
and Analyses:

    >>> sample = ar.getSample()
    >>> getCurrentState(sample)
    'to_be_sampled'

    >>> partitions = sample.getSamplePartitions()
    >>> get_current_states(partitions)
    ['to_be_sampled']

    >>> analyses = ar.getAnalyses()
    >>> get_current_states(analyses)
    ['to_be_sampled']


Validate transitions for "to_be_sampled" when a Sampler is not set
------------------------------------------------------------------

When a "Sampler" is not set, the transition `sample` is not allowed.


With rejection reasons disabled
...............................

If no "Rejection reasons" have been entered in Setup, the system does not allow
the rejection of neither Analysis Requests nor Samples:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False

Thus, `scheduled_sampling` and `cancel` are the only allowed transitions for
both the Analysis Request and Sample:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'scheduled_sampling']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'scheduled_sampling']

But although both partitions and analyses can be cancelled, none of them can be
scheduled individually:

    >>> get_allowed_transitions(partitions)
    ['cancel']

    >>> get_allowed_transitions(analyses)
    ['cancel']


With rejection reasons enabled
..............................

If "Rejection reasons" have been entered in Setup, the system does allow the
rejection of Analysis Requests and Samples:

    >>> reasons = [{'checkbox': 'on',
    ...             'textfield-0': 'a',
    ...             'textfield-1': 'b',
    ...             'textfield-2': 'c'}]
    >>> bikasetup.setRejectionReasons(reasons)
    >>> bikasetup.isRejectionWorkflowEnabled()
    True

Thus, `reject`, `scheduled_sampling` and `cancel` are the only allowed
transitions for both the Analysis Request and Sample:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'reject', 'scheduled_sampling']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'reject', 'scheduled_sampling]

But although both partitions and analyses can be cancelled, none of them can be
neither scheduled nor rejected individually:

    >>> get_allowed_transitions(partitions)
    ['cancel']

    >>> get_allowed_transitions(analyses)
    ['cancel']

Disable rejection reasons again:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False


Validate transitions for "to_be_sampled" when a Sampler is not set
------------------------------------------------------------------

Set a Sampler for the Sample:

    >>> sample.setSampler(sampler.getId())
    >>> sample.getSampler()
    'sampler'

With rejection reasons disabled
...............................

If no "Rejection reasons" have been entered in Setup, the system does not allow
the rejection of neither Analysis Requests nor Samples:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False

Thus, `sample`, `scheduled_sampling` and `cancel` are the only allowed
transitions for both the Analysis Request and Sample:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'sample', 'scheduled_sampling']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'sample', 'scheduled_sampling']

But although both partitions and analyses can be cancelled, none of them can be
neither sampled nor scheduled individually:

    >>> get_allowed_transitions(partitions)
    ['cancel']

    >>> get_allowed_transitions(analyses)
    ['cancel']


With rejection reasons enabled
..............................

If "Rejection reasons" have been entered in Setup, the system does allow the
rejection of Analysis Requests and Samples:

    >>> reasons = [{'checkbox': 'on',
    ...             'textfield-0': 'a',
    ...             'textfield-1': 'b',
    ...             'textfield-2': 'c'}]
    >>> bikasetup.setRejectionReasons(reasons)
    >>> bikasetup.isRejectionWorkflowEnabled()
    True

Thus, `sample`, `reject`, `scheduled_sampling` and `cancel` are the only allowed
transitions for both the Analysis Request and Sample:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'reject', 'sample', 'scheduled_sampling']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'reject', 'sample', 'scheduled_sampling]

But although both partitions and analyses can be cancelled, none of them can be
sampled, scheduled or rejected individually:

    >>> get_allowed_transitions(partitions)
    ['cancel']

    >>> get_allowed_transitions(analyses)
    ['cancel']

Disable rejection reasons again:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False

And unset the Sampler:

    >>> sample.setSampler(None)
    >>> sample.getSampler()
    ''
