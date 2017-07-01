from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

from bika.lims import logger
from bika.lims.workflow import changeWorkflowState
from bika.lims.workflow import doActionFor
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import isBasicTransitionAllowed
from bika.lims.workflow import wasTransitionPerformed
from bika.lims.workflow.analysis import events as analysis_events

# TODO Workflow - ReferenceAnalysis . Review

def after_submit(obj):
    """Method triggered after a 'submit' transition for the current
    ReferenceAnalysis is performed.
    By default, the "submit" action for transitions the RefAnalysis to the
    "attachment_due" state. If attachment is not required, the Reference
    Analysis is transitioned to 'to_be_verified' state (via 'attach').
    If all the analyses that belong to the same worksheet are in a suitable
    state, the 'submit' transition to the worksheet is triggered too.
    This function is called automatically by
    bika.lims.workflow.AfterTransitionEventHandler
    """
    # By default, the 'submit' action transitions the ReferenceAnalysis to
    # the 'attachment_due'. Since doActionFor already checks for the guards
    # in this case (guard_attach_transition), try always the transition to
    # 'to_be_verified' via 'attach' action
    # doActionFor will check the
    doActionFor(obj, 'attach')

    # Escalate to Worksheet. Note that the guard for submit transition from
    # Worksheet will check if the Worksheet can be transitioned, so there is no
    # need to check here if all analyses within the WS have been transitioned
    # already
    ws = obj.getWorksheet()
    if ws:
        doActionFor(ws, 'submit')


def after_attach(obj):
    # Escalate to Worksheet. Note that the guard for attach transition from
    # Worksheet will check if the Worksheet can be transitioned, so there is no
    # need to check here if all analyses within the WS have been transitioned
    # already
    ws = obj.getWorksheet()
    if ws:
        doActionFor(ws, 'attach')


def after_retract(obj):
    # Escalate to Worksheet. Note that the guard for attach transition from
    # Worksheet will check if the Worksheet can be transitioned, so there is no
    # need to check here if all analyses within the WS have been transitioned
    # already
    ws = obj.getWorksheet()
    if ws:
        doActionFor(ws, 'retract')


def after_verify(obj):
    # Escalate to Worksheet. Note that the guard for attach transition from
    # Worksheet will check if the Worksheet can be transitioned, so there is no
    # need to check here if all analyses within the WS have been transitioned
    # already
    ws = obj.getWorksheet()
    if ws:
        doActionFor(ws, 'verify')


def after_expire(obj):
    obj.setDateExpired(DateTime())


def after_dispose(obj):
    obj.setDateDisposed(DateTime())
