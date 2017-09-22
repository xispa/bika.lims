from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

from bika.lims import logger
from bika.lims.interfaces import IRoutineAnalysis
from bika.lims.utils.analysis import create_analysis
from bika.lims.workflow import changeWorkflowState
from bika.lims.workflow import doActionFor
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import isBasicTransitionAllowed
from bika.lims.workflow import wasTransitionPerformed
from bika.lims.workflow import skip


def before_submit(obj):
    """Fired before a 'submit' transition for the analysis passed in

    If the analysis result is binded to a calculation and the calculation
    requires results from other analyses (dependencies), the function will try
    to transition all them first. Note that this function only attemps to
    transition the dependencies, but is responsability of the guard_submit
    to evaluate if dependencies are suitable for transition.

    This function is called automatically by
    bika.lims.workflow.BeoreTransitionEventHandler

    :param obj: the analysis to be transitioned
    :type obj: AbstractRoutineAnalysis
    """
    dependencies = obj.getDependencies()
    for dependency in dependencies:
        doActionFor(dependency, 'submit')


def after_submit(obj):
    """Method triggered after a 'submit' transition for the analysis passed in
    is performed.

    If there are analyses that depends on this analysis to calculate their
    results, the function will try to transition them too. Note that this
    function only attempts the transition of dependents. Is responsability of
    the guard_submit to evaluate if the dependent is suitable for transition.

    After trying to transition dependents, it fires the reflex rules associated
    to the analysis and binded to 'submit' transition. Note that as a result,
    new analyses might be created and assigned to the same Analysis Request or
    Worksheet the current analysis belongs to.

    After this, tries to transition the Analysis Request the analysis belongs
    to. Note there is a guard for Analysis Request that will check if the
    Analysis Request is in a suitable state for such a transition.

    Also promotes the submit transition to the Worksheet to which the analysis
    belongs to. Note that for the worksheet there is already a guard that
    assures the transition to the worksheet will only be performed if all
    analyses within the worksheet have already been transitioned.

    This function is called automatically by
    bika.lims.workfow.AfterTransitionEventHandler

    :param obj: the analysis that has been transitioned
    :type obj: AbstractRoutineAnalysis
    """
    # Try to transition dependents
    dependents = obj.getDependents()
    for dependent in dependents:
        doActionFor(dependent, 'submit')

    # Trigger all the reflex rules process associate to 'submit' transition.
    # It may create new analysis associated to the same AR of this Analysis,
    # to the same Worksheet, etc., so is important to call this function before
    # trying further transitions for Analysis Request and Worksheet.
    obj.fire_reflex_rules('submit')

    # Escalate to Analysis Request. Note that the guard for submit transition
    # from Analysis Request will check if the AR can be transitioned, so there
    # is no need to check here if all analyses within the AR have been
    # transitioned already.
    ar = obj.getRequest()
    doActionFor(ar, 'submit')

    # Ecalate to Worksheet. Note that the guard for submit transition from
    # Worksheet will check if the Worksheet can be transitioned, so there is no
    # need to check here if all analyses within the WS have been transitioned
    # already
    ws = obj.getWorksheet()
    if ws:
        doActionFor(ws, 'submit')
    _reindex_request(obj)


def after_retract(obj):
    """Function triggered after a 'retract' transition for the analysis passed
    in is performed. Retracting an analysis cause its transition to 'retracted'
    state and the creation of a new copy of the same analysis as a retest.
    Note that retraction only affects to single Analysis and has no other
    effect in the status of the Worksheet to which the Analysis is assigned or
    to the Analysis Request to which belongs (transition is never proomoted)
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    """
    # TODO Workflow Analysis - review this function
    # Rename the analysis to make way for it's successor.
    # Support multiple retractions by renaming to *-0, *-1, etc
    parent = obj.aq_parent
    kw = obj.getKeyword()
    analyses = [x for x in parent.objectValues("Analysis")
                if x.getId().startswith(obj.getId())]

    # LIMS-1290 - Analyst must be able to retract, which creates a new
    # Analysis.  So, _verifyObjectPaste permission check must be cancelled:
    parent._verifyObjectPaste = str
    parent.manage_renameObject(kw, "{0}-{1}".format(kw, len(analyses)))
    delattr(parent, '_verifyObjectPaste')

    # Create new analysis from the retracted obj
    analysis = create_analysis(parent, obj)
    changeWorkflowState(
        analysis, "bika_analysis_workflow", "sample_received")

    # Assign the new analysis to this same worksheet, if any.
    ws = obj.getWorksheet()
    if ws:
        ws.addAnalysis(analysis)
    analysis.reindexObject()

    # retract our dependencies
    dependencies = obj.getDependencies()
    for dependency in dependencies:
        doActionFor(dependency, 'retract')

    # Retract our dependents
    dependents = obj.getDependents()
    for dependent in dependents:
        doActionFor(dependent, 'retract')

    _reindex_request(obj)


