# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from bika.lims import enum
from bika.lims import PMF
from bika.lims.browser import ulocalized_time
from bika.lims.interfaces import IJSONReadExtender
from bika.lims.jsonapi import get_include_fields
from bika.lims.utils import t
from bika.lims import logger
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IWorkflowChain
from Products.CMFPlone.workflow import ToolWorkflowChain
from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION
from zope.component import adapts
from zope.interface import implementer
from zope.interface import implements
from zope.interface import Interface
import sys
import traceback


def skip(instance, action, peek=False, unskip=False):
    """Returns True if the transition is to be SKIPPED

        peek - True just checks the value, does not set.
        unskip - remove skip key (for manual overrides).

    called with only (instance, action_id), this will set the request variable preventing the
    cascade's from re-transitioning the object and return None.
    """

    uid = callable(instance.UID) and instance.UID() or instance.UID
    skipkey = "%s_%s" % (uid, action)
    if 'workflow_skiplist' not in instance.REQUEST:
        if not peek and not unskip:
            instance.REQUEST['workflow_skiplist'] = [skipkey, ]
    else:
        if skipkey in instance.REQUEST['workflow_skiplist']:
            if unskip:
                instance.REQUEST['workflow_skiplist'].remove(skipkey)
            else:
                return True
        else:
            if not peek and not unskip:
                instance.REQUEST["workflow_skiplist"].append(skipkey)


def doActionFor(instance, action_id, active_only=True, allowed_transition=True):
    """Performs the transition (action_id) to the instance.

    The transition will only be triggered if the current state of the object
    allows the action_id passed in (delegate to isTransitionAllowed) and the
    instance hasn't been flagged as to be skipped previously.
    If active_only is set to True, the instance will only be transitioned if
    it's current state is active (not cancelled nor inactive)

    :param instance: Object to be transitioned
    :param action_id: transition id
    :param active_only: True if transition must apply to active objects
    :param allowed_transition: True for a allowed transition check
    :returns: true if the transition has been performed and message
    :rtype: list
    """
    actionperformed = False
    message = ''
    if isinstance(instance, list):
        # This check is here because sometimes Plone creates a list
        # from submitted form elements.
        if len(instance) > 1:
            logger.error(
                "doActionFor is getting an instance paramater which is alist  "
                "with more than one item. Instance: '{}', action_id: '{}'"
                .format(instance, action_id)
            )
        instance = instance[0]
    if not instance:
        return actionperformed, message

    workflow = getToolByName(instance, "portal_workflow")
    skipaction = skip(instance, action_id, peek=True)
    if skipaction:
        clazzname = instance.__class__.__name__
        msg = "Skipping transition '{0}': {1} '{2}'".format(action_id,
                                                            clazzname,
                                                            instance.getId())
        logger.info(msg)
        return actionperformed, message

    if allowed_transition:
        allowed = isTransitionAllowed(instance, action_id, active_only)
        if not allowed:
            transitions = workflow.getTransitionsFor(instance)
            transitions = [trans['id'] for trans in transitions]
            transitions = ', '.join(transitions)
            currstate = getCurrentState(instance)
            clazzname = instance.__class__.__name__
            msg = "Transition '{0}' not allowed: {1} '{2}' ({3}). " \
                  "Available transitions: {4}".format(action_id, clazzname,
                                                      instance.getId(),
                                                      currstate, transitions)
            logger.warning(msg)
            _logTransitionFailure(instance, action_id)
            return actionperformed, message
    else:
        logger.warning(
            "doActionFor should never (ever) be called with allowed_transition"
            "set to True as it avoids permission checks.")
    try:
        workflow.doActionFor(instance, action_id)
        actionperformed = True
    except WorkflowException as e:
        message = str(e)
        logger.error(message)
    return actionperformed, message


