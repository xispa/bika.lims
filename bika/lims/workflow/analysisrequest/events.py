# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.CORE
#
# Copyright 2018 by it's authors.
# Some rights reserved. See LICENSE.rst, CONTRIBUTORS.rst.

from DateTime import DateTime
from bika.lims import api
from bika.lims.workflow import doActionFor
from bika.lims.workflow import getCurrentState


def _promote_transition(analysis_request, transition_id):
    """Promotes the transition passed in to the Sample Partitions assigned to
    the Analysis Request passed in.
    :param analysis_request: Analysis Request that promotes the transition
    :param transition_id: Unique id of the transition
    """
    partitions = analysis_request.getPartitions()
    for partition in partitions:
        doActionFor(partition, transition_id)

def after_no_sampling_workflow(analysis_request):
    """Method triggered after a 'sampling_workflow' transition for the
    Analysis Request passed in is performed. Tries to perform the same
    transition to the Sample associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'no_sampling_workflow')


def after_sampling_workflow(analysis_request):
    """Method triggered after a 'sampling_workflow' transition for the
    Analysis Request passed in is performed. Tries to perform the same
    transition to the Sample associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'sampling_workflow')


def after_to_be_preserved(analysis_request):
    """Method triggered after a 'sampling_workflow' transition for the
    Analysis Request passed in is performed. Tries to perform the same
    transition to the Sample associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'to_be_preserved')


def after_preserve(analysis_request):
    """Method triggered after a 'preserve' transition for the Analysis Request
    passed in is performed. Tries to perform the same transition to the Sample
    associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'preserve')


def after_schedule_sampling(analysis_request):
    """Method triggered after a 'schedule_sampling' transition for the
    Analysis Request passed in is performed. Tries to perform the same
    transition to the Sample associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'schedule_sampling')


def after_sample(analysis_request):
    """Method triggered after a 'sample' transition for the Analysis Request
    passed in is performed. Tries to perform the same transition to the Sample
    associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'sample')


def after_sample_due(analysis_request):
    """Method triggered after a 'sample_due' transition for the Analysis Request
    passed in is performed. Tries to perform the same transition to the Sample
    associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'sample_due')


def after_receive(analysis_request):
    """
    Functio triggered after a 'receive' transition for the Analysis Request
    passed in is performed.
    Stores the value for "Date Received" field and also tries to perform the
    same transition to the Sample the Analysis Request passed in belongs to.
    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: IAnalysisRequest
    """
    # In most cases, the date of a given transition can be retrieved from an
    # object by using a getter that delegates the action to getTransitionDate,
    # without the need of storing the value manually.
    # This is a different case: a DateTimeField/Widget field is explicitly
    # declared in AR's schema because in some cases, the user may want to
    # change the Received Date by him/herself. For this reason, we set the
    # value manually here.
    analysis_request.setDateReceived(DateTime())
    analysis_request.reindexObject(idxs=["getDateReceived", ])

    sample = analysis_request.getSample()
    if sample:
        doActionFor(sample, 'receive')


def after_reject(analysis_request):
    """Method triggered after a 'reject' transition for the Analysis Request
    passed in is performed.

    Transitions and sets the rejection reasons to the parent Sample. Also
    transitions the analyses assigned to the AR

    bika.lims.workflow.AfterTransitionEventHandler
    :param obj: Analysis Request affected by the transition
    :type obj: AnalysisRequest
    """
    sample = analysis_request.getSample()
    if not sample:
        return

    if getCurrentState(sample) != 'rejected':
        doActionFor(sample, 'reject')
        reasons = analysis_request.getRejectionReasons()
        sample.setRejectionReasons(reasons)

    # Deactivate all analyses from this Analysis Request
    ans = analysis_request.getAnalyses(full_objects=True)
    for analysis in ans:
        doActionFor(analysis, 'reject')

    if analysis_request.bika_setup.getNotifyOnRejection():
        # Import here to brake circular importing somewhere
        from bika.lims.utils.analysisrequest import notify_rejection
        # Notify the Client about the Rejection.
        from bika.lims.utils.analysisrequest import notify_rejection
        notify_rejection(analysis_request)


def after_dispose(analysis_request):
    """Method triggered after a 'dispose' transition for the Analysis Request
    passed in is performed. Tries to perform the same transition to the Sample
    associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'dispose')


