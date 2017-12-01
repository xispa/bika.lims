from bika.lims import logger
from bika.lims import api
from Products.CMFCore.Expression import Expression
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.config import PROJECTNAME as product
from bika.lims.upgrade import upgradestep
from bika.lims.upgrade.utils import UpgradeUtils

def fix_workflows(portal):
    # Rename all guard expressions to python:here.guard_handler('<action_id>')
    set_guard_expressions(portal)

    # Fix workflow transitions
    fix_workflow_transitions(portal)


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