def _logTransitionFailure(obj, transition_id):
    wftool = getToolByName(obj, "portal_workflow")
    chain = wftool.getChainFor(obj)
    for wf_id in chain:
        wf = wftool.getWorkflowById(wf_id)
        if wf is not None:
            sdef = wf._getWorkflowStateOf(obj)
            if sdef is not None:
                for tid in sdef.transitions:
                    if tid != transition_id:
                        continue
                    tdef = wf.transitions.get(tid, None)
                    if not tdef:
                        continue
                    if tdef.trigger_type != TRIGGER_USER_ACTION:
                        logger.warning("  Trigger type is not manual")
                    if not tdef.actbox_name:
                        logger.warning("  No actbox_name set")
                    if not wf._checkTransitionGuard(tdef, obj):
                        guard = tdef.guard
                        expr = guard.getExprText()
                        logger.warning("  Guard failed: {0}".format(expr))
                    return
    logger.warning("Transition not found. Check the workflow definition!")


def doActionsFor(instance, actions):
    """Performs a set of transitions to the instance passed in
    """
    startpoint = False
    prevevents = getReviewHistoryActionsList(instance)
    for action in actions:
        if not startpoint and action in prevevents:
            continue
        startpoint = True
        doActionFor(instance, action)


def BeforeTransitionEventHandler(instance, event):
    """ This event is executed before each transition and delegates further
    actions to 'before_<transition_id>' function if exists in the module
    bika.lims.workflow.<instance_class_name>.

    If the abovementioned functoin does not exist or if there is no transition
    for the state change (like the 'creation' state, then the function does
    nothing.

    :param instance: the instance to be transitioned
    :type instance: ATContentType
    :param event: event that holds the transition to be performed
    :type event: IObjectEvent
    """
    # there is no transition for the state change (creation doesn't have a
    # 'transition')
    if not event.transition:
        return

    clazzname = instance.portal_type
    currstate = getCurrentState(instance)
    msg = "Transition '{0}' started: {1} '{2}' ({3})".format(
        event.transition.id,  clazzname, instance.getId(), currstate)
    logger.info(msg)

    # Inspect if bika.lims.workflow.<clazzname>.<events> module exists
    wfmodule = sys.modules['{}.{}.events'.format(__name__, clazzname.lower())]
    if not wfmodule:
        return

    # Inspect if before_<transition_id> function exists in the above module
    key = 'before_{0}'.format(event.transition.id)
    before_event = getattr(wfmodule, key, False)
    if not before_event:
        return

    # Fire the before_event
    msg = "BeforeTransition for {0} ({1}) {2}: {3}'"
    fullname = '{0}.{1}'.format(wfmodule.__name__, key)
    logger.info(msg.format(clazzname, instance.getId(), 'started', fullname))
    before_event(instance)
    logger.info(msg.format(clazzname, instance.getId(), 'finished', fullname))


def AfterTransitionEventHandler(instance, event):
    """ This event is executed after each transition and delegates further
    actions to 'after_x_transition_event' function if exists in the instance
    passed in, where 'x' is the id of the event's transition.

    If the passed in instance has not a function with the abovementioned
    signature, or if there is no transition for the state change (like the
    'creation' state) or the same transition has already been run for the
    the passed in instance during the current server request, then the
    function does nothing.

    :param instance: the instance that has been transitioned
    :type instance: ATContentType
    :param event: event that holds the transition performed
    :type event: IObjectEvent
    """
    # there is no transition for the state change (creation doesn't have a
    # 'transition')
    if not event.transition:
        return

    # Set the request variable preventing cascade's from re-transitioning.
    if skip(instance, event.transition.id):
        return

    clazzname = instance.portal_type
    currstate = getCurrentState(instance)
    msg = "Transition '{0}' finished: '{1}' '{2}' ({3})".format(
        event.transition.id,  clazzname, instance.getId(), currstate)
    logger.info(msg)

    # Because at this point, the object has been transitioned already, but
    # further actions are probably needed still, so be sure is reindexed
    # before going forward.
    instance.reindexObject()

    # Inspect if bika.lims.workflow.<clazzname>.<events> module exists
    wfmodule = sys.modules['{}.{}.events'.format(__name__, clazzname.lower())]
    if not wfmodule:
        return

    # Inspect if after_<transition_id> function exists in the above module
    key = 'after_{0}'.format(event.transition.id)
    after_event = getattr(wfmodule, key, False)
    if not after_event:
        return

    # Fire the after_event
    msg = "AfterTransition for {0} ({1}) {2}: {3}'"
    fullname = '{0}.{1}'.format(wfmodule.__name__, key)
    logger.info(msg.format(clazzname, instance.getId(), 'started', fullname))
    after_event(instance)
    logger.info(msg.format(clazzname, instance.getId(), 'finished', fullname))


