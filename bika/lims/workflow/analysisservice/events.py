# TODO Workflow - AnalysisService. Full review


def after_activate(obj):
    return obj.workflow_script_activate()


def after_deactivate(obj):
    return obj.workflow_script_deactivate()