def after_expire(analysis_request):
    """Method triggered after a 'expire' transition for the Analysis Request
    passed in is performed. Tries to perform the same transition to the Sample
    associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'expire')


def after_sample_prep(analysis_request):
    """Method triggered after a 'sample_prep' transition for the Analysis
    Request passed in is performed. Tries to perform the same transition to the
    Sample associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'sample_prep')


def after_sample_prep_complete(analysis_request):
    """Method triggered after a 'sample_prep' transition for the Analysis
    Request passed in is performed. Tries to perform the same transition to the
    Sample associated to the analysis request passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: AnalysisRequest
    """
    _promote_transition(analysis_request, 'sample_prep_complete')


def after_attach(obj):
    """Method triggered after an 'attach' transition for the Analysis Request
    passed in is performed.
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    :param obj: Analysis Request affected by the transition
    :type obj: AnalysisRequest
    """
    # Don't cascade. Shouldn't be attaching ARs for now (if ever).
    pass


def after_verify(obj):
    """Method triggered after a 'verify' transition for the Analysis Request
    passed in is performed. Responsible of triggering cascade actions to
    associated analyses.
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    :param obj: Analysis Request affected by the transition
    :type obj: AnalysisRequest
    """
    pass


def after_publish(obj):
    """Method triggered after an 'publish' transition for the Analysis Request
    passed in is performed. Performs the 'publish' transition to children.
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    :param obj: Analysis Request affected by the transition
    :type obj: AnalysisRequest
    """
    # Transition the children
    ans = obj.getAnalyses(full_objects=True)
    for analysis in ans:
        doActionFor(analysis, 'publish')


def after_reinstate(obj):
    """Method triggered after a 'reinstate' transition for the Analysis Request
    passed in is performed. Activates all analyses contained in the object.
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    :param obj: Analysis Request affected by the transition
    :type obj: AnalysisRequest
    """
    ans = obj.getAnalyses(full_objects=True, cancellation_state='cancelled')
    for analysis in ans:
        doActionFor(analysis, 'reinstate')


def after_cancel(analysis_request):
    """
    Function triggered after a 'cancel' transition for the Analysis Request
    passed in is performed. Deactivates all analyses that contains. If the
    Anaysis Request passed in is the only that hasn't been yet within a Sample,
    then, triggers te `cancel` transition to the parent Sample.
    :param analysis_request: Analysis Request affected by the transition
    :type analysis_request: IAnalysisRequest
    """
    ans = analysis_request.getAnalyses(cancellation_state='active')
    for analysis in ans:
        doActionFor(analysis, 'cancel')

    # If this Analysis Request is the only Analysis Request from the Sample
    # that hasn't been yet cancelled, then promote the `cancel` transition to
    # the Sample
    sample = analysis_request.getSample()
    if not sample:
        return

    for ar in sample.getAnalysisRequests():
        if api.get_uid(ar) == api.get_uid(analysis_request):
            # Same Analysis Request as the one we are evaluating. Dismiss.
            continue
        if not getCurrentState(ar, 'cancelled'):
            # At least there is one AR that belongs to the same Sample that
            # hasn't been cancelled yet.
            return

    # Promote to Sample
    doActionFor(sample, 'cancel')


def after_retract(obj):
    """Method triggered afeter a 'retract' transition for the Analysis Request
    passed in is performed. Retracting an Analysis Request has no effect to the
    analyses it contains, neither to the Sample that belongs to.
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    :param obj: Analysis Request affected by the transition
    :type obj: Analysis Request
    """
    pass