def get_workflow_actions(obj):
    """ Compile a list of possible workflow transitions for this object
    """

    def translate(id):
        return t(PMF(id + "_transition_title"))

    workflow = getToolByName(obj, 'portal_workflow')
    actions = [{"id": it["id"],
                "title": translate(it["id"])}
               for it in workflow.getTransitionsFor(obj)]

    return actions


def isBasicTransitionAllowed(context, permission=None):
    """Most transition guards need to check the same conditions:

    - Is the object active (cancelled or inactive objects can't transition)
    - Has the user a certain permission, required for transition.  This should
    normally be set in the guard_permission in workflow definition.

    """
    workflow = getToolByName(context, "portal_workflow")
    mtool = getToolByName(context, "portal_membership")
    if not isActive(context):
        return False
    if permission:
        return mtool.checkPermission(permission, context)
    return True


def isTransitionAllowed(instance, transition_id, active_only=True):
    """Checks if the object can perform the transition passed in.
    If active_only is set to true, the function will always return false if the
    object's current state is inactive or cancelled.
    Apart from the current state, it also checks if the guards meet the
    conditions (as per workflowtool.getTransitionsFor)
    :returns: True if transition can be performed
    :rtype: bool
    """
    if active_only and not isBasicTransitionAllowed(instance):
        return False

    wftool = getToolByName(instance, "portal_workflow")
    chain = wftool.getChainFor(instance)
    for wf_id in chain:
        wf = wftool.getWorkflowById(wf_id)
        if wf and wf.isActionSupported(instance, transition_id):
            return True

    return False


def wasTransitionPerformed(instance, transition_id):
    """Checks if the transition passed in has been performed to the object.
    :param instance: the object to check for the transition passed in
    :param transition_id: the id of the transition to check
    :type instance: ATContentType
    :returns: true or false
    :rtype: bool
    """
    review_history = getReviewHistory(instance)
    for event in review_history:
        if event['action'] == transition_id:
            return True
    return False


def isActive(instance):
    """Returns True if the object is neither in a cancelled nor inactive state
    :param instance: the object to check for its active/inactive status
    :type instance: ATContentType
    :returns: true or false
    :rtype: bool
    """
    state = getCurrentState(instance, 'cancellation_state')
    if state == 'cancelled':
        return False
    state = getCurrentState(instance, 'inactive_state')
    if state == 'inactive':
        return False
    return True


def getReviewHistoryActionsList(instance):
    """Returns a list with the actions performed for the instance, from oldest
    to newest. If there is no review history for the instance passed in or the
    user has not enough privileges to see it, returns an empty list.
    :param instance: the object to retrieve the review history from
    :type instance: ATContentType
    :returns: the list of action/transition ids, sorted from oldest to newest
    :rtype: list
    """
    review_history = getReviewHistory()
    review_history.reverse()
    actions = [event['action'] for event in review_history]
    return actions


def getReviewHistory(instance):
    """Returns the review history for the instance in reverse order, from newer
    to older. If there is no review history for the instance passed in or the
    current user has not enough privileges to see it, returns an empty list
    :param instance: the object to retrieve the review history from
    :type instance: ATContentType
    :returns: the list of historic events as dicts
    :rtype: list of dicts
    """
    review_history = []
    workflow = getToolByName(instance, 'portal_workflow')
    try:
        # https://jira.bikalabs.com/browse/LIMS-2242:
        # Sometimes the workflow history is inexplicably missing!
        review_history = list(workflow.getInfoFor(instance, 'review_history'))
    except WorkflowException:
        logger.error(
            "workflow history is inexplicably missing."
            " https://jira.bikalabs.com/browse/LIMS-2242")
    # invert the list, so we always see the most recent matching event
    review_history.reverse()
    return review_history


