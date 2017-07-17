# coding=utf-8
from DateTime import DateTime
from bika.lims.workflow import doActionFor
from bika.lims.workflow import isTransitionAllowed


def _cascade_promote_transition(partition, transition_id):
    """ Performs the transition for the transition_id passed in to the
    children, parent and siblings of the partition passed in.

    Tries to fire the transition_id passed in for all the analyses associated
    to the partition. The function tries to fire the same transition to the
    parent Sample.

    Note the function tries to perform the transitions to children and parent,
    but those transitions will only take place if the corresponding guards and
    loops.
    permissions allow to do it. This mechanism prevents infinite recursive

    :param partition: Sample Partition for which the transition has to be
                      cascaded or promoted.
    :param transition_id: Unique id of the transition
    :type partition: SamplePartition
    :type transition_id: str
    """
    for analysis in partition.getAnalyses():
        doActionFor(analysis, transition_id)

    # Promote Sample. Sample transition will, in turn, transition the Analysis
    # Requests.
    sample = partition.getSample()
    doActionFor(sample, transition_id)


def after_no_sampling_workflow(partition):
    """Method triggered after a 'no_sampling_workflow' transition for the
    Sample Partition passed in is performed.

    Tries to perform the same transition to all the analyses and parent sample
    associated to the partition passed in.

    Once done, does the following:

    a) If parent Sample has the sampling workflow enabled and the partition has
       a preservation set:
       The function tries to perform the "to_be_preserved" transition to the
       Sample Partition itself.

    b) If parent Sample has the sampling workflow disabled
       The function tries to perform the "sample_due" transition to the Sample
       Partition itself.

    Note that in both cases (a or b), the transition ultimately performed to
    the Sample Partition will be triggered to children (analyses) and escalated
    to parents (Sample and Analysis Requests).

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'no_sampling_workflow')

    if isTransitionAllowed(partition, 'to_be_preserved'):
        # The partition requires to be preserved
        doActionFor(partition, 'to_be_preserved')
        return

    # Automatic transition to sample due
    doActionFor(partition, 'sample_due')


def after_sampling_workflow(partition):
    """Method triggered after a 'sampling_workflow' transition for the
    Sample Partition passed in is performed.

    Tries to perform the same transition to all the analyses and parent sample
    associated to the partition passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'sampling_workflow')


def after_to_be_preserved(partition):
    """Method triggered after a 'to_be_preserved' transition for the
    Sample Partition passed in is performed.

    Tries to perform the same transition to all the analyses and parent sample
    associated to the partition passed in.

    If the container used for this partition already comes pre-preserved (so
    there is no additional action to be made by the sample collector, then
    fires the 'preserve' transition automatically.

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'to_be_preserved')

    # If the container used for this partition already comes pre-preserved (so
    # there is no additional action to be made by the sample collector, then
    # fire the 'preserve' transition automatically
    container = partition.getContainer()
    if container and container.getPrePreserved():
        doActionFor(partition, 'preserve')


def after_preserve(partition):
    """Method triggered after a 'preserve' transition for the Sample Partition
    passed in is performed.

    Tries to perform the same transition to all the analyses and parent sample
    associated to the partition passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'preserve')


def after_schedule_sampling(partition):
    """Method triggered after a 'schedule_sampling' transition for the Sample
    Partition passed in is performed.

    Tries to perform the same transition to all the analyses and parent sample
    associated to the partition passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'schedule_sampling')


def after_sample(partition):
    """Method triggered after a 'sample' transition for the Sample Partition
    passed in is performed.

    Tries to perform 'sample' transition to all Analyses associated to the
    Sample Partition and the parent Sample as well. The assumption is that if
    all Sample Partitions of a Sample have been sampled, the Sample must be
    sampled too.

    Once done, does the following:

    a) If parent Sample has the sampling workflow enabled and the partition has
       a preservation set:
       The function tries to perform the "to_be_preserved" transition to the
       Sample Partition itself.

    b) If parent Sample has the sampling workflow disabled
       The function tries to perform the "sample_due" transition to the Sample
       Partition itself.

    Note that in both cases (a or b), the transition ultimately performed to
    the Sample Partition will be triggered to children (analyses) and escalated
    to parents (Sample and Analysis Requests).

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample Partition affected by the 'sample' transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'sample')

    if isTransitionAllowed(partition, 'to_be_preserved'):
        # The partition requires to be preserved
        doActionFor(partition, 'to_be_preserved')
        return

    # Automatic transition to sample due
    doActionFor(partition, 'sample_due')


