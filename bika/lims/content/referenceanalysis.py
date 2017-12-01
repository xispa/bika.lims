# -*- coding: utf-8 -*-

# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.
from AccessControl import ClassSecurityInfo

from DateTime import DateTime
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.public import *
from Products.CMFCore.utils import getToolByName
from bika.lims import deprecated
from bika.lims.config import PROJECTNAME, STD_TYPES
from bika.lims.content.abstractanalysis import AbstractAnalysis
from bika.lims.content.abstractanalysis import schema
from bika.lims.interfaces import IReferenceAnalysis
from bika.lims.subscribers import skip
from bika.lims.workflow import doActionFor
from plone.app.blob.field import BlobField
from zope.interface import implements

schema = schema.copy() + Schema((
    StringField(
        'ReferenceType',
        vocabulary=STD_TYPES,
    ),
    BlobField(
        'RetractedAnalysesPdfReport',
    ),
    StringField(
        'ReferenceAnalysesGroupID',
    )
))


class ReferenceAnalysis(AbstractAnalysis):
    implements(IReferenceAnalysis)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    @security.public
    def getSupplier(self):
        """ Returns the Supplier of the ReferenceSample this ReferenceAnalysis
        refers to
        """
        sample = self.getSample()
        if sample:
            return sample.aq_parent

    @security.public
    def getSupplierUID(self):
        supplier = self.getSupplier()
        if supplier:
            return supplier.UID()

    @security.public
    def getSample(self):
        """ Returns the ReferenceSample this ReferenceAnalysis refers to
        Delegates to self.aq_parent
        """
        return self.aq_parent

    @security.public
    def getDueDate(self):
        """Used to populate getDueDate index and metadata.
        This very simply returns the expiry date of the parent reference sample.
        """
        sample = self.getSample()
        if sample:
            return sample.getExpiryDate()

    @security.public
    def setResult(self, value):
        # Always update ResultCapture date when this field is modified
        self.setResultCaptureDate(DateTime())
        val = str(value).strip()
        self.getField('Result').set(self, val)

    def getReferenceResults(self):
        """
        It is used as metacolumn
        """
        return self.getSample().getReferenceResults()

    @security.public
    def getResultsRange(self):
        sample = self.getSample()
        if sample:
            return sample.getResultsRangeDict()

    def getAnalysisSpecs(self, specification=None):
        specs = self.getResultsRange()
        if specs and self.getKeyword() in specs:
            return specs

    def getInstrumentUID(self):
        """
        It is a metacolumn.
        Returns the same value as the service.
        """
        instrument = self.getInstrument()
        if not instrument:
            return None
        return instrument.UID()

    def getServiceDefaultInstrumentUID(self):
        """
        It is used as a metacolumn.
        Returns the default service's instrument UID
        """
        ins = self.getInstrument()
        if ins:
            return ins.UID()
        return ''

    def getServiceDefaultInstrumentTitle(self):
        """
        It is used as a metacolumn.
        Returns the default service's instrument UID
        """
        ins = self.getInstrument()
        if ins:
            return ins.Title()
        return ''

    def getServiceDefaultInstrumentURL(self):
        """
        It is used as a metacolumn.
        Returns the default service's instrument UID
        """
        ins = self.getInstrument()
        if ins:
            return ins.absolute_url_path()
        return ''

    def getDependencies(self, retracted=False):
        """It doesn't make sense for a ReferenceAnalysis to use
        dependencies, since them are only used in calculations for
        routine analyses
        """
        return []

    @deprecated("[1710] Reference Analyses do not support Interims")
    def setInterimFields(self, interims=None , **kwargs):
        pass

    @deprecated("[1710] Reference Analyses do not support Interims")
    def getInterimFields(self):
        return []

    @deprecated("[1710] Reference Analyses do not support Calculations")
    def setCalculation(self, calculation=None, **kwargs):
        pass

    @deprecated("[1710] Reference Analyses do not support Calculations")
    def getCalculation(self):
        return None

    @deprecated("[1710] Reference Analyses do not support Calculations")
    def getCalculationTitle(self):
        return None

    @deprecated("[1710] Reference Analyses do not support Calculations")
    def getCalculationUID(self):
        return None


registerType(ReferenceAnalysis, PROJECTNAME)