def getCurrentState(obj, stateflowid='review_state'):
    """ The current state of the object for the state flow id specified
        Return empty if there's no workflow state for the object and flow id
    :param obj: the object from which the current state has to be retrieved
    :type obj: ATContentType
    :param stateflowid: the state flow id
    :type stateflowid: string
    :returns: the state of the passed in object for the passed in state flow id
    :rtype: string
    """
    wf = getToolByName(obj, 'portal_workflow')
    return wf.getInfoFor(obj, stateflowid, '')


def getTransitionActor(obj, action_id):
    """Returns the actor that performed a given transition. If transition has
    not been performed, or current user has no privileges, returns None. If
    the transition has been performed multiple times for the the passed-in
    object, returns actor who performed the last transition
    :param obj: object for which the transition was performed
    :type obj: ATContentType
    :param action_id: the transition id
    :type action_id: string
    :returns: the username of the user that performed the transition passed-in
    :rtype: string
    """
    review_history = getReviewHistory(obj)
    for event in review_history:
        if event.get('action') == action_id:
            return event.get('actor')
    return None


def getTransitionActors(obj, action_id):
    """Returns the actors that performed a given transition, sorted by the time
    the transition was performed descendant. If transition has not been
    performed, or current user has no privileges, returns an empty list.
    :param obj: object for which the transition was performed
    :type obj: ATContentType
    :param action_id: the transition id
    :type action_id: string
    :returns: usernames of users that performed the transition passed-in
    :rtype: list
    """
    actors = []
    review_history = getReviewHistory(obj)
    for event in review_history:
        if event.get('action') == action_id:
            actor = event.get('actor')
            actors.append(actor)
    return actors


def getTransitionMember(obj, action_id):
    """Returns the member that performed a given transition. If transition has
    not been performed, or current user has no privileges, returns None. If the
    transition has been performed multiple times for the the passed-in object,
    returns the member who performed the last transition
    :param obj: object for which the transition was performed
    :type obj: ATContentType
    :param action_id: the transition id
    :type action_id: string
    :returns: the member that performed the transition passed-in
    :rtype: IMember
    """
    actor = getTransitionActor(action_id)
    if not actor:
        return None
    mtool = getToolByName(self, 'portal_membership')
    member = mtool.getMemberById(actor)
    return member


def getTransitionDate(obj, action_id, return_as_datetime=False):
    """Returns the date when the transition passed-in was performed.
    If transition has not been performed to the passed in object, or current
    user has no privileges, returns None. If the the transition has been
    performed multiple times for the passed-in object, returns the last
    transition date.
    :param obj: object for which the transition was performed
    :param action_id: the transition id
    :param return_as_datetime: return the result as datetime or string
    :type obj: ATContentType
    :type action_id: string
    :type return_as_datetime: bool
    :returns: the date when the transition was performed
    """
    review_history = getReviewHistory(obj)
    for event in review_history:
        if event.get('action') == action_id:
            evtime = event.get('time')
            if return_as_datetime:
                return evtime
            if evtime:
                value = ulocalized_time(evtime, long_format=True,
                                        time_only=False, context=obj)
                return value
    return None


