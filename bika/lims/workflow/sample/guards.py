# coding=utf-8
from bika.lims import logger
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import isEndState
from bika.lims.workflow import isTransitionAllowed


def guard_sampling_workflow(sample):
    """Returns true if the 'sampling_workflow' transition can be performed to
    the sample passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to at least one of the partitions from
      the sample passed in or at least one of the partitions' state is the
      'to_be_sampled' state already.

    Note this function does not check if the Sampling workflow has been enabled
    in Bika Setup. This check is delegated to partitions corresponding guards

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='sampling_workflow',
                               dependencies=sample.getSamplePartitions(),
                               target_statuses=['to_be_sampled'],
                               check_action=False)


def guard_to_be_preserved(sample):
    """Returns true if the 'to_be_preserved' transition can be performed to the
    sample passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - At least there is one Sample Partition that needs to be preserved or has
      already be transitioned to a to_be_preserved state

    Note this function does not check if the Sampling Workflow has been enabled
    in Bika Setup on purpose, cause may happen the Sample was created when the
    workflow was enabled and now is not. So, in fact, a Sample can only be
    transitioned to to_be_preserved state only if has at least one Partition
    that requires to be preserved. The guard for this transition in Sample
    Partition will deal with either the Sampling Workflow is enabled or not.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='to_be_preserved',
                               dependencies=sample.getSamplePartitions(),
                               target_statuses=['to_be_preserved'],
                               check_action=False)


def guard_preserve(sample):
    """Returns true if the 'preserve' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to at least one of the partitions from
      the sample passed in or at least one of the partitions' state is the
      'sample_due' state already.

    Note this function does not check if the Sampling workflow has been enabled
    in Bika Setup. This check is delegated to partitions corresponding guards

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='preserve',
                               dependencies=sample.getSamplePartitions(),
                               target_statuses=['sample_due'],
                               check_action=False)


def guard_schedule_sampling(sample):
    """Returns true if the 'schedule_sampling' transition can be performed to
    the sample passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to at least one of the partitions from
      the sample passed in or at least one of the partitions' state is the
      'scheduled_sampling' state already.

    Note this function does not check if the Sampling workflow has been enabled
    in Bika Setup. This check is delegated to partitions corresponding guards

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='schedule_sampling',
                               dependencies=sample.getSamplePartitions(),
                               target_statuses=['scheduled_sampling'],
                               check_action=False)


def guard_sample(sample):
    """Returns true if the 'sample' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to at least one of the partitions from
      the sample passed in or the transition was performed at least for one of
      the partitions.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='sample',
                               dependencies=sample.getSamplePartitions(),
                               check_history=True,
                               check_action=False)


def guard_sample_due(sample):
    """Returns true if the 'sample_due' transition can be performed to the
    sample passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to all active partitions associated to
      the sample passed in or the transition has been performed already.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='sample_due',
                               dependencies=sample.getSamplePartitions(),
                               check_all=True,
                               check_history=True,
                               check_action=False)


def guard_receive(sample):
    """Returns true if the 'receive' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to all active partitions associated to
      the sample passed in or the transition has been performed already.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='receive',
                               dependencies=sample.getSamplePartitions(),
                               check_all=True,
                               check_history=True,
                               check_action=False)


def guard_reject(sample):
    """Returns true if the 'reject' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to all partitions from the sample passed
      in or their state is already 'rejected'

    Note this function does not check if the Rejection workflow is enabled in
    Bika Setup. This check is delegated to guard from partitions.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='reject',
                               dependencies=sample.getSamplePartitions(),
                               target_statuses=['rejected'],
                               check_all=True,
                               check_action=False)


def guard_dispose(sample):
    """Returns true if the 'dispose' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to all active partitions from the sample
      passed in or their state is already 'disposed'

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='dispose',
                               dependencies=sample.getSamplePartitions(),
                               target_statuses=['disposed'],
                               check_all=True,
                               check_action=False)


def guard_sample_prep(sample):
    """Returns true if the 'sample_prep' transition can be performed to the
    sample passed in.

    Returns True if the following conditions are met:
    - The user has enough privileges to fire the transition
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed to all active partitions from the
      sample passed in or their state is already 'rejected'

    Note this function does not check if the sample has a preparation workflow
    set. This check is delegated to guard from partitions.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isTransitionAllowed(instance=sample,
                               transition_id='sample_prep',
                               dependencies=sample.getSamplePartitions(),
                               target_statuses=['sample_prep'],
                               check_all=True,
                               check_action=False)


def guard_sample_prep_complete(sample):
    """Returns true if the 'sample_prep_complete' transition can be performed
    to the sample passed in. This relies on user created workflow.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The Sample doesn't have a PreparationWorkflow assigned or if does, the
      Sample does not have state associated or is a dead-end state.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    state_var = 'sampleprep_review_state'
    prep_workflow_id = sample.getPreparationWorkflow(sample)
    if not prep_workflow_id:
        # This should never happen, but return True to prevent a stale status
        msg = "No preparation workflow set for sample {0}, although its " + \
              "current state is {1}: Allowing sample_prep_complete transition"
        state = getCurrentState(sample)
        logger.warning(msg.format(sample.getId(), state))
        return True

    state = getCurrentState(sample, state_var)
    if not state:
        # This should never happen, but return True to prevent a stale status
        msg = "No {0} value found for sample {1}, although its current " + \
              "is {1}: Allowing sample_prep_complete transition"
        state = getCurrentState(sample)
        logger.warning(msg.format(state_var, sample.getId(), state))
        return True

    # If the current state for sampleprep_review_state is the last possible
    # from the preparation workflow, return True. Otherwise, assume the
    # preparation workflow has not finished yet and return False
    return isEndState(sample, prep_workflow_id)
