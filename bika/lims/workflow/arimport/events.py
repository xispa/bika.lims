from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

from bika.lims import logger
from bika.lims.utils.analysis import create_analysis
from bika.lims.workflow import changeWorkflowState
from bika.lims.workflow import doActionFor
from bika.lims.workflow import getCurrentState
from bika.lims.workflow import isBasicTransitionAllowed
from bika.lims.workflow import wasTransitionPerformed
from bika.lims.workflow import skip

# TODO Workflow - ARImport. Full review


def before_validate(obj):
    """This function transposes values from the provided file into the
    ARImport object's fields, and checks for invalid values.

    If errors are found:
        - Validation transition is aborted.
        - Errors are stored on object and displayed to user.

    """
    # Re-set the errors on this ARImport each time validation is attempted.
    # When errors are detected they are immediately appended to this field.
    obj.setErrors([])
    obj.validate_headers()
    obj.validate_samples()

    if obj.getErrors():
        addStatusMessage(obj.REQUEST, _p('Validation errors.'), 'error')
        transaction.commit()
        obj.REQUEST.response.write(
            '<script>document.location.href="%s/edit"</script>' % (
                obj.absolute_url()))
    obj.REQUEST.response.write(
        '<script>document.location.href="%s/view"</script>' % (
            obj.absolute_url()))


def after_import(obj):
    obj.workflow_script_import()
