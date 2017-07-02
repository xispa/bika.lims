## Script (Python) "guard_handler"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=transition_id=None
##title=guard_handler Script
from bika.lims.workflow import GuardHandler
GuardHandler(context, transition_id)
