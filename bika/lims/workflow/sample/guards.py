# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.CORE
#
# Copyright 2018 by it's authors.
# Some rights reserved. See LICENSE.rst, CONTRIBUTORS.rst.

from Products.CMFCore.WorkflowCore import WorkflowException
from bika.lims import logger
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import getReviewHistoryActionsList
from bika.lims.workflow import isActive
from bika.lims.workflow import isEndState
from bika.lims.workflow import isTransitionAllowed
from bika.lims.workflow import getIncomingTransitionIds


def guard_no_sampling_workflow(sample):
    """Returns true if the 'no_sampling_workflow' transition can be performed
    to the sample passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed if all active associated partitions have
      either been transitioned or can transition.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns True or False
    """
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='no_sampling_workflow',
                                   dependencies=partitions,
                                   check_all=True,
                                   check_history=True,
                                   check_action=False)


def guard_sampling_workflow(sample):
    """Returns true if the 'sampling_workflow' transition can be performed to
    the sample passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed if all active associated partitions have
      either been transitioned or can transition.

    Note this function does not check if the Sampling workflow has been enabled
    in Bika Setup. This check is delegated to partitions corresponding guards.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='sampling_workflow',
                                   dependencies=partitions,
                                   check_all=True,
                                   check_history=True,
                                   check_action=False)


def guard_to_be_preserved(sample):
    """Returns true if the 'to_be_preserved' transition can be performed to the
    sample passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - At least there is one active Sample Partition that needs to be preserved
      or has already been transitioned to a 'to_be_preserved' state

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
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='to_be_preserved',
                                   dependencies=partitions,
                                   target_statuses=['to_be_preserved'],
                                   check_action=False)


def guard_preserve(sample):
    """Returns true if the 'preserve' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed if all active sample partitions have
      either reached the state 'sample_due' or there's only one sample
      partition that still requires preservation (this transition can be
      performed to the partition).

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    # TODO Workflow - Preserve should only be available for Partitions. Once
    # all partitions are transitioned, then transition the Sample, but not the
    # other way round
    partitions = sample.getSamplePartitions()
    for partition in partitions:
        if not isActive(partition):
            # If the partition is not active, assume is ok
            continue

        if isTransitionAllowed(partition, 'preserve'):
            continue

        # The only possible path for a partition to be in a sample_due state
        # is because of 'preserve' or 'sample_due' transitions.
        if getCurrentState(partition) != 'sample_due':
            possible_trans = getIncomingTransitionIds(sample, 'sample_due')
            transitions = getReviewHistoryActionsList(partition)
            trans = [trans for trans in transitions if trans in possible_trans]
            if len(trans) == 0:
                # The partition hasn't been transitioned to sample_due yet
                return False

    return True


def guard_schedule_sampling(sample):
    """Returns true if the 'schedule_sampling' transition can be performed to
    the sample passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed if all active associated partitions have
      either been transitioned or can transition.

    Note this function does not check if the Sampling workflow has been enabled
    in Bika Setup. This check is delegated to partitions corresponding guards

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='schedule_sampling',
                                   dependencies=partitions,
                                   check_history=True,
                                   check_all=True,
                                   check_action=False)


def guard_sample(sample):
    """Returns true if the 'sample' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed if all active associated partitions have
      either been transitioned or can transition.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='sample',
                                   dependencies=partitions,
                                   check_all=True,
                                   check_history=True,
                                   check_action=False)


def guard_sample_due(sample):
    """Returns true if the 'sample_due' transition can be performed to the
    sample passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed if all active associated partitions have
      either been transitioned or can transition.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='sample_due',
                                   dependencies=partitions,
                                   check_all=True,
                                   check_history=True,
                                   check_action=False)


def guard_receive(sample):
    """Returns true if the 'receive' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled status)

    :param sample: Sample object the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    return isActive(sample)


def guard_reject(sample):
    """Returns true if the 'reject' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - Rejection workflow is enabled in Setup

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    if not isActive(sample):
        return False

    return sample.bika_setup.isRejectionWorkflowEnabled()


def guard_expire(sample):
    """Returns true if the 'no_sampling_workflow' transition can be performed
    to the sample passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed if all active associated partitions have
      either been transitioned or can transition.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns True or False
    """
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='expire',
                                   dependencies=partitions,
                                   target_statuses=['expired'],
                                   check_all=True,
                                   check_action=False)


def guard_dispose(sample):
    """Returns true if the 'dispose' transition can be performed to the sample
    passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - The transition can be performed if all active associated partitions have
      either been transitioned or can transition.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='dispose',
                                   dependencies=partitions,
                                   target_statuses=['disposed'],
                                   check_all=True,
                                   check_action=False)


def guard_sample_prep(sample):
    """Returns true if the 'sample_prep' transition can be performed to the
    sample passed in.

    Returns True if the following conditions are met:
    - The Sample is active (neither inactive nor cancelled state)
    - At least there is one active Sample Partition that requires preparation
      or has already been transitioned to a 'sample_prep' state

    Note this function does not check if the sample has a preparation workflow
    set. This check is delegated to guard from partitions.

    :param sample: the Sample the transition has to be evaluated against.
    :type sample: Sample
    :returns: True or False
    :rtype: bool
    """
    partitions = sample.getSamplePartitions()
    if partitions:
        return isTransitionAllowed(instance=sample,
                                   transition_id='sample_prep',
                                   dependencies=partitions,
                                   target_statuses=['sample_prep'],
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