def changeWorkflowState(content, wf_id, state_id, acquire_permissions=False,
                        portal_workflow=None, **kw):
    """Change the workflow state of an object
    @param content: Content obj which state will be changed
    @param state_id: name of the state to put on content
    @param acquire_permissions: True->All permissions unchecked and on riles and
                                acquired
                                False->Applies new state security map
    @param portal_workflow: Provide workflow tool (optimisation) if known
    @param kw: change the values of same name of the state mapping
    @return: None
    """

    if portal_workflow is None:
        portal_workflow = getToolByName(content, 'portal_workflow')

    # Might raise IndexError if no workflow is associated to this type
    found_wf = 0
    for wf_def in portal_workflow.getWorkflowsFor(content):
        if wf_id == wf_def.getId():
            found_wf = 1
            break
    if not found_wf:
        logger.error("%s: Cannot find workflow id %s" % (content, wf_id))

    wf_state = {
        'action': None,
        'actor': None,
        'comments': "Setting state to %s" % state_id,
        'review_state': state_id,
        'time': DateTime(),
        }

    # Updating wf_state from keyword args
    for k in kw.keys():
        # Remove unknown items
        if k not in wf_state:
            del kw[k]
    if 'review_state' in kw:
        del kw['review_state']
    wf_state.update(kw)

    portal_workflow.setStatusOf(wf_id, content, wf_state)

    if acquire_permissions:
        # Acquire all permissions
        for permission in content.possible_permissions():
            content.manage_permission(permission, acquire=1)
    else:
        # Setting new state permissions
        wf_def.updateRoleMappingsFor(content)

    # Map changes to the catalogs
    content.reindexObject(idxs=['allowedRolesAndUsers', 'review_state'])
    return


# Enumeration of the available status flows
StateFlow = enum(review='review_state',
                 inactive='inactive_state',
                 cancellation='cancellation_state')

# Enumeration of the different available states from the inactive flow
InactiveState = enum(active='active')

# Enumeration of the different states can have a batch
BatchState = enum(open='open',
                  closed='closed',
                  cancelled='cancelled')

BatchTransitions = enum(open='open',
                        close='close')

CancellationState = enum(active='active',
                         cancelled='cancelled')

CancellationTransitions = enum(cancel='cancel',
                               reinstate='reinstate')


class JSONReadExtender(object):

    """- Adds the list of possible transitions to each object, if 'transitions'
    is specified in the include_fields.
    """

    implements(IJSONReadExtender)

    def __init__(self, context):
        self.context = context

    def __call__(self, request, data):
        include_fields = get_include_fields(request)
        if not include_fields or "transitions" in include_fields:
            data['transitions'] = get_workflow_actions(self.context)



@implementer(IWorkflowChain)
def SamplePrepWorkflowChain(ob, wftool):
    """Responsible for inserting the optional sampling preparation workflow
    into the workflow chain for objects with ISamplePrepWorkflow

    This is only done if the object is in 'sample_prep' state in the
    primary workflow (review_state).
    """
    # use catalog to retrieve review_state: getInfoFor causes recursion loop
    chain = list(ToolWorkflowChain(ob, wftool))
    try:
        bc = getToolByName(ob, 'bika_catalog')
    except AttributeError:
        logger.warning(traceback.format_exc())
        logger.warning(
            "Error getting 'bika_catalog' using 'getToolByName' with '{0}'"
            " as context.".format(ob))
        return chain
    proxies = bc(UID=ob.UID())
    if not proxies or proxies[0].review_state != 'sample_prep':
        return chain
    sampleprep_workflow = ob.getPreparationWorkflow()
    if sampleprep_workflow:
        chain.append(sampleprep_workflow)
    return tuple(chain)


def SamplePrepTransitionEventHandler(instance, event):
    """Sample preparation is considered complete when the sampleprep workflow
    reaches a state which has no exit transitions.

    If the stateis state's ID is the same as any AnalysisRequest primary
    workflow ID, then the AnalysisRequest will be sent directly to that state.

    If the final state's ID is not found in the AR workflow, the AR will be
    transitioned to 'sample_received'.
    """
    if not event.transition:
        # creation doesn't have a 'transition'
        return

    if not event.new_state.getTransitions():
        # Is this the final (No exit transitions) state?
        wftool = getToolByName(instance, 'portal_workflow')
        primary_wf_name = list(ToolWorkflowChain(instance, wftool))[0]
        primary_wf = wftool.getWorkflowById(primary_wf_name)
        primary_wf_states = primary_wf.states.keys()
        if event.new_state.id in primary_wf_states:
            # final state name matches review_state in primary workflow:
            dst_state = event.new_state.id
        else:
            # fallback state:
            dst_state = 'sample_received'
        changeWorkflowState(instance, primary_wf_name, dst_state)
