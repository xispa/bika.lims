# coding=utf-8
from plone.app.contentmenu.menu import WorkflowMenu as BaseClass


class WorkflowMenu(BaseClass):

    def getMenuItems(self, context, request):
        """Overrides the workflow actions menu displayed top right in the
        object's view. Displays the current state of the object, as well as a
        list with the actions that can be performed.
        The option "Advanced.." is not displayed and the list is populated with
        all allowed transitions for the object.
        """
        results = super(WorkflowMenu, self).getMenuItems(context, request)
        # Remove status history menu item ('Advanced...')
        results = [r for r in results
            if not r['action'].endswith('/content_status_history')]
        return results
