# coding=utf-8
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import isActive
from bika.lims.workflow import isBasicTransitionAllowed
from bika.lims.workflow import isTransitionAllowed
from bika.lims.workflow import wasTransitionPerformed


def guard_no_sampling_workflow(analysis_request):
    """Returns true if the 'no_sampling_workflow' transition can be performed
    to the analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='no_sampling_workflow',
                                   dependencies=[sample],
                                   target_statuses=['sampled'],
                                   check_history=True,
                                   check_action=False)


def guard_sampling_workflow(analysis_request):
    """Returns true if the 'sampling_workflow' transition can be performed to
    the analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='sampling_workflow',
                                   dependencies=[sample],
                                   target_statuses=['to_be_sampled'],
                                   check_history=True,
                                   check_action=False)


def guard_to_be_preserved(analysis_request):
    """Returns true if the 'to_be_preserved' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='to_be_preserved',
                                   dependencies=[sample],
                                   target_statuses=['to_be_preserved'],
                                   check_action=False)


def guard_preserve(analysis_request):
    """Returns true if the 'preserve' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='preserve',
                                   dependencies=[sample],
                                   target_statuses=['sample_due'],
                                   check_action=False)


def guard_schedule_sampling(analysis_request):
    """Returns true if the 'schedule_sampling' transition can be performed to
    the analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='schedule_sampling',
                                   dependencies=[sample],
                                   target_statuses=['scheduled_sampling'],
                                   check_action=False)


def guard_sample(analysis_request):
    """Returns true if the 'sample' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='sample',
                                   dependencies=[sample],
                                   target_statuses=['sampled'],
                                   check_history=True,
                                   check_action=False)


def guard_sample_due(analysis_request):
    """Returns true if the 'sample_due' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='sample_due',
                                   dependencies=[sample],
                                   target_statuses=['sample_due'],
                                   check_history=True,
                                   check_action=False)


def guard_receive(analysis_request):
    """Returns true if the 'receive' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='receive',
                                   dependencies=[sample],
                                   target_statuses=['sample_received'],
                                   check_history=True,
                                   check_action=False)


def guard_reject(analysis_request):
    """Returns true if the 'reject' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='reject',
                                   dependencies=[sample],
                                   target_statuses=['rejected'],
                                   check_action=False)


def guard_expire(analysis_request):
    """Returns true if the 'expire'' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='expire',
                                   dependencies=[sample],
                                   target_statuses=['expired'],
                                   check_action=False)


def guard_dispose(analysis_request):
    """Returns true if the 'reject' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='dispose',
                                   dependencies=[sample],
                                   target_statuses=['disposed'],
                                   check_action=False)


def guard_sample_prep(analysis_request):
    """Returns true if the 'sample_prep' transition can be performed to the
    analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='sample_prep',
                                   dependencies=[sample],
                                   target_statuses=['sample_prep'],
                                   check_action=False)


def guard_sample_prep_complete(analysis_request):
    """Returns true if the 'sample_prep_complete' transition can be performed
    to the analysis request passed in.

    Returns True if the transition can be performed to the Sample associated to
    the analysis request passed in or the Sample has already been transitioned.

    :param analysis_request: Request the transition has to be evaluated against
    :type analysis_request: AnalysisRequest
    :returns: True or False
    :rtype: bool
    """
    sample = analysis_request.getSample()
    if sample:
        return isTransitionAllowed(instance=analysis_request,
                                   transition_id='sample_prep_complete',
                                   dependencies=[sample],
                                   check_history=True,
                                   check_action=False)


def guard_assign(obj):
    """Allow or disallow transition depending on our children's states
    """
    # TODO Workflow Assign AR - To revisit. Is there any reason why we want an
    # AR to be in an 'assigned' state?. If no, remove the transition from the
    # workflow definition, as well as from here and from content.analysisrequest
    return False


def guard_unassign(obj):
    """Allow or disallow transition depending on our children's states
    """
    # TODO Workflow UnAssign AR - To revisit. Is there any reason why we want an
    # AR to be in an 'assigned' state?. If no, remove the transition from the
    # workflow definition, as well as from here and from content.analysisrequest
    return False


def guard_verify(obj):
    """Returns True if 'verify' transition can be applied to the Analysis
    Request passed in. This is, returns true if all the analyses that contains
    have already been verified. Those analyses that are in an inactive state
    (cancelled, inactive) are dismissed, but at least one analysis must be in
    an active state (and verified), otherwise always return False. If the
    Analysis Request is in inactive state (cancelled/inactive), returns False
    Note this guard depends entirely on the current status of the children
    :returns: true or false
    """
    if not isBasicTransitionAllowed(obj):
        return False

    analyses = obj.getAnalyses(full_objects=True)
    invalid = 0
    for an in analyses:
        # The analysis has already been verified?
        if wasTransitionPerformed(an, 'verify'):
            continue

        # Maybe the analysis is in an 'inactive' state?
        if not isActive(an):
            invalid += 1
            continue

        # Maybe the analysis has been rejected or retracted?
        dettached = ['rejected', 'retracted', 'attachments_due']
        status = getCurrentState(an)
        if status in dettached:
            invalid += 1
            continue

        # At this point we can assume this analysis is an a valid state and
        # could potentially be verified, but the Analysis Request can only be
        # verified if all the analyses have been transitioned to verified
        return False

    # Be sure that at least there is one analysis in an active state, it
    # doesn't make sense to verify an Analysis Request if all the analyses that
    # contains are rejected or cancelled!
    return len(analyses) - invalid > 0


def guard_prepublish(obj):
    """Returns True if 'prepublish' transition can be applied to the Analysis
    Request passed in.
    Returns true if the Analysis Request is active (not in a cancelled/inactive
    state), the 'publish' transition cannot be performed yet, and at least one
    of its analysis is under to_be_verified state or has been already verified.
    As per default DC workflow definition in bika_ar_workflow, note that
    prepublish does not transitions the Analysis Request to any other state
    different from the actual one, neither its children. This 'fake' transition
    is only used for the prepublish action to be displayed when the Analysis
    Request' status is other than verified, so the labman can generate a
    provisional report, also if results are not yet definitive.
    :returns: true or false
    """
    if not isBasicTransitionAllowed(obj):
        return False

    if isTransitionAllowed(obj, 'publish'):
        return False

    analyses = obj.getAnalyses(full_objects=True)
    for an in analyses:
        # If the analysis is not active, omit
        if not isActive(an):
            continue

        # Check if the current state is 'verified'
        status = getCurrentState(an)
        if status in ['verified', 'to_be_verified']:
            return True

    # This analysis request has no single result ready to be verified or
    # verified yet. In this situation, it doesn't make sense to publish a
    # provisional results reports without a single result to display
    return False


def guard_publish(obj):
    """Returns True if 'publish' transition can be applied to the Analysis
    Request passed in. Returns true if the Analysis Request is active (not in
    a cancelled/inactive state). As long as 'publish' transition, in accordance
    with its DC workflow can only be performed if its previous state is
    verified or published, there is no need of additional validations.
    :returns: true or false
    """
    return isBasicTransitionAllowed(obj)
