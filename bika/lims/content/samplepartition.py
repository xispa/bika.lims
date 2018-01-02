# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.CORE
#
# Copyright 2018 by it's authors.
# Some rights reserved. See LICENSE.rst, CONTRIBUTORS.rst.


from datetime import timedelta
from AccessControl import ClassSecurityInfo
from Products.ATContentTypes.lib.historyaware import HistoryAwareMixin
from Products.ATContentTypes.utils import DT2dt, dt2DT
from Products.Archetypes.public import *
from Products.CMFPlone.utils import safe_unicode
from zope.interface import implements
from bika.lims.browser.fields import DurationField
from bika.lims.browser.fields import UIDReferenceField
from bika.lims.config import PROJECTNAME
from bika.lims.content.bikaschema import BikaSchema
from bika.lims.interfaces import ISamplePartition, ISamplePrepWorkflow
from bika.lims.workflow import getTransitionDate
from DateTime import DateTime

schema = BikaSchema.copy() + Schema((
    ReferenceField('Container',
        allowed_types=('Container',),
        relationship='SamplePartitionContainer',
        required=1,
        multiValued=0,
    ),
    ReferenceField('Preservation',
        allowed_types=('Preservation',),
        relationship='SamplePartitionPreservation',
        required=0,
        multiValued=0,
    ),
    BooleanField('Separate',
        default=False
    ),
    UIDReferenceField('Analyses',
        allowed_types=('Analysis',),
        required=0,
        multiValued=1,
    ),
    DateTimeField('DatePreserved',
    ),
    StringField('Preserver',
        searchable=True
    ),
    DurationField('RetentionPeriod',
    ),
    ComputedField('DisposalDate',
        expression = 'context.disposal_date()',
        widget = ComputedWidget(
            visible=False,
        ),
    ),
)
)

schema['title'].required = False


class SamplePartition(BaseContent, HistoryAwareMixin):
    implements(ISamplePartition, ISamplePrepWorkflow)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    _at_rename_after_creation = True

    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

    def _getCatalogTool(self):
        from bika.lims.catalog import getCatalog
        return getCatalog(self)

    def Title(self):
        """ Return the Sample ID as title """
        return safe_unicode(self.getId()).encode('utf-8')

    def getSample(self):
        """Returns the Sample the current Sample Partition belongs to
        """
        return self.aq_parent

    def getSiblings(self):
        """Returns the siblings of this Sample Partition. This is the Sample
        Partitions that belongs to the same Sample as this one.
        If no siblings found, returns None

        :returns: a list of SamplePartitions associated to the same Sample
        :rtype: list
        """
        sample = self.getSample()
        if sample:
            partitions = sample.getSamplePartitions()
            siblings = [sp for sp in partitions if sp.UID() != sp.UID()]
            return siblings

    @security.public
    def current_date(self):
        """ return current date """
        return DateTime()

    @security.public
    def disposal_date(self):
        """ return disposal date """

        DateSampled = self.getDateSampled()

        # fallback to sampletype retention period
        st_retention = self.aq_parent.getSampleType().getRetentionPeriod()

        # but prefer retention period from preservation
        pres = self.getPreservation()
        pres_retention = pres and pres.getRetentionPeriod() or None

        rp = pres_retention and pres_retention or None
        rp = rp or st_retention

        td = timedelta(
            days='days' in rp and int(rp['days']) or 0,
            hours='hours' in rp and int(rp['hours']) or 0,
            minutes='minutes' in rp and int(rp['minutes']) or 0)

        dis_date = DateSampled and dt2DT(DT2dt(DateSampled) + td) or None
        return dis_date

    @security.public
    def getDateDisposed(self):
        """Returns the date when this Sample Partition was disposed. If the
        Sample Partition hasn't been disposed, returns None

        :returns: Date when this Sample Partition was disposed
        :rtype: DateTime
        """
        return getTransitionDate(self, 'dispose', return_as_datetime=True)

    @security.public
    def getDateExpired(self):
        """Returns the date when this Sample Partition expired. If the Sample
        Partition didn't expire, returns None

        :returns: Date when this Sample Partition expired
        :rtype: DateTime
        """
        return getTransitionDate(self, 'expire', return_as_datetime=True)


registerType(SamplePartition, PROJECTNAME)
