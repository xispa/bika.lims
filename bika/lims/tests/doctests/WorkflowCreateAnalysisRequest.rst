==================================
Workflow - Create Analysis Request
==================================

:download:`sample_workflow <../../../../docs/resources/bika_sample_workflow.svg>`
is a DCWorkflow that defines the status an object of type `Sample` can reach,
as well as the transitions allowed from any given state to other states
depending on the user rights for that specific state and other factors verified
by guards.

Some of the statuses and transitions set in `sample_workflow`, specially those
related with the initial statuses of a Sample until it gets received, are in
sync with transitions set in `ar_workflow` and in `analysis_workflow`. For
example, if a Sample is transitioned to `sampled` state, the Analysis Requests
associated to this sample will also be transitioned to the same `state`, as well
as its associated analyses.

Thus, this doctest will validate the consistency amongst these different, but
strongly related objects, during the creation process.

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

We will test the sample creation with Lab Manager privileges:

    >>> setRoles(portal, TEST_USER_ID, ['LabManager',])

Analysis Request creation with Sampling Workflow disabled
---------------------------------------------------------

Sampling workflow is a setting that lives in `setup` and enables an additional
route in the workflow to keep track of the sampling process. If the sampling
workflow is disabled, the Sample reaches the state `registered` first and is
automatically transitioned thanks to an `after_transition_event` to
`sample_due` state:

    >>> bikasetup.setSamplingWorkflowEnabled(False)

Primary Analysis Request
........................

Crete an Analysis Request, that in turn will create a Sample, a Sample Partition
and the Analyses associated. Since Sampling workflow is disabled, all them will
be automatically transitioned to `sample_due`:

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

    >>> analyses = ar.getAnalyses()
    >>> [getCurrentState(an) for an in analyses]
    ['sample_due', 'sample_due']

Now, check the allowed transitions for this Analysis Request, as well as for its
associated objects. If no "Rejection Reasons" have been entered in Setup, the
system does not allow the rejection of an Analysis Request and Sample:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False

Thus, `receive` and `cancel` (from `cancellation_workflow`) are only allowed
for the current state of the Analysis Request, Sample and Sample Partitions:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'receive']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'receive']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'receive']

For analyses, the transition `assign`, that comes from `worksheet_workflow`, is
allowed too:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign', 'cancel', 'receive']

If "Rejection Reasons" are entered in Setup, the system also allows the Analysis
Request, Sample and Sample Partitions to be rejected:

    >>> bikasetup.setRejectionReasons([{'checkbox': 'on', 'texfield-1': 'AA'}])
    >>> bikasetup.isRejectionWorkflowEnabled()
    True

Therefore, the allowed transitions for Analysis Request, Sample and Sample
Partitions are `cancel` (from `cancellation_workflow`), `receive` and `reject`:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'receive', 'reject']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'receive', 'reject']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'receive', 'reject']

There is no `reject` transition for analyses, cause the rejection is done at
Analysis Request and/or Sample levels, without effect to analyses. Rather,
analyses have the transition `assign`, that comes from `worksheet_workflow`:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign', 'cancel', 'receive']

Secondary Analysis Request
..........................

If we create a new Analysis Request, but using the same Sample as before, this
new Analysis Request will automatically be transitioned to `sample_due` state:

    >>> values['Sample'] = sample.UID()
    >>> ar = create_analysisrequest(client, request, values, service_uids)
    >>> getCurrentState(ar)
    'sample_due'

As well as its associated Sample Partitions:

    >>> parts = ar.getPartitions()
    >>> [getCurrentState(part) for part in parts]
    ['sample_due']

And its analyses:

    >>> analyses = ar.getAnalyses()
    >>> [getCurrentState(an) for an in analyses]
    ['sample_due', 'sample_due']

Now, check the allowed transitions for this secondary Analysis Request, as well
as for its associated objects. If no "Rejection Reasons" have been entered in
Setup, the system does not allow the rejection of an Analysis Request:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False

Thus, `receive` and `cancel` (from `cancellation_workflow`) are only allowed
for the current state of the Analysis Request, Sample and Sample Partitions:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'receive']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'receive']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'receive']

For analyses, the transition `assign`, that comes from `worksheet_workflow`, is
allowed too:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign', 'cancel', 'receive']

If "Rejection Reasons" are entered in Setup, the system also allows the
rejection of the Analysis Request, Sample and Sample Partitions:

    >>> bikasetup.setRejectionReasons([{'checkbox': 'on', 'texfield-1': 'AA'}])
    >>> bikasetup.isRejectionWorkflowEnabled()
    True

Therefore, the allowed transitions for Analysis Request, Sample and Sample
Partitions are `cancel` (from `cancellation_workflow`), `receive` and `reject`:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'receive', 'reject']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'receive', 'reject']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'receive', 'reject']

There is no 'reject' transition for analyses, cause the rejection is done at
AnalysisRequest and/or Sample levels, without effect to analyses. Rather,
analyses have the transition `assign`, that comes from `worksheet_workflow`:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign', 'cancel', 'receive']

Analysis Request creation with Sampling Workflow enabled
--------------------------------------------------------

Sampling workflow is a setting that lives in `setup` that enables an additional
route in the workflow to keep track of the sampling process. If the sampling
workflow is enabled, the Sample reaches the state `registered` first and then
is automatically transitioned to `to_be_sampled` state:

    >>> bikasetup.setSamplingWorkflowEnabled(True)

Primary Analysis Request
........................

