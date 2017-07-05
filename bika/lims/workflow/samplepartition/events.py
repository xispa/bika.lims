from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

from bika.lims import logger
from bika.lims.workflow import skip
from bika.lims.workflow import doActionFor
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import isBasicTransitionAllowed
from bika.lims.workflow import wasTransitionPerformed

# TODO Workflow - SamplePartition. Review all


def _cascade_promote_transition(obj, transition_id, targetstate):
    """ Performs the transition for the actionid passed in to its children
    (Analyses). If all sibling partitions are in the targe state, promotes
    the transition to its parent Sample
    """
    # Transition our analyses
    for analysis in obj.getAnalyses():
        doActionFor(analysis, transition_id)

    # If all sibling partitions are received, promote Sample. Sample
    # transition will, in turn, transition the Analysis Requests.
    sample = obj.aq_parent
    parts = sample.objectValues("SamplePartition")
    recep = [sp for sp in parts if wasTransitionPerformed(sp, targetstate)]
    if len(parts) == len(recep):
        doActionFor(sample, transition_id)


def after_no_sampling_workflow(obj):
    """Method triggered after a 'no_sampling_workflow' transition for the
    current Sample is performed. Triggers the 'no_sampling_workflow'
    transition for depedendent objects, such as Sample Partitions and
    Analysis Requests.
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    """
    _cascade_promote_transition(obj, 'no_sampling_workflow', 'sampled')


def after_sampling_workflow(self):
    """Method triggered after a 'sampling_workflow' transition for the
    current Sample is performed. Triggers the 'sampling_workflow'
    transition for depedendent objects, such as Sample Partitions and
    Analysis Requests.
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    """
    _cascade_promote_transition(obj, 'sampling_workflow', 'to_be_sampled')


def after_sample(self):
    """Method triggered after a 'sample' transition for the current
    SamplePartition is performed. Triggers the 'sample' transition for
    depedendent objects, such as Analyses
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    """
    _cascade_promote_transition(obj, 'sample', 'sampled')


def after_sample_due(obj):
    """Method triggered after a 'sample_due' transition for the current
    SamplePartition is performed. Triggers the 'sample_due' transition for
    depedendent objects, such as Analyses
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    """
    _cascade_promote_transition(obj, 'sample_due', 'sample_due')


def after_receive(obj):
    """Method triggered after a 'receive' transition for the current Sample
    Partition is performed. Stores value for "Date Received" field and also
    triggers the 'receive' transition for depedendent objects, such as
    Analyses associated to this Sample Partition. If all Sample Partitions
    that belongs to the same sample as the current Sample Partition have
    been transitioned to the "received" state, promotes to Sample
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    """
    obj.setDateReceived(DateTime())
    obj.reindexObject(idxs=["getDateReceived", ])
    _cascade_promote_transition(obj, 'receive', 'sample_received')


def after_to_be_preserved(obj):
    sample = obj.aq_parent
    workflow = getToolByName(obj, 'portal_workflow')
    # Transition our analyses
    analyses = obj.getAnalyses()
    for analysis in analyses:
        doActionFor(analysis, "to_be_preserved")
    # if all our siblings are now up to date, promote sample and ARs.
    parts = sample.objectValues("SamplePartition")
    if parts:
        lower_states = ['to_be_sampled', 'to_be_preserved', ]
        escalate = True
        for part in parts:
            if workflow.getInfoFor(part, 'review_state') in lower_states:
                escalate = False
        if escalate:
            doActionFor(sample, "to_be_preserved")
            for ar in sample.getAnalysisRequests():
                doActionFor(ar, "to_be_preserved")


def after_preserve(obj):
    workflow = getToolByName(obj, 'portal_workflow')
    sample = obj.aq_parent
    # Transition our analyses
    analyses = obj.getAnalyses()
    if analyses:
        for analysis in analyses:
            doActionFor(analysis, "preserve")
    # if all our siblings are now up to date, promote sample and ARs.
    parts = sample.objectValues("SamplePartition")
    if parts:
        lower_states = ['to_be_sampled', 'to_be_preserved', ]
        escalate = True
        for part in parts:
            if workflow.getInfoFor(part, 'review_state') in lower_states:
                escalate = False
        if escalate:
            doActionFor(sample, "preserve")
            for ar in sample.getAnalysisRequests():
                doActionFor(ar, "preserve")


def after_reinstate(obj):
    sample = obj.aq_parent
    workflow = getToolByName(obj, 'portal_workflow')
    obj.reindexObject(idxs=["cancellation_state", ])
    sample_c_state = workflow.getInfoFor(sample, 'cancellation_state')
    # if all sibling partitions are active, activate sample
    if not skip(sample, "reinstate", peek=True):
        cancelled = [sp for sp in sample.objectValues("SamplePartition")
                     if workflow.getInfoFor(sp, 'cancellation_state') == 'cancelled']
        if sample_c_state == 'cancelled' and not cancelled:
            workflow.doActionFor(sample, 'reinstate')


def after_cancel(obj):
    if skip(obj, "cancel"):
        return
    sample = obj.aq_parent
    workflow = getToolByName(obj, 'portal_workflow')
    obj.reindexObject(idxs=["cancellation_state", ])
    sample_c_state = workflow.getInfoFor(sample, 'cancellation_state')
    # if all sibling partitions are cancelled, cancel sample
    if not skip(sample, "cancel", peek=True):
        active = [sp for sp in sample.objectValues("SamplePartition")
                  if workflow.getInfoFor(sp, 'cancellation_state') == 'active']
        if sample_c_state == 'active' and not active:
            workflow.doActionFor(sample, 'cancel')


def after_reject(obj):
    workflow = getToolByName(obj, 'portal_workflow')
    sample = obj.aq_parent
    obj.reindexObject(idxs=["review_state", ])
    sample_r_state = workflow.getInfoFor(sample, 'review_state')
    # if all sibling partitions are cancelled, cancel sample
    not_rejected = [sp for sp in sample.objectValues("SamplePartition")
              if workflow.getInfoFor(sp, 'review_state') != 'rejected']
    if sample_r_state != 'rejected':
        workflow.doActionFor(sample, 'reject')


def after_expire(obj):
    obj.setDateExpired(DateTime())
    obj.reindexObject(idxs=["review_state", "getDateExpired", ])
