from bika.lims.workflow import doActionFor

# TODO Workflow - SamplingRound. Full review


def after_cancel(obj):
    """
    When the round is cancelled, all its associated Samples and ARs are
    cancelled by the system.
    """
    # deactivate all Samples from this SamplingRound. Note cancelling a Sample
    # will also cancel its AnalysisRequests
    analysis_requests = obj.getAnalysisRequests()
    for ar in analysis_requests:
        ar_obj = ar.getObject()
        sample = ar_obj.getSample()
        doActionFor(ar_obj, 'cancel')
