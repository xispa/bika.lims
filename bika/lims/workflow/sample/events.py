# coding=utf-8
from DateTime import DateTime
from bika.lims.workflow import doActionFor


def _cascade_transition(sample, transition_id):
    """ Performs the transition for the transition_id passed in to children.

    Tries to fire the transition_id passed in for all Sample Partitions that
    belong to the sample passed in. Once done, tries to apply the same
    transition to all Analysis Requests associated to the sample passed in.

    Note the function tries to apply the transitions to children, but will
    only take place if the corresponding guards allows it. This mechanism
    prevents infinite recursive problems.

    :param sample: Sample for which the transition has to be cascaded
    :param transition_id: Unique id of the transition
    :type sample: Sample
    :type transition_id: str
    """

    # Transition all Sample Partitions associated to the current Sample.
    # Note the transition for SamplePartition will already take care of
    # eventual cascading transitions to analyses, so there is no need to
    # consider analyses here.
    for part in sample.getSamplePartitions():
        doActionFor(part, transition_id)

    # Transition all Analysis Requests that are associated to this Sample.
    for ar in sample.getAnalysisRequests():
        doActionFor(ar, transition_id)


def after_no_sampling_workflow(sample):
    """Method triggered after a 'no_sampling_workflow' transition for the
    Sample passed in is performed.

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'no_sampling_workflow')


def after_sampling_workflow(sample):
    """Method triggered after a 'sampling_workflow' transition for the Sample
    passed in is performed.

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'sampling_workflow')


def after_to_be_preserved(sample):
    """Method triggered after a 'to_be_preserved' transition for the Sample
    passed in is performed.

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'to_be_preserved')


def after_preserve(sample):
    """Method triggered after a 'preserve' transition for the Sample passed
    in is performed.

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'preserve')


def after_schedule_sampling(sample):
    """Method triggered after a 'schedule_sampling' transition for the Sample
    passed in is performed.

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'schedule_sampling')


def after_sample(sample):
    """Method triggered after a 'sample' transition for the Sample passed in is
    performed.

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'sample')


def after_sample_due(sample):
    """Method triggered after a 'sample_due' transition for the Sample passed
    in is performed.

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'sample_due')


def after_receive(sample):
    """Method triggered after a 'receive' transition for the Sample passed in
    is performed.

    Stores value for "Date Received" field and also tries to perform the same
    transition to Sample Partitions and Analysis Requests associated to the
    sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """

    # In most cases, the date of a given transition can be retrieved from an
    # object by using a getter that delegates the action to getTransitionDate,
    # without the need of storing the value manually.
    # This is a different case: a DateTimeField/Widget field is explicitly
    # declared in Sample's schema because in some cases, the user may want to
    # change the Received Date by him/herself. For this reason, we set the
    # value manually here.
    sample.setDateReceived(DateTime())
    sample.reindexObject(idxs=["getDateReceived", ])
    _cascade_transition(sample, 'receive')


def after_reject(sample):
    """Method triggered after a 'reject' transition for the Sample passed in is
    performed.

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in. If rejection reasons are set
    for the current Sample, the same rejection reasons will be set to the
    Analysis Requests the rejection will be attempted to.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """

    # Before trying to cascade the transition to ARs, we need to set the value
    # for rejection reasons, just to prevent the reject guard from Analysis
    # Request to return False because there is no rejection reason set already.
    reasons = sample.getRejectionReasons()
    if reasons:
        for ar in sample.getAnalysisRequests():
            if not ar.getRejectionReasons():
                ar.setRejectionReasons(reasons)

    # Now, cascade the transition
    _cascade_transition(sample, 'reject')


def after_dispose(sample):
    """Method triggered after a 'dispose' transition for the Sample passed in
    is performed.

    Tries to perform the same transition to the Sample Partitions that belong
    to the sample passed in. It also stores value for "Date Disposed" field.
    Note that analysis requests are not affected by this transition.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    sample.setDateDisposed(DateTime())
    sample.reindexObject(idxs=["getDateDisposed", ])

    for partition in sample.getSamplePartitions():
        doActionFor(partition, 'dispose')


def after_expire(sample):
    """Method triggered after a 'expire' transition for the Sample passed in
    is performed.

    Tries to perform the same transition to the Sample Partitions that belong
    to the sample passed in. It also stores the value for "Date Expired" field.
    Note that analysis requests are not affected by this transition. If a
    Sample has expired, all Sample Partitions must expire too.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    sample.setDateExpired(DateTime())
    sample.reindexObject(idxs=["getDateExpired", ])

    for partition in sample.getSamplePartitions():
        doActionFor(partition, 'expire')


def after_sample_prep(sample):
    """Method triggered after a 'sample_prep' transition for the Sample passed
    in is performed.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    # TODO Workflow - Sample after_sample_prep
    pass


def after_sample_prep_complete(sample):
    """Method triggered after a 'sample_prep_complete' transition for the
    Sample passed in is performed.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    # TODO Workflow - Sample after_sample_prep_complete
    pass


def after_cancel(sample):
    """Method triggered after a 'cancel' transition for the Sample passed in
    is performed. Transition from bika_cancellation_workflow

    Tries to perform the same transition to the Sample Partitions and Analysis
    Requests associated to the sample passed in. If a Sample is cancelled, then
    all the Sample Partitions must be cancelled too.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'cancel')


def after_reinstate(sample):
    """Method triggered after a 'reinstate' transition for the Sample passed in
    is performed. Transition from bika_cancellation_workflow

    Tries to perform the same transition to Sample Partitions and Analysis
    Requests associated to the sample passed in.

    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler

    :param sample: Sample affected by the transition
    :type sample: Sample
    """
    _cascade_transition(sample, 'reinstate')
