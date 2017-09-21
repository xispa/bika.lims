# -*- coding: utf-8 -*-
#
# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

import re

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode


from plone import api
from plone.protect import CheckAuthenticator

from bika.lims import PMF
from bika.lims import logger
from bika.lims.browser import BrowserView
from bika.lims.content.contact import Contact
from bika.lims.content.labcontact import LabContact
from bika.lims import bikaMessageFactory as _


class AnonymizerView(BrowserView):
    """
    """

    def __call__(self):
        request = self.request
        self.anonymize_lab_contacts()
        return "Anonymizing..."


    def anonymize_lab_contacts(self):
        return True