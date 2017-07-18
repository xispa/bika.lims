from AccessControl import ClassSecurityInfo
from bika.lims.workflow import getAllowedTransitions
from plone.jsonapi.core import router
from plone.jsonapi.core.interfaces import IRouteProvider
from Products.CMFCore.utils import getToolByName
from zExceptions import BadRequest
from zope import interface
import json
import plone


class allowedTransitionsFor(object):
    interface.implements(IRouteProvider)

    def initialize(self, context, request):
        self.context = context
        self.request = request

    @property
    def routes(self):
        return (
            ("/allowedTransitionsFor", "allowedTransitionsFor",
                self.allowed_transitions_for,
                dict(methods=['GET', 'POST'])),
            ("/allowedTransitionsFor_many", "allowedTransitionsFor_many",
                self.allowed_transitions_for_many,
                dict(methods=['GET', 'POST'])),
        )

    def allowed_transitions_for(self, context, request):
        """/@@API/allowedTransitionsFor: Returns a list with the ids of the
        transitions that can be applied to the object for the uid passed in

        Required parameters:
            - uid: the uid of the object to get the allowed transitions
        """
        plone.protect.CheckAuthenticator(request)
        obj = None
        if request.get('uid', ''):
            uid = request['uid']
            uc = getToolByName(context, 'uid_catalog')
            obj = uc(UID=uid)
            if len(obj) != 1:
                obj = None
            else:
                obj = obj[0].getObject()

        if not obj and request.get('obj_path', ''):
            obj_path = request['obj_path']
            site_path = context.portal_url.getPortalObject().getPhysicalPath()
            if site_path and isinstance(site_path, basestring):
                site_path = site_path if site_path.startswith(
                    '/') else '/' + site_path
                obj = context.restrictedTraverse(site_path + obj_path)
            elif site_path and len(site_path) > 1:
                site_path = site_path[1]
                site_path = site_path if site_path.startswith(
                    '/') else '/' + site_path
                obj = context.restrictedTraverse(site_path + obj_path)

        ret = {
            "url": router.url_for("allowedTransitionsFor", force_external=True),
            "success": False,
            "error": True,
            "transitions": []
        }
        if obj:
            ret['transitions'] = getAllowedTransitions(obj)
            ret['success'] = True
            ret['error'] = False
        return ret


    def allowed_transitions_for_many(self, context, request):
        """/@@API/allowedTransitionsFor_many: Returns a list of dictionaries. Each
        dictionary has the following structure:
            {'uid': <uid_object_passed_in>,
             'transitions': [<transtion_id_1>, <transition_id2>]}

        Required parameters:
            - uid: uids of the objects to get the allowed transitions from
        """
        uc = getToolByName(context, 'uid_catalog')
        uids = json.loads(request.get('uid', '[]'))
        if not uids:
            raise BadRequest("No object UID specified in request")

        allowed_transitions = []
        try:
            objs = uc(UID=uids)
            for obj in objs:
                obj = obj.getObject()
                transitions = getAllowedTransitions(obj)
                allowed_transitions.append({'uid': obj.UID(),
                                            'transitions': transitions})
        except Exception as e:
            msg = "Cannot get allowed transitions: {0}".format( e.message)
            raise BadRequest(msg)

        ret = {
            "url": router.url_for("allowedTransitionsFor_many",
                                  force_external=True),
            "success": True,
            "error": False,
            "transitions": allowed_transitions
        }
        return ret
