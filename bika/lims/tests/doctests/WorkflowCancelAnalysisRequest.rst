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

    bin/test -t WorkflowCreateAnalysisRequest

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
route in the workflow to keep track of the sampling process.

If the sampling workflow is disabled, the Sample reaches the state `registered`
first and is automatically transitioned thanks to an `after_transition_event` to
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
system does not allow the rejection of neither an Analysis Request nor a Sample:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False

Thus, `receive` and `cancel` (from `cancellation_workflow`) are the transitions
allowed for the current state of the Sample:

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'receive']

Analysis Request can be `received` too, cause its reception triggers the
reception of the Sample to which belongs. On the other hand, the cancellation
of an Analysis Request does not trigger the cancellation of the Sample, except
if the AnalysisRequest is the only AR from this Sample that remains in a
non-cancelled state:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'receive']

Because a Sample Partition is a "part" of a Sample, Sample Partitions cannot be
received individually, the Sample must be received as a whole. Even though,
Sample Partitions can still be cancelled individually:

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']

As for Sample Partitions, Analyses cannot be received individually. The Analysis
Request that contains them (and therefore, the Sample the Analysis Request
belongs to) must be received as a whole. Moreover, Analyses can not be cancelled
individually, can be removed or retracted (after reception of the Analysis
Request), but not cancelled. On the other hand, analyses have the transition
`assign`, provided by `worksheetanalysis_workflow`, that allows the labman to
assign analyses to analysts:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign']


Primary Analysis Request with rejection reasons enabled
.......................................................

If "Rejection Reasons" are entered in Setup, the system also allows the user to
reject Analysis Requests and Samples:

    >>> bikasetup.setRejectionReasons([{'checkbox': 'on', 'texfield-1': 'AA'}])
    >>> bikasetup.isRejectionWorkflowEnabled()
    True

The allowed transitions for Sample are `receive`, `cancel` and `reject`:

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'receive', 'reject']

The same for Analysis Request. While the reception of an Analysis Request
triggers the reception of the Sample to which belongs, the rejection of an
Analysis Request does not trigger the cancellation of the Sample, except if the
Sample only has assigned the Analysis Request to be rejected:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'receive', 'reject']

Because a Sample Partition is a "part" of a Sample, Sample Partitions cannot be
neither rejected nor received individually, the Sample must be rejected or
received as a whole. Even though, Sample Partitions can still be cancelled
individually:

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']

As for Sample Partitions, Analyses cannot be neither rejected nor received
individually. The Analysis Request that contains them (and therefore, the Sample
the Analysis Request belongs to) must be received or rejected as a whole.
Moreover, Analyses can not be cancelled individually, can be removed or
retracted (after reception of the Analysis Request), but not cancelled. On the
other hand, analyses have the transition `assign`, provided by
`worksheetanalysis_workflow`, that allows the labman the assignment of analyses
to analysts:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign']


Secondary Analysis Request
..........................

If a new Analysis Request is created, but using the same Sample as before, this
new Analysis Request will automatically be transitioned to the same state the
Sample has reached. In this case, the `sample_due` state:

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


Analysis Request creation with Sampling Workflow enabled
--------------------------------------------------------

If the sampling workflow is enabled, the Sample reaches the state `registered`
first and then is automatically transitioned to `to_be_sampled` state:

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