def after_verify(obj):
    """
    Method triggered after a 'verify' transition for the analysis passed in
    is performed. Promotes the transition to the Analysis Request and to
    Worksheet (if the analysis is assigned to any)
    This function is called automatically by
    bika.lims.workfow.AfterTransitionEventHandler
    """

    # If the analysis has dependencies, transition them
    for dependency in obj.getDependencies():
        doActionFor(dependency, 'verify')

    # Do all the reflex rules process
    obj.fire_reflex_rules('verify')

    # Escalate to Analysis Request. Note that the guard for verify transition
    # from Analysis Request will check if the AR can be transitioned, so there
    # is no need to check here if all analyses within the AR have been
    # transitioned already.
    ar = obj.getRequest()
    doActionFor(ar, 'verify')

    # Ecalate to Worksheet. Note that the guard for verify transition from
    # Worksheet will check if the Worksheet can be transitioned, so there is no
    # need to check here if all analyses within the WS have been transitioned
    # already
    ws = obj.getWorksheet()
    if ws:
        doActionFor(ws, 'verify')
    _reindex_request(obj)



def after_cancel(obj):
    # TODO Workflow Analysis - review this function
    if skip(obj, "cancel"):
        return
    workflow = getToolByName(obj, "portal_workflow")
    # If it is assigned to a worksheet, unassign it.
    state = workflow.getInfoFor(obj, 'worksheetanalysis_review_state')
    if state == 'assigned':
        ws = obj.getWorksheet()
        skip(obj, "cancel", unskip=True)
        ws.removeAnalysis(obj)
    obj.reindexObject()
    _reindex_request(obj)


def after_reject(obj):
    # TODO Workflow Analysis - review this function
    if skip(obj, "reject"):
        return
    workflow = getToolByName(obj, "portal_workflow")
    # If it is assigned to a worksheet, unassign it.
    state = workflow.getInfoFor(obj, 'worksheetanalysis_review_state')
    if state == 'assigned':
        ws = obj.getWorksheet()
        ws.removeAnalysis(obj)
    obj.reindexObject()
    _reindex_request(obj)


def after_attach(obj):
    # TODO Workflow Analysis - review this function
    if skip(obj, "attach"):
        return
    workflow = getToolByName(obj, "portal_workflow")
    # If all analyses in this AR have been attached escalate the action
    # to the parent AR
    ar = obj.aq_parent
    state = workflow.getInfoFor(ar, "review_state")
    if state == "attachment_due" and not skip(ar, "attach", peek=True):
        can_attach = True
        for a in ar.getAnalyses():
            if a.review_state in ("to_be_sampled", "to_be_preserved",
                                  "sample_due", "sample_received",
                                  "attachment_due"):
                can_attach = False
                break
        if can_attach:
            workflow.doActionFor(ar, "attach")
    # If assigned to a worksheet and all analyses on the worksheet have
    # been attached, then attach the worksheet.
    ws = obj.getBackReferences('WorksheetAnalysis')
    if ws:
        ws_state = workflow.getInfoFor(ws, "review_state")
        if ws_state == "attachment_due" \
                and not skip(ws, "attach", peek=True):
            can_attach = True
            for a in ws.getAnalyses():
                state = workflow.getInfoFor(a, "review_state")
                if state in ("to_be_sampled", "to_be_preserved",
                             "sample_due", "sample_received",
                             "attachment_due", "assigned"):
                    can_attach = False
                    break
            if can_attach:
                workflow.doActionFor(ws, "attach")
    obj.reindexObject()
    _reindex_request(obj)


def _reindex_request(obj):
    if IRoutineAnalysis.providedBy(obj):
        request = obj.getRequest()
        if request:
            request.reindexObject()