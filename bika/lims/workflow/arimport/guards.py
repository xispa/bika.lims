from bika.lims.workflow import isBasicTransitionAllowed


def guard_validate(obj):
    """We may only attempt validation if file data has been uploaded.
    """
    data = obj.getOriginalFile()
    if data and len(data):
        return isBasicTransitionAllowed(obj)
