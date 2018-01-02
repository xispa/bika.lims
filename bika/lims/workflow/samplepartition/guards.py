# coding=utf-8
from bika.lims.workflow import isBasicTransitionAllowed, wasTransitionPerformed, \
    isActive, getCurrentState


def guard_no_sampling_workflow(partition):
    """Returns true if the 'no_sampling_workflow' transition can be performed
    to the sample partition passed in.

    Returns True if the Sample partition is active (its state is neither
    inactive nor cancelled)

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(partition)


def guard_sampling_workflow(partition):
    """Returns true if the 'sampling_workflow' transition can be performed to
    the sample partition passed in.

    Returns True if the following conditions are met:
    - The Sample Partition is active (neither inactive nor cancelled state)
    - Sampling Workflow is enabled in bika_setup

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    if not partition.bika_setup.getSamplingWorkflowEnabled():
        return False

    return isBasicTransitionAllowed(partition)


def guard_to_be_preserved(partition):
    """Returns true if the 'to_be_preserved' transition can be performed to the
    sample partition passed in.

    Returns True if the following conditions are met:
    - The Sample Partition is active (neither inactive nor cancelled state)
    - The Sample Partition has assigned a Preservation that uses a Container
      that doesn't come pre-preserved already.
    - Sampling Workflow is enabled in bika_setup

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    if not partition.getPreservation():
        return False

    # If the container used for this partition already comes pre-preserved (so
    # there is no additional action to be made by the sample collector, assume
    # that is already in a preserved state, so return False
    container = partition.getContainer()
    if container and container.getPrePreserved():
        return False

    if not partition.bika_setup.getSamplingWorkflowEnabled():
        return False

    return isBasicTransitionAllowed(partition)


def guard_preserve(partition):
    """Returns true if the 'preserve' transition can be performed to the sample
    partition passed in.

    Returns True if the state of the Sample Partition is active (neither
    inactive nor cancelled state).

    Note that if the sample partition reached a state ('to_be_preserved') from
    which this transition can be performed, there is no need then if sampling
    workflow is enabled, cause may happen the sample partition was transitioned
    to the current state previously, when the sampling workflow was indeed,
    enabled. If sampling workflow was checked here, there is the risk to end up
    with a sample partition in a stale status, with no available transition
    other than cancel.

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(partition)


def guard_schedule_sampling(partition):
    """Returns true if the 'schedule_sampling' transition can be performed to
    the sample partition passed in.

    Returns True if the following conditions are met:
    - The Sample partition is active (neither inactive nor cancelled state)
    - The Sample associated to the partition has values set for SamplingDate
      and ScheduledSamplingSampler values
    - Schedule Sampling workflow is enabled in bika_setup

    Note that if the sample partition reached a state ('to_be_sampled') from
    which this transition can be performed, there is no need then if sampling
    workflow is enabled, cause may happen the sample partition was transitioned
    to the current state previously, when the sampling workflow was indeed,
    enabled. If sampling workflow was checked here, there is the risk to end up
    with a sample partition in a stale status, with no available transition
    other than cancel.

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    if not partition.bika_setup.getScheduleSamplingEnabled():
        return False

    sample = partition.getSample()
    if not sample:
        return False

    sampler = sample.getScheduledSamplingSampler()
    sampling_date = sample.getSamplingDate()
    if sampler and sampling_date:
        return isBasicTransitionAllowed(partition)

    return False


def guard_sample(partition):
    """Returns true if the 'sample' transition can be performed to the sample
    partition passed in.

    Returns True if the following conditions are met:
    - The Sample Partition is active (neither inactive nor cancelled state)
    - The associated Sample has values set for DateSampled and Sampler

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    sample = partition.getSample()
    if sample:
        date_sampled = sample.getDateSampled()
        sampler = sample.getSampler()
        if date_sampled and sampler:
            return isBasicTransitionAllowed(partition)


def guard_sample_due(partition):
    """Returns true if the 'sample_due' transition can be performed to the
    sample partition passed in.

    Returns True if the state of the Sample Partition is active (neither
    inactive nor cancelled state).

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(partition)


def guard_receive(partition):
    """
    Returns True if the transition 'receive' can be performed to the Sample
    Partition passed in.
    Returns true if the state of the Sample Partition passed in is active and
    the Sample that belongs to has already been received.
    :param partition: Partition the transition has to be evaluated against
    :type partition: SamplePartition
    :return: True if the Sample Partition passed in can be received
    :rtype: bool
    """
    if not isBasicTransitionAllowed(partition):
        return False

    sample = partition.getSample()
    return wasTransitionPerformed(sample, 'receive')


def guard_reject(partition):
    """Returns true if the 'reject' transition can be performed to the
    sample partition passed in.

    Returns True if the following conditions are met:
    - The Sample partition is active (neither inactive nor cancelled state)
    - The Sample the Partition belongs to has been rejected

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    if not isActive(partition):
        return False

    sample = partition.getSample()
    return getCurrentState(sample) == 'rejected'


def guard_dispose(partition):
    """Returns true if the 'dispose' transition can be performed to the
    sample partition passed in.

    Returns True if the state of the Sample Partition is active (neither
    inactive nor cancelled state).

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(partition)


def guard_expire(partition):
    """Returns true if the 'dispose' transition can be performed to the
    sample partition passed in.

    Returns True if the state of the Sample Partition is active (neither
    inactive nor cancelled state).

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    return isBasicTransitionAllowed(partition)


def guard_sample_prep(partition):
    """Returns true if the 'sample_prep' transition can be performed to the
    sample partition passed in.

    Returns True if the following conditions are met:
    - The Sample Partition is active (neither inactive nor cancelled state)
    - The Sample associated to the Partition has a PreparationWorkflow assigned

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    sample = partition.getSample()
    if sample.getPreparationWorkflow():
        return isBasicTransitionAllowed(partition)

    return False


def guard_sample_prep_complete(partition):
    """Returns true if the 'sample_prep_complete' transition can be performed
    to the sample partition passed in.

    Returns True if the state of the Sample Partition is active (neither
    inactive nor cancelled state).

    :param partition: Partition the transition has to be evaluated against.
    :type partition: SamplePartition
    :returns: True or False
    :rtype: bool
    """
    # TODO Workflow - SamplePartition.guard_sample_prep_complete
    return isBasicTransitionAllowed(partition)
