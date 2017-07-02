from Products.CMFCore.utils import getToolByName
from bika.lims.workflow import isBasicTransitionAllowed
from bika.lims.workflow import isTransitionAllowed
from bika.lims.workflow import wasTransitionPerformed
from bika.lims.permissions import Unassign


def guard_submit(obj):
    """Returns true if the 'submit' transition can be performed to the analysis
    passed in.

    Returns True if the following conditions are met:
    - The analysis is active (neither inactive nor cancelled state)
    - The current user has enough privileges to fire the 'submit' transition
    - A non-empty result for this analysis has been set or, if the result of
      the analysis is binded to a calculation, results of all dependencies and
      values for interim fields are not empty.

    :param obj: the analysis for which the submit transition must be evaluated
    :type obj: AbstractRoutineAnalysis
    :returns: True or False
    :rtype: bool
    """
    if not isBasictransitionAllowed(obj):
        return False

    # If the state is sample_due, only permit the submit transition if the
    # point of capture is 'field'
    state = getCurrentState(oj)
    if state == 'sample_due' and obj.getPointOfCapture() != 'field':
        return False

    # If the analysis has a result, then we can assume the rest of conditions
    # regarding calculation and dependencies have been met, so there is no
    # need of further checks.
    if obj.getResult():
        return True

    # If there is a calculation associated to this analysis, be sure the
    # interim fields have values set.
    calculation = obj.getCalculation()
    if calculation and not calculation.getInterimFields():
        return False

    # Check if all dependencies have been submitted already or are ready
    # Remember dependencies are those analyses required for the calculation of
    # the result of the current analysis.
    dependencies = obj.getDependencies()
    for dep in dependencies:
        if not wasTransitionPerformed(dep, 'submit'):
            if not isTransitionAllowed(dep, 'submit'):
                # There is at least one dependency that hasn't been submitted
                # yet or cannot be submitted.
                return False

    return True


def guard_sample(obj):
    """ Returns true if the sample transition can be performed for the sample
    passed in.
    :returns: true or false
    """
    return isBasicTransitionAllowed(obj)


def guard_to_be_preserved(obj):
    """Returns if the Sample Partition to which this Analysis belongs needs
    to be prepreserved, so the Analysis. If the analysis has no Sample
    Partition assigned, returns False.
    Delegates to Sample Partitions's guard_to_be_preserved
    """
    part = obj.getSamplePartition()
    if not part:
        return False
    return isTransitionAllowed(part, 'to_be_preserved')

def guard_retract(obj):
    """ Returns true if the sample transition can be performed for the sample
    passed in.
    :returns: true or false
    """
    return isBasicTransitionAllowed(obj)


def guard_sample_prep(obj):
    return isBasicTransitionAllowed(obj)


def guard_sample_prep_complete(obj):
    return isBasicTransitionAllowed(obj)


def guard_receive(obj):
    return isBasicTransitionAllowed(obj)


def guard_publish(obj):
    """ Returns true if the 'publish' transition can be performed to the
    analysis passed in.
    In accordance with bika_analysis_workflow, 'publish'
    transition can only be performed if the state of the analysis is verified,
    so this guard only checks if the analysis state is active: there is no need
    of additional checks, cause the DC Workflow machinery will already take
    care of them.
    :returns: true or false
    """
    return isBasicTransitionAllowed(obj)


def guard_import(obj):
    return isBasicTransitionAllowed(obj)


def guard_attach(obj):
    if not isBasicTransitionAllowed(obj):
        return False
    if not obj.getAttachment():
        return obj.getAttachmentOption() != 'r'
    return True


def guard_assign(obj):
    return isBasicTransitionAllowed(obj)


def guard_unassign(obj):
    """Check permission against parent worksheet
    """
    mtool = getToolByName(obj, "portal_membership")
    if not isBasicTransitionAllowed(obj):
        return False
    ws = obj.getBackReferences("WorksheetAnalysis")
    if not ws:
        return False
    ws = ws[0]
    if isBasicTransitionAllowed(ws):
        if mtool.checkPermission(Unassign, ws):
            return True
    return False


def guard_verify(obj):
    if not isBasicTransitionAllowed(obj):
        return False

    if obj.isVerifiable():
        mtool = getToolByName(obj, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        return obj.isUserAllowedToVerify(member)

    return False


def guard_reject(obj):
    if not isBasicTransitionAllowed(obj):
        return False
    return obj.bika_setup.isRejectionWorkflowEnabled()


# TODO Workflow Analysis - Enable and review together with bika_listing stuff
def guard_new_verify(obj):
    """
    Checks if the verify transition can be performed to the Analysis passed in
    by the current user depending on the user roles, the current status of the
    object and the number of verifications already performed.
    :returns: true or false
    """
    if not isBasicTransitionAllowed(obj):
        return False

    nmvers = obj.getNumberOfVerifications()
    if nmvers == 0:
        # No verification has been done yet.
        # The analysis can only be verified it all its dependencies have
        # already been verified
        for dep in obj.getDependencies():
            if not verify(dep):
                return False

    revers = obj.getNumberOfRequiredVerifications()
    if revers - nmvers == 1:
        # All verifications performed except the last one. Check if the user
        # can perform the verification and if so, then allow the analysis to
        # be transitioned to the definitive "verified" state (otherwise will
        # remain in "to_be_verified" until all remmaining verifications - 1 are
        # performed
        mtool = getToolByName(obj, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        return obj.isUserAllowedToVerify(member)

    return False