Crete an Analysis Request, that in turn will create a Sample, a Sample Partition
and the Analyses associated. Since Sampling workflow is enabled, all them will
be automatically transitioned to `to_be_sampled`:

    >>> values = {
    ...     'Client': client.UID(),
    ...     'Contact': contact.UID(),
    ...     'SamplingDate': date_future,
    ...     'SampleType': sampletype.UID()}
    >>> service_uids = [Cu.UID(), Fe.UID()]
    >>> ar = create_analysisrequest(client, request, values, service_uids)
    >>> getCurrentState(ar)
    'to_be_sampled'

    >>> sample = ar.getSample()
    >>> getCurrentState(sample)
    'to_be_sampled'

    >>> parts = sample.getSamplePartitions()
    >>> [getCurrentState(part) for part in parts]
    ['to_be_sampled']

    >>> analyses = ar.getAnalyses()
    >>> [getCurrentState(an) for an in analyses]
    ['to_be_sampled', 'to_be_sampled']

If no Date Sampled (not we've created the Analysis Request with a Samplind Date
instead of a Date Sampled) and Sampler are not set, `sample` transition is not
allowed:

    >>> 'sample' in getAllowedTransitions(ar)
    False

    >>> 'sample' in getAllowedTransitions(sample)
    False

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> 'sample' in allowed
    False

We can assign a Sampler, but if no Date Sampled is assigned, the `sample`
transition is still not allowed:

    >>> sample.setSampler("I am a sampler")
    >>> sample.getSampler()
    'I am a sampler'

    >>> 'sample' in getAllowedTransitions(ar)
    False

    >>> 'sample' in getAllowedTransitions(sample)
    False

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> 'sample' in allowed
    False

The same result if we only assign the Date Sampled:

    >>> sample.setSampler(None)
    >>> sample.setDateSampled(date_now)
    >>> 'sample' in getAllowedTransitions(ar)
    False

    >>> 'sample' in getAllowedTransitions(sample)
    False

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> 'sample' in allowed
    False

Indeed, we have to assign both Date Sampled and Sampler for the transition
`sample` to be allowed:

    >>> sample.setSampler("I am a sampler")
    >>> sample.setDateSampled(date_now)
    >>> 'sample' in getAllowedTransitions(ar)
    True

    >>> 'sample' in getAllowedTransitions(sample)
    True

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> 'sample' in allowed
    True

But note that `sample` transition is not allowed for analyses, cause this
transition is performed automatically to them when their assigned Sample
Partitions are effectively transitioned (analysis guard for `sample` only
returns True if the transition has already been performed to the Sample
Partition). In summary, we do not want the user to be able to "Sample" an
Analysis, it doesn't make sense. This state is maintained in `analysis_workflow`
for sync purposes with the Sample Partition only:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> 'sample' in allowed
    False

Now, check the allowed transitions for this Analysis Request, as well as for its
associated objects. If "Schedule Sampling" and "Rejection Reasons" are disabled
in Setup, then only transitions `cancel` from `cancellation_workflow` and
`sample` are allowed:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False
    >>> bikasetup.setScheduleSamplingEnabled(False)
    >>> bikasetup.getScheduleSamplingEnabled()
    False

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'sample']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'sample']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'sample']

For analyses, only the transition `assign`, that comes from
`worksheet_workflow`, and `cancel` that comes from `cancellation_workflow` are
allowed. Remember that `sample` transition is not allowed for analyses:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign', 'cancel']

If "Rejection Reasons" are enabled in Setup, the additional `reject` transition
is available:

    >>> bikasetup.setRejectionReasons([{'checkbox': 'on', 'texfield-1': 'AA'}])
    >>> bikasetup.isRejectionWorkflowEnabled()
    True

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'reject', 'sample']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'reject', 'sample']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'reject', 'sample']

If "Schedule Sampling" is enabled in Setup, an additional transition
`schedule_sampling` is available, but only if a Sampler for the Schedule and
a Sampling Date are assigned:

    >>> bikasetup.setScheduleSamplingEnabled(True)
    >>> bikasetup.getScheduleSamplingEnabled()
    True

    >>> sample.getScheduledSamplingSampler()
    ''

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'reject', 'sample']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'reject', 'sample']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'reject', 'sample']

So, we need to set a Sampler that will be in charge of Sampling (we already
assigned a Sampling Date when we created the Analysis Request):

    >>> sample.setScheduledSamplingSampler('I will sample')
    >>> sample.getScheduledSamplingSampler()
    'I will sample'

And then, the `schedule_sampling` transition becomes available:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'reject', 'sample', 'schedule_sampling']

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'reject', 'sample', 'schedule_sampling']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'reject', 'sample', 'schedule_sampling']

There is neither `reject` nor `schedule_sampling` transitions for analyses,
cause both transitions have meaning at AnalysisRequest and/or Sample levels.
Rather, analyses have the transition `assign`, that comes from
`worksheet_workflow`. Remember that `sample` transition is not allowed for
analyses:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign', 'cancel']

Secondary Analysis Request
..........................

If we create a new Analysis Request, but using the same Sample as before, this
new AR will automatically be transitioned to `to_be_sampled` state:

    >>> values['Sample'] = sample.UID()
    >>> ar = create_analysisrequest(client, request, values, service_uids)
    >>> getCurrentState(ar)
    'to_be_sampled'

As well as its associated Sample Partitions:

    >>> parts = ar.getPartitions()
    >>> [getCurrentState(part) for part in parts]
    ['to_be_sampled']

And its analyses:

    >>> analyses = ar.getAnalyses()
    >>> [getCurrentState(an) for an in analyses]
    ['to_be_sampled', 'to_be_sampled']

Since we've reused the same Sample as before, both Date Sampled and Sampler are
preserved and transition `sample` is allowed for this secondary AR:

    >>> 'sample' in getAllowedTransitions(ar)
    True

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> 'sample' in allowed
    True
