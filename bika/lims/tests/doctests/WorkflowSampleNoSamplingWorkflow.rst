=================================================
Sample Workflow - No Sampling Workflow Transition
=================================================

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

`no_sampling_workflow` transition is automatically triggered once a Sample is
created (status `sample_registered`), but only if the sampling workflow setting
in Setup is disabled. In turn, after `no_sampling_workflow` is performed to the
Sample, the same transition is automatically triggered to its children (Sample
Partitions, Analysis requests and Analyses). As a result, all these objects,
including the Sample itself, reach the status `sampled`.

When Sample reaches the state `sampled`, the transition `sample_due` is
automatically triggered to the Sample and its children, but only if the Sample
does not require a preservation (this depends on the container used and/or the
Sample Type). As a result, the Sample and its children will reach the status
`sample_due`.

This doctest validates the transition `no_sampling_workflow` for a Sample, as
well as its status and transition integrity with its strongly related objects,
such as Sample Partitions, Analysis Requests and Analyses. For the sake of
clarity and simplicity, this test does not validate the transitions involved
when the Sampling Workflow is enabled in Setup or when the Sample requires
preservation. These use cases are validated in other doctests.


Test Setup
==========

Running this test from the buildout directory:

    bin/test -t WorkflowSampleNoSamplingWorkflow

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

We will test with Lab Manager privileges:

    >>> setRoles(portal, TEST_USER_ID, ['LabManager',])


Analysis Request and Sample creation with Sample Workflow Disabled
==================================================================

Sampling workflow is a setting that lives in Setup and enables an additional
route in the workflow to keep track of the sampling process. If the sampling
workflow is disabled, the Sample reaches the state `registered` first and is
automatically transitioned thanks to an `after_transition_event` to `sampled`
status first and then, if no preservation is required, is automatically
transitioned to `sample_due` state:

    >>> bikasetup.setSamplingWorkflowEnabled(False)

Create a primary Analysis Request:

    >>> values = {
    ...     'Client': client.UID(),
    ...     'Contact': contact.UID(),
    ...     'DateSampled': date_now,
    ...     'SampleType': sampletype.UID()}
    >>> service_uids = [Cu.UID(), Fe.UID()]
    >>> ar = create_analysisrequest(client, request, values, service_uids)

Because sampling workflow is disabled and the sample does not require
preservation, the current state of the Analysis Request is `sample_due`:

    >>> getCurrentState(ar)
    'sample_due'

As well as the Sample object the Analysis Request relates to, Sample Partitions
and Analyses:

    >>> sample = ar.getSample()
    >>> getCurrentState(sample)
    'sample_due'

    >>> partitions = sample.getSamplePartitions()
    >>> [getCurrentState(part) for part in partitions]
    ['sample_due']

    >>> analyses = ar.getAnalyses()
    >>> [getCurrentState(an) for an in analyses]
    ['sample_due', 'sample_due']


Validate transitions when Sample Due with rejections reasons disabled
---------------------------------------------------------------------

If no "Rejection reasons" have been entered in Setup, the system does not allow
the rejection of neither Analysis Requests nor Samples:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False

Thus, `receive` and `cancel` (from `cancellation_workflow`) are the only allowed
transitions for the Analysis Request and Sample:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'receive']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'receive']

But although partitions can be cancelled, cannot be received individually:

    >>> allowed = [getAllowedTransitions(part) for part in partitions]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']

And the same with analyses:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']


Validate transitions when Sample Due with rejections reasons enabled
--------------------------------------------------------------------

If "Rejection reasons" have been entered in Setup, the system does allow the
rejection of Analysis Requests and Samples:

    >>> reasons = [{'checkbox': 'on',
    ...             'textfield-0': 'a',
    ...             'textfield-1': 'b',
    ...             'textfield-2': 'c'}]
    >>> bikasetup.setRejectionReasons(reasons)
    >>> bikasetup.isRejectionWorkflowEnabled()
    True

Thus, `reject`, `receive` and `cancel` (from `cancellation_workflow`) are the
only allowed transitions for the Analysis Request and Sample:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'receive', 'reject']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'receive', 'reject']

But although partitions can be cancelled, cannot be neither received or rejected
individually:

    >>> allowed = [getAllowedTransitions(part) for part in partitions]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']

And the same with analyses:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']