If no Date Sampled (note we've created the Analysis Request with a Sampling Date
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

The same result if we only assign the Date Sampled, but without Sampler:

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

Indeed, we have to assign both Date Sampled and Sampler to allow the `sample`
transition for the Sample:

    >>> sample.setSampler("I am a sampler")
    >>> sample.setDateSampled(date_now)
    >>> 'sample' in getAllowedTransitions(sample)
    True

Analysis Request can be `sampled` too, cause performing this `sample` transition
to the Analysis Request triggers the same transition for the Sample the Analysis
Requests belongs to. And the same the other way round; `sample` transition
applied to a Sample triggers the same transition to all Analysis Requests
associated:

    >>> 'sample' in getAllowedTransitions(ar)
    True

Because a Sample Partition is a "part" of a Sample, Sample Partitions cannot be
sampled individually, the Sample must be sampled as a whole:

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> 'sample' in allowed
    False

As for Sample Partitions, Analyses cannot be sampled individually, the Analysis
Request that contains them (and therefore, the Sample the Analysis Request
belongs to) must be sampled as a whole:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> 'sample' in allowed
    False

Now, check the allowed transitions for this Analysis Request, as well as for its
associated objects. If "Schedule Sampling" and "Rejection Reasons" are disabled
in Setup, then only transitions `cancel` and `sample` are allowed:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False
    >>> bikasetup.setScheduleSamplingEnabled(False)
    >>> bikasetup.getScheduleSamplingEnabled()
    False

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'sample']

Analysis Request can be `sampled` too, cause performing this `sample` transition
to the Analysis Request triggers the same transition for the Sample the Analysis
Requests belongs to. And the same the other way round; `sample` transition
applied to a Sample triggers the same transition to all Analysis Requests
associated:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'sample']

Because a Sample Partition is a "part" of a Sample, Sample Partitions cannot be
sampled individually, the Sample must be sampled as a whole. Even though, Sample
Partitions can still be cancelled individually:

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']

As for Sample Partitions, Analyses cannot be sampled individually. The Analysis
Request that contains them (and therefore, the Sample the Analysis Request
belongs to) must be sampled as a whole. Moreover, Analyses can not be cancelled
individually, can be removed or retracted (after reception of the Analysis
Request), but not cancelled. On the other hand, analyses have the transition
`assign`, provided by `worksheetanalysis_workflow`, that allows the labman the
assignment of analyses to analysts:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign']


Primary Analysis Request with rejection reasons enabled
.......................................................

If "Rejection Reasons" are enabled in Setup, the additional `reject` transition
is available:

    >>> bikasetup.setRejectionReasons([{'checkbox': 'on', 'texfield-1': 'AA'}])
    >>> bikasetup.isRejectionWorkflowEnabled()
    True

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'reject', 'sample']

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'reject', 'sample']

As discussed before, partitions cannot be neither rejected nor sampled
individually, the whole Sample or Analysis Request must be rejected or sampled
instead. Even though, Sample Partitions can still be cancelled individually:

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']

If "Schedule Sampling" is enabled in Setup, an additional transition
`schedule_sampling` is available, but only if the Sample has both a Sampler for
the Scheduled Sampling and a valid Sampling Date assigned:

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
    ['cancel']

So, we need to set a Sampler that will be in charge of Sampling (we already
assigned a Sampling Date when we created the Analysis Request):

    >>> sample.setScheduledSamplingSampler('I will sample')
    >>> sample.getScheduledSamplingSampler()
    'I will sample'

And then, the `schedule_sampling` transition becomes available:

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'reject', 'sample', 'schedule_sampling']

    >>> sorted(getAllowedTransitions(ar))
    ['cancel', 'reject', 'sample', 'schedule_sampling']

As for `reject` and `sample`, the `schedule_sampling` transition cannot be
performed individually to a Sample Partition:

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel']

Analyses cannot be scheduled for sampling. The Analysis Request that contains
them (and therefore, the Sample the Analysis Request belongs to) must be
scheduled for sampling as a whole. Moreover, Analyses can not be cancelled
individually, can be removed or retracted (after reception of the Analysis
Request), but not cancelled. On the other hand, analyses have the transition
`assign`, provided by `worksheetanalysis_workflow`, that allows the labman the
assignment of analyses to analysts:

    >>> allowed = [getAllowedTransitions(analysis) for analysis in analyses]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['assign']


Secondary Analysis Request
..........................

If a new Analysis Request is created, but using the same Sample as before, this
new Anlaysis Request will automatically be transitioned to the same state the
Sample has reached. In this case, the `to_be_sampled` state:

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
