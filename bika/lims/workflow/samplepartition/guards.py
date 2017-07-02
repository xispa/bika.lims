from Products.CMFCore.utils import getToolByName
from bika.lims.workflow import isBasicTransitionAllowed


def guard_to_be_preserved(obj):
    """ Returns True if this Sample Partition needs to be preserved
    Returns false if no analyses have been assigned yet, or the Sample
    Partition has Preservation and Container objects assigned with the
    PrePreserved option set for the latter.
    """
    if not obj.getPreservation():
        return False

    if not obj.getAnalyses():
        return False

    container = obj.getContainer()
    if container and container.getPrePreserved():
        return False

    return isBasicTransitionAllowed(obj)
