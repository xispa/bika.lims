from Products.CMFCore.utils import getToolByName


def deactivate(obj):
    """Returns true if the Analysis Category passed in can be deactivated.

    Returns True if the current user has enough privileges to deactivate the
    Analysis Category passed in and if the latter doesn't have any Analysis
    Service associated. Otherwise, returns false.

    :param obj: AnalysisCategory the deactivate transition must be evaluated
    :type obj: AnalysisCategory
    :returns: True or False
    :rtype: bool
    """
    bsc = getToolByName(obj, 'bika_setup_catalog')
    services = bsc(portal_type='AnalysisService', getCategoryUID=obj.UID())
    return services.length == 0
