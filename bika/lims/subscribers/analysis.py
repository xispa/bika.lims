# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from AccessControl import getSecurityManager
from Acquisition import aq_inner
from bika.lims import logger
from bika.lims.workflow import doActionFor
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import changeWorkflowState

from DateTime import DateTime
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.event import ObjectInitializedEvent
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
import transaction
import zope.event
from zope.interface import alsoProvides


def ObjectInitializedEventHandler(instance, event):
    """Fired when a IRoutineAnalysis has been created. Transitionates the
    object (or its container) to a suitable state, if necessary.

    The object is transitioned to the same state as the container (e.g.: if
    the Analysis Request is in a sampled state, the object's state must be
    the same). Also looks after eventual inconsistencies: if the state of the
    Analysis Request is to_be_verified, the AR itself must be transitioned
    back to "sample_received" (retract transition).

    :param instance: the analysis the event relates to
    :param event: the event instance
    :type instance: IRoutineAnalysis
    :type event: Products.Archetypes.interfaces.IObjectInitializedEvent
    """
    ar = instance.getRequest()
    ar_state = getCurrentState(ar)

    if ar_state == 'to_be_verified':
        # Since all the analyses from the Analysis Request have been already
        # submitted, the AR has been automatically transitioned to
        # 'to_be_verified'. To prevent inconsistencies, retract the AR to be
        # sure its state is 'sample_received' again. Note that retracting an
        # Analysis Request has no effect to the Analyses it contains.
        doActionFor(ar, 'retract')

    elif wasTransitionPerformed(ar, 'verify'):
        # Weird. this should never happen: no new analyses can be added to an
        # already verified Analysis Request
        raise Exception("Cannot add a routine analysis to a verified AR")

    else:
        # Force the analysis to the same state as the Analysis Request. We use
        # changeWorkflowState here because we are pretty sure doActionFor will
        # not work: we do not know beforehand if the current state would allow
        # such a transition.
        changeWorkflowState(instance, "bika_analysis_workflow", ar_state)


def ObjectRemovedEventHandler(instance, event):
    # TODO Workflow - Review all this function and normalize
    # May need to promote the AR's review_state
    # if all other analyses are at a higher state than this one was.
    workflow = getToolByName(instance, 'portal_workflow')
    ar = instance.getRequest()
    can_submit = True
    can_attach = True
    can_verify = True
    can_publish = True

    # We add this manually here, because during admin/ZMI removal,
    # it may possibly not be added by the workflow code.
    if not 'workflow_skiplist' in instance.REQUEST:
        instance.REQUEST['workflow_skiplist'] = []

    for a in ar.getAnalyses():
        a_state = a.review_state
        if a_state in \
           ('to_be_sampled', 'to_be_preserved',
            'sample_due', 'sample_received',):
            can_submit = False
        if a_state in \
           ('to_be_sampled', 'to_be_preserved',
            'sample_due', 'sample_received', 'attachment_due',):
            can_attach = False
        if a_state in \
           ('to_be_sampled', 'to_be_preserved',
            'sample_due', 'sample_received',
            'attachment_due', 'to_be_verified',):
            can_verify = False
        if a_state in \
           ('to_be_sampled', 'to_be_preserved',
            'sample_due', 'sample_received',
            'attachment_due', 'to_be_verified', 'verified',):
            can_publish = False

    # Note: AR adds itself to the skiplist so we have to take it off again
    #       to allow multiple promotions (maybe by more than one deleted instance).
    if can_submit and workflow.getInfoFor(ar, 'review_state') == 'sample_received':
        try:
            workflow.doActionFor(ar, 'submit')
        except WorkflowException:
            pass
        skip(ar, 'submit', unskip=True)
    if can_attach and workflow.getInfoFor(ar, 'review_state') == 'attachment_due':
        try:
            workflow.doActionFor(ar, 'attach')
        except WorkflowException:
            pass
        skip(ar, 'attach', unskip=True)
    if can_verify and workflow.getInfoFor(ar, 'review_state') == 'to_be_verified':
        instance.REQUEST["workflow_skiplist"].append('verify all analyses')
        try:
            workflow.doActionFor(ar, 'verify')
        except WorkflowException:
            pass
        skip(ar, 'verify', unskip=True)
    if can_publish and workflow.getInfoFor(ar, 'review_state') == 'verified':
        instance.REQUEST["workflow_skiplist"].append('publish all analyses')
        try:
            workflow.doActionFor(ar, 'publish')
        except WorkflowException:
            pass
        skip(ar, 'publish', unskip=True)

    ar_ws_state = workflow.getInfoFor(ar, 'worksheetanalysis_review_state')
    if ar_ws_state == 'unassigned':
        if not ar.getAnalyses(worksheetanalysis_review_state = 'unassigned'):
            if ar.getAnalyses(worksheetanalysis_review_state = 'assigned'):
                try:
                    workflow.doActionFor(ar, 'assign')
                except WorkflowException:
                    pass
                skip(ar, 'assign', unskip=True)

    return
