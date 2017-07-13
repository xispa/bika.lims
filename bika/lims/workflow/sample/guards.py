from Products.CMFCore.utils import getToolByName
from bika.lims import logger
from bika.lims.workflow import isBasicTransitionAllowed


def guard_sampling_workflow(sample):
    """Returns true if the 'sampling_workflow' transition can be performed to
    the sample passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - Sampling Workflow is enabled in bika_setup

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    if not sample.bika_setup.getSamplingWorkflowEnabled():
        return False

    return isBasicTransitionAllowed(sample)


def guard_to_be_preserved(sample):
    """Returns true if the 'to_be_preserved' transition can be performed to the
    sample passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - Sampling Workflow is enabled in bika_setup
    - At least there is one Sample Partition that needs to be preserved

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    if not sample.bika_setup.getSamplingWorkflowEnabled():
        return False

    if not isBasicTransitionAllowed(sample):
        return False

    for partition in sample.getSamplePartitions():
        if partition.getPreservation():
            return True

    return False


def guard_preserve(sample):
    """Returns true if the 'preserver' transition can be performed to the
    sample passed in.

    Returns True if the user has enough privileges to fire the transition and
    the Sample is active (neither inactive nor cancelled state)

    :param sample: the Sample the transition has to be valuated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(sample)


def guard_schedule_sampling(sample):
    """Returns true if the 'schedule_sampling' transition can be performed to
    the sample passed in.

    Returns True if the user has enough privileges to fire the transition and
    the Sample is active (neither inactive nor cancelled state).

    Note that if the sample reached a state from which this transition can be
    performed, there is no need to check if sampling workflow is enabled, cause
    may happen the sampling workflow was enabled before the Sample creation
    (and the sample was transitioned accordingly), but disabled afterwards. If
    we force the sampling workflow to be enabled here, in that case we'd end up
    with a stale sample, with no transition allowed other than cancel.

    :param sample: the Sample the transition has to be valuated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(sample)


def guard_sample(sample):
    """Returns true if the 'sample' transition can be performed to the sample
    passed in.

    Returns True if the user has enough privileges to fire the transition and
    the Sample is active (neither inactive nor cancelled state)

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(sample)


def guard_sample_due(sample):
    """Returns true if the 'sample_due' transition can be performed to the
    sample passed in.

    Returns True if the user has enough privileges to fire the transition and
    the Sample is active (neither inactive nor cancelled state)

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(sample)


def guard_receive(sample):
    """Returns true if the 'receive' transition can be performed to the sample
    passed in.

    Returns True if the user has enough privileges to fire the transition and
    the Sample is active (neither inactive nor cancelled state)

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(sample)


def guard_reject(sample):
    """Returns true if the 'reject' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - Rejection Workflow is enabled in bika_setup

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    if not sample.bika_setup.getRejectionWorkflowEnabled():
        return False

    return isBasicTransitionAllowed(sample)


def guard_dispose(sample):
    """Returns true if the 'dispose' transition can be performed to the sample
    passed in.

    Returns True if the user has enough privileges to fire the transition and
    the Sample is active (neither inactive nor cancelled state)

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(sample)


def guard_sample_prep(sample):
    """Returns true if the 'sample_prep' transition can be performed to the
    sample passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - Rejection Workflow is enabled in bika_setup
    - A Preparation Workflow is set for the sample passed in

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    if not sample.getPreparationWorkflow():
        return False

    return isBasicTransitionAllowed(sample)


def guard_sample_prep_complete(obj):
    """ This relies on user created workflow.  This function must
    defend against user errors.

    AR and Analysis guards refer to this one.

    - If error is encountered, do not permit object to proceed.  Break
      this rule carelessly and you may see recursive automatic workflows.

    - If sampleprep workflow is badly configured, primary review_state
      can get stuck in "sample_prep" forever.

    """
    # TODO Workflow - Sample.guard_sample_prep_complete
    wftool = getToolByName(obj, 'portal_workflow')
    try:
        # get sampleprep workflow object.
        sp_wf_name = obj.getPreparationWorkflow()
        sp_wf = wftool.getWorkflowById(sp_wf_name)
        # get sampleprep_review state.
        sp_review_state = wftool.getInfoFor(obj, 'sampleprep_review_state')
        assert sp_review_state
    except WorkflowException as e:
        logger.warn("guard_sample_prep_complete_transition: "
                    "WorkflowException %s" % e)
        return False
    except AssertionError:
        logger.warn("'%s': cannot get 'sampleprep_review_state'" %
                    sampleprep_wf_name)
        return False

    # get state from workflow - error = allow transition
    # get possible exit transitions for state: error = allow transition
    transitions = sp_wf
    if len(transitions) > 0:
        return False
    return True
