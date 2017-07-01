from DateTime import DateTime

# TODO Workflow - SupplyOrder. Full review


def after_dispatch(obj):
    obj.setDateDispatched(DateTime())
