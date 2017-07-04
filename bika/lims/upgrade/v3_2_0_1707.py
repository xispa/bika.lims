# This file is part of Bika LIMS
#
# Copyright 2011-2017 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.
from Acquisition import aq_inner
from Acquisition import aq_parent

from bika.lims import logger
from bika.lims.upgrade import upgradestep
from bika.lims.upgrade.utils import UpgradeUtils
from plone.api.portal import get_tool

from Products.CMFCore.Expression import Expression

product = 'bika.lims'
version = '3.2.0.1707'

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
                  'sampleprep_simple']


@upgradestep(product, version)
def upgrade(tool):
    portal = aq_parent(aq_inner(tool))
    ut = UpgradeUtils(portal)
    ufrom = ut.getInstalledVersion(product)
    if ut.isOlderVersion(product, version):
        logger.info("Skipping upgrade of {0}: {1} > {2}".format(
            product, ufrom, version))
        # The currently installed version is more recent than the target
        # version of this upgradestep
        return True

    logger.info("Upgrading {0}: {1} -> {2}".format(product, ufrom, version))

    # Fix workflows stuff
    fix_workflows(portal)

    logger.info("{0} upgraded to version {1}".format(product, version))
    return True


def fix_workflows(portal):
    # Rename all guard expressions to python:here.guard_handler('<action_id>')
    set_guard_expressions(portal)

    # Fix workflow transitions
    fix_workflow_transitions(portal)


def set_guard_expressions(portal):
    """Rename all guard expressions to python:here.guard_handler('<action_id>')
    """
    logger.info('Renaming guard expressions...')
    wtool = get_tool('portal_workflow')
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
            'sample_due':      ['receive', 'reject'],
            'sample_received': ['expire', 'sample_prep', 'reject']
        }
    }
    wtool = get_tool('portal_workflow')
    for wfid, wfdef in inconsistences.items():
        workflow = wtool.getWorkflowById(wfid)
        for wfstatid, transitions in wfdef.items():
            msg = "Transitions for {0}.{1} set to: {2}"
            workflow.states[wfstatid].transitions = transitions
            logger.info(msg.format(wfid, wfstatid, ','.join(transitions)))
