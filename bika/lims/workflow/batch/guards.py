from bika.lims.workflow import BatchState
from bika.lims.workflow import CancellationState
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import isBasicTransitionAllowed
from bika.lims.workflow import StateFlow


def guard_open(obj):
    """ Permitted if current review_state is 'closed' or 'cancelled'
        The open transition is already controlled by 'Bika: Reopen Batch'
        permission, but left here for security reasons and also for the
        capability of being expanded/overrided by child products or
        instance-specific-needs.
    """
    revstatus = getCurrentState(obj, StateFlow.review)
    canstatus = getCurrentState(obj, StateFlow.cancellation)
    return revstatus == BatchState.closed \
        and canstatus == CancellationState.active


def guard_close(obj):
    """ Permitted if current review_state is 'open'.
        The close transition is already controlled by 'Bika: Close Batch'
        permission, but left here for security reasons and also for the
        capability of being expanded/overrided by child products or
        instance-specific needs.
    """
    revstatus = getCurrentState(obj, StateFlow.review)
    canstatus = getCurrentState(obj, StateFlow.cancellation)
    return revstatus == BatchState.open \
        and canstatus == CancellationState.active
