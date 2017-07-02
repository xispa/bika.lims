from bika.lims.workflow import isBasicTransitionAllowed


def guard_cancel(obj):
    return isBasicTransitionAllowed(obj)


def guard_reinstate(self):
    return isBasicTransitionAllowed(obj)
