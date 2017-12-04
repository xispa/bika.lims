from bika.lims import logger
from bika.lims import api
from Products.CMFCore.Expression import Expression

def fix_workflows(portal):
    # Rename all guard expressions to python:here.guard_handler('<action_id>')
    set_guard_expressions(portal)

    # Fix workflow transitions
    fix_workflow_transitions(portal)

    # Removes states that are no longer used
    remove_stale_states(portal)


def set_guard_expressions(portal):
    """Rename all guard expressions to python:here.guard_handler('<action_id>')
    """
    bika_workflows = ['bika_analysis_workflow',
                      'bika_ar_workflow',
                      'bika_arimport_workflow',
                      'bika_batch_workflow',
                      'bika_cancellation_workflow',
                      'bika_duplicateanalysis_workflow',
                      'bika_inactive_workflow',
                      'bika_order_workflow',
                      'bika_publication_workflow',
                      'bika_referenceanalysis_workflow',
                      'bika_referencesample_workflow',
                      'bika_sample_workflow',
                      'bika_samplinground_workflow',
                      'bika_worksheet_workflow',
                      'sampleprep_simple',

                      # 'bika_arimports_workflow',
                      # 'bika_client_workflow',
                      # 'bika_one_state_workflow',
                      # 'bika_reject_analysis_workflow',
                      # 'bika_worksheetanalysis_workflow',

                      ]
    logger.info('Renaming guard expressions...')
    wtool = api.get_tool('portal_workflow')
    for wfid in bika_workflows:
        workflow = wtool.getWorkflowById(wfid)
        transitions = workflow.transitions
        for transid in transitions.objectIds():
            newguard = "python:here.guard_handler('{0}')".format(transid)
            transition = transitions[transid]
            guard = transition.getGuard()
            oldexpr = 'None'
            if guard:
                oldexpr = guard.expr.text if guard.expr else 'None'
            if oldexpr == newguard:
                continue
            guard.expr = Expression(newguard)
            transition.guard = guard
            msg = "Guard expression for '{0}.{1}' changed: {2} -> {3}".format(
                wfid, transid, oldexpr, newguard)
            logger.info(msg)


def fix_workflow_transitions(portal):
    logger.info('Fix workflow transitions...')
    inconsistences = {
        'bika_sample_workflow': {
            'sample_due': ['receive', 'reject'],
            'sample_received': ['expire', 'sample_prep', 'reject']
        }
    }
    wtool = api.get_tool('portal_workflow')
    for wfid, wfdef in inconsistences.items():
        workflow = wtool.getWorkflowById(wfid)
        for wfstatid, transitions in wfdef.items():
            msg = "Transitions for {0}.{1} set to: {2}"
            workflow.states[wfstatid].transitions = transitions
            logger.info(msg.format(wfid, wfstatid, ','.join(transitions)))

def remove_stale_states(portal):
    """Removes states from different workflows that are no longer used. It also
    removes the 'exit-transitions' from each state that points to the target
    state"""
    states = {
        'bika_analysis_workflow': ['rejected', ],
    }
    wtool = api.get_tool('portal_workflow')
    for wf_id, wf_states in states.items():
        # Look for the transition for which the end-state is wf_state
        trans_to_remove = list()
        workflow = wtool.getWorkflowById(wf_id)
        transitions = workflow.transitions
        for transid in transitions.objectIds():
            transition = transitions[transid]
            if transition.new_state_id in wf_states:
                trans_to_remove.append(transid)
        # Remove the transitions
        for trans_remove in trans_to_remove:
            workflow.transitions.deleteTransitions([trans_remove])

        # Now, remove the states
        workflow.states.deleteStates(wf_states)