def after_sample_due(partition):
    """Method triggered after a 'sample_due' transition for the Sample
    Partition passed in is performed.

    Tries to perform the same transition to all the analyses and parent sample
    associated to the partition passed in. The assumption is that if all
    Sample Partitions of a Sample are pending of reception, the Sample must be
    in a pending state too.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'sample_due')


def after_receive(partition):
    """Method triggered after a 'receive' transition for the Sample Partition
    passed in is performed.

    Tries to perform the same transition to all the analyses and parent sample
    associated to the partition passed in. It also stores the value for the
    "Date Received" field of the partition. The assumption is that if all
    Sample Partitions of a Sample have been received, the Sample must be
    received too.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    partition.setDateReceived(DateTime())
    partition.reindexObject(idxs=["getDateReceived", ])
    _cascade_promote_transition(partition, 'receive')


def after_reject(partition):
    """Method triggered after a 'reject' transition for the Sample Partition
    passed in is performed.

    Tries to perform the same transition to the parent sample the partition
    passed in belongs to. Note that in this case, analyses are not affected by
    this transition. The assumption is that if all Sample Partitions of a
    Sample have been rejected, the Sample must be rejected too.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """

    # Promote Sample. Sample transition will, in turn, transition the Analysis
    # Requests.
    sample = partition.getSample()
    doActionFor(sample, 'reject')


def after_dispose(partition):
    """Method triggered after a 'dispose' transition for the Sample Partition
    passed in is performed.

    Tries to perform the same transition to the parent sample the partition
    passed in belongs to. The assumption is that if all Sample Partitions of a
    Sample have been disposed, the Sample must be rejected too.
    Note that in this case, analyses are not affected by this transition.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """

    # Promote Sample. Sample transition will, in turn, transition the Analysis
    # Requests.
    sample = partition.getSample()
    doActionFor(sample, 'dispose')


def after_expire(partition):
    """Method triggered after a 'expire' transition for the Sample Partition
    passed in is performed.

    Tries to perform the same transition to the parent Sample. The assumption
    is that if all Sample Partitions of a Sample are expired, the Sample must
    be expired too. Note analyses are not affected by this transition.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    sample = partition.getSample()
    doActionFor(sample, 'expire')


def after_sample_prep(sample):
    """Method triggered after a 'sample_prep' transition for the Sample
    Partition passed in is performed.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample partition affected by the transition
    :type sample: SamplePartition
    """
    # TODO Workflow - SamplePartition after_sample_prep
    pass


def after_sample_prep_complete(sample):
    """Method triggered after a 'sample_prep_complete' transition for the
    Sample Partition passed in is performed.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample partition affected by the transition
    :type sample: SamplePartition
    """
    # TODO Workflow - SamplePartition after_sample_prep_complete
    pass


def after_cancel(partition):
    """Method triggered after a 'cancel' transition for the Sample Partition
    passed in is performed. Transition from bika_cancellation_workflow

    Tries to perform the same transition to the parent Sample. The assumption
    is that if all Sample Partitions of a Sample are cancelled, the Sample must
    be cancelled too, as well as the analyses assigned to this partition.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'cancel')


def after_reinstate(partition):
    """Method triggered after a 'reinstate' transition for the Sample Partition
    passed in is performed. Transition from bika_cancellation_workflow

    Tries to perform the same transition to all the analyses and parent sample
    associated to the partition passed in. The assumption is that if all
    Sample Partitions of a Sample are reinstated, the Sample must be reinstated
    too, as well as all the analyses assigned to this partition.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param partition: Sample partition affected by the transition
    :type partition: SamplePartition
    """
    _cascade_promote_transition(partition, 'reinstate')
