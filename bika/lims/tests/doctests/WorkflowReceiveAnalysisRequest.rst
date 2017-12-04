===================================
Workflow - Receive Analysis Request
===================================

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

Thus, this doctest validates the consistency amongst these different, but
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

Sampling workflow is a setting that lives in `setup` and enables an additional
route in the workflow to keep track of the sampling process. If the sampling
workflow is disabled, the Sample reaches the state `registered` first and is
automatically transitioned thanks to an `after_transition_event` to
`sample_due` state. Because Sampling workflow only has effect before the
`receive` transition, we omit this setting: :

    >>> bikasetup.setSamplingWorkflowEnabled(False)

Analysis Request reception
--------------------------

We create a primary Analysis Request:

    >>> setRoles(portal, TEST_USER_ID, ['LabManager',])
    >>> values = {
    ...     'Client': client.UID(),
    ...     'Contact': contact.UID(),
    ...     'DateSampled': date_now,
    ...     'SampleType': sampletype.UID()}
    >>> service_uids = [Cu.UID(), Fe.UID()]
    >>> ar = create_analysisrequest(client, request, values, service_uids)

Because sampling workflow is disabled, the current state of the Analysis
Request is `sample_due`:

    >>> getCurrentState(ar)
    'sample_due'

We receive the analysis request:

    >>> performed = doActionFor(ar, 'receive')

And check the current state of the Analysis Request and objects associated are
correct:

    >>> getCurrentState(ar)
    'sample_received'

    >>> sample = ar.getSample()
    >>> getCurrentState(sample)
    'sample_received'

    >>> parts = sample.getSamplePartitions()
    >>> [getCurrentState(part) for part in parts]
    ['sample_received']

    >>> analyses = ar.getAnalyses()
    >>> [getCurrentState(an) for an in analyses]
    ['sample_received', 'sample_received']

Now, check the allowed transitions for this Analysis Request, as well as for its
associated objects. If no "Rejection Reasons" have been entered in Setup, the
system does not allow the rejection of an Analysis Request and Sample:

    >>> bikasetup.setRejectionReasons([])
    >>> bikasetup.isRejectionWorkflowEnabled()
    False

Thus, `expire` and `cancel` (from `cancellation_workflow`) are the allowed
transitions for Sample and Sample Partitions:

    >>> sorted(getAllowedTransitions(sample))
    ['cancel', 'expire']

    >>> allowed = [getAllowedTransitions(part) for part in parts]
    >>> allowed = [item for sublist in allowed for item in sublist]
    >>> sorted(set(allowed))
    ['cancel', 'expire']

While only `cancel` (from `cancellation_workflow`) is allowed for the current
state of the Analysis Request. The `expire` transition exists for the Analysis
Request, but is only allowed when the transition `expire` to the Sample
associated to the Analysis Request has been triggered. This is, we don't want
this transition to appear in Analysis Requests actions, rather we want this
action to be performed automatically when a Sample is `expired`. Consequently,
`guard_expire` for analysis request only returns true if the Sample has been
transitioned already:

    >>> sorted(getAllowedTransitions(ar))
    ['cancel']

