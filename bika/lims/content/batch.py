# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from AccessControl import ClassSecurityInfo
from bika.lims import bikaMessageFactory as _
from bika.lims.utils import t
from bika.lims.config import PROJECTNAME
from bika.lims.content.bikaschema import BikaFolderSchema
from bika.lims.interfaces import IBatch, IClient
from bika.lims.workflow import skip, BatchState, StateFlow, getCurrentState,\
    CancellationState
from bika.lims.browser.widgets import DateTimeWidget
from plone import api
from plone.app.folder.folder import ATFolder
from Products.Archetypes.public import *
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope.interface import implements
from bika.lims.permissions import EditBatch
from plone.indexer import indexer
from Products.Archetypes.references import HoldingReference
from Products.ATExtensions.ateapi import RecordsField
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.browser.widgets import RecordsWidget as bikaRecordsWidget

from bika.lims.browser.widgets import ReferenceWidget
from zope.component import getAdapters
from bika.lims.interfaces import IBatchSearchableText


class InheritedObjectsUIField(RecordsField):

    """XXX bika.lims.RecordsWidget doesn't cater for multiValued fields
    InheritedObjectsUI is a RecordsField because we want the RecordsWidget,
    but the values are stored in ReferenceField 'InheritedObjects'
    """

    def get(self, instance, **kwargs):
        # Return the formatted contents of InheritedObjects field.
        field = instance.Schema()['InheritedObjects']
        value = field.get(instance)
        return [{'Title': x.Title(),
                 'ObjectID': x.id,
                 'Description': x.Description()} for x in value]

    def getRaw(self, instance, **kwargs):
        # Return the formatted contents of InheritedObjects field.
        field = instance.Schema()['InheritedObjects']
        value = field.get(instance)
        return [{'Title': x.Title(),
                 'ObjectID': x.id,
                 'Description': x.Description()} for x in value]

    def set(self, instance, value, **kwargs):
        _field = instance.Schema().getField('InheritedObjects')
        uids = []
        if value:
            bc = getToolByName(instance, 'bika_catalog')
            ids = [x['ObjectID'] for x in value]
            if ids:
                proxies = bc(id=ids)
                if proxies:
                    uids = [x.UID for x in proxies]
        RecordsField.set(self, instance, value)
        return _field.set(instance, uids)


schema = BikaFolderSchema.copy() + Schema((
    StringField(
        'BatchID',
        required=False,
        validators=('uniquefieldvalidator',),
        widget=StringWidget(
            visible=False,
            label=_("Batch ID"),
        )
    ),
    ReferenceField(
        'Client',
        required=0,
        allowed_types=('Client',),
        relationship='BatchClient',
        widget=ReferenceWidget(
            label=_("Client"),
            size=30,
            visible=True,
            base_query={'inactive_state': 'active'},
            showOn=True,
            colModel=[{'columnName': 'UID', 'hidden': True},
                      {'columnName': 'Title', 'width': '60', 'label': _('Title')},
                      {'columnName': 'ClientID', 'width': '20', 'label': _('Client ID')}
                     ],
      ),
    ),
    StringField(
        'ClientBatchID',
        required=0,
        widget=StringWidget(
            label=_("Client Batch ID")
        )
    ),
    DateTimeField(
        'BatchDate',
        required=False,
        widget=DateTimeWidget(
            label=_('Date'),
        ),
    ),
    LinesField(
        'BatchLabels',
        vocabulary="BatchLabelVocabulary",
        accessor="getLabelNames",
        widget=MultiSelectionWidget(
            label=_("Batch Labels"),
            format="checkbox",
        )
    ),
    TextField(
        'Remarks',
        default_content_type='text/x-web-intelligent',
        allowable_content_types=('text/plain', ),
        default_output_type="text/plain",
        widget=TextAreaWidget(
            macro="bika_widgets/remarks",
            label=_('Remarks'),
            append_only=True,
        )
    ),
    ReferenceField(
        'InheritedObjects',
        required=0,
        multiValued=True,
        allowed_types=('AnalysisRequest'),  # batches are expanded on save
        referenceClass = HoldingReference,
        relationship = 'BatchInheritedObjects',
        widget=ReferenceWidget(
            visible=False,
        ),
    ),
    InheritedObjectsUIField(
        'InheritedObjectsUI',
        required=False,
        type='InheritedObjects',
        subfields=('Title', 'ObjectID', 'Description'),
        subfield_sizes = {'Title': 25,
                          'ObjectID': 25,
                          'Description': 50,
                          },
        subfield_labels = {'Title': _('Title'),
                           'ObjectID': _('Object ID'),
                           'Description': _('Description')
                           },
        widget = bikaRecordsWidget(
            label=_("Inherit From"),
            description=_(
                "Include all analysis requests belonging to the selected objects."),
            innerJoin="<br/>",
            combogrid_options={
                'Title': {
                    'colModel': [
                        {'columnName': 'Title', 'width': '25',
                         'label': _('Title'), 'align': 'left'},
                        {'columnName': 'ObjectID', 'width': '25',
                         'label': _('Object ID'), 'align': 'left'},
                        {'columnName': 'Description', 'width': '50',
                         'label': _('Description'), 'align': 'left'},
                        {'columnName': 'UID', 'hidden': True},
                    ],
                    'url': 'getAnalysisContainers',
                    'showOn': False,
                    'width': '600px'
                },
                'ObjectID': {
                    'colModel': [
                        {'columnName': 'Title', 'width': '25',
                         'label': _('Title'), 'align': 'left'},
                        {'columnName': 'ObjectID', 'width': '25',
                         'label': _('Object ID'), 'align': 'left'},
                        {'columnName': 'Description', 'width': '50',
                         'label': _('Description'), 'align': 'left'},
                        {'columnName': 'UID', 'hidden': True},
                    ],
                    'url': 'getAnalysisContainers',
                    'showOn': False,
                    'width': '600px'
                },
            },
        ),
    ),
)
)

schema['BatchID'].widget.description = _("If no value is entered, the Batch ID"
                                         " will be auto-generated.")
schema['title'].required = False
schema['title'].widget.visible = True
schema['title'].widget.description = _("If no Title value is entered,"
                                       " the Batch ID will be used.")
schema['description'].required = False
schema['description'].widget.visible = True

schema.moveField('ClientBatchID', before='description')
schema.moveField('BatchID', before='description')
schema.moveField('title', before='description')
schema.moveField('Client', after='title')


class Batch(ATFolder):
    implements(IBatch)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    _at_rename_after_creation = True

    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

    def Title(self):
        """ Return the Batch ID if title is not defined """
        titlefield = self.Schema().getField('title')
        if titlefield.widget.visible:
            return safe_unicode(self.title).encode('utf-8')
        else:
            return safe_unicode(self.id).encode('utf-8')

    def _getCatalogTool(self):
        from bika.lims.catalog import getCatalog
        return getCatalog(self)

    def getClient(self):
        """ Retrieves the Client for which the current Batch is attached to
            Tries to retrieve the Client from the Schema property, but if not
            found, searches for linked ARs and retrieve the Client from the
            first one. If the Batch has no client, returns None.
        """
        client = self.Schema().getField('Client').get(self)
        if client:
            return client
        client = self.aq_parent
        if IClient.providedBy(client):
            return client

    def getClientTitle(self):
        client = self.getClient()
        if client:
            return client.Title()
        return ""

    def getContactTitle(self):
        return ""

    def getProfilesTitle(self):
        return ""

    def getAnalysisService(self):
        analyses = set()
        for ar in self.getAnalysisRequests():
            for an in ar.getAnalyses():
                analyses.add(an)
        value = []
        for analysis in analyses:
            val = analysis.Title
            if val not in value:
                value.append(val)
        return list(value)

    def getAnalysts(self):
        analyses = []
        for ar in self.getAnalysisRequests():
            analyses += list(ar.getAnalyses(full_objects=True))
        value = []
        for analysis in analyses:
            val = analysis.getAnalyst()
            if val not in value:
                value.append(val)
        return value

    security.declarePublic('getBatchID')

    def getBatchID(self):
        if self.BatchID:
            return self.BatchID
        if self.checkCreationFlag():
            return self.BatchID
        return self.getId()

    def BatchLabelVocabulary(self):
        """ return all batch labels """
        bsc = getToolByName(self, 'bika_setup_catalog')
        ret = []
        for p in bsc(portal_type='BatchLabel',
                     inactive_state='active',
                     sort_on='sortable_title'):
            ret.append((p.UID, p.Title))
        return DisplayList(ret)

    def getAnalysisRequestsBrains(self, **kwargs):
        """ Return all the Analysis Requests brains linked to the Batch
        kargs are passed directly to the catalog.
        """
        kwargs['getBatchUID'] = self.UID()
        catalog = getToolByName(self, CATALOG_ANALYSIS_REQUEST_LISTING)
        brains = catalog(kwargs)
        return brains

    def getAnalysisRequests(self, **kwargs):
        """ Return all the Analysis Requests objects linked to the Batch
        kargs are passed directly to the catalog.
        """
        brains = self.getAnalysisRequestsBrains(**kwargs)
        return [b.getObject() for b in brains]

    def isOpen(self):
        """ Returns true if the Batch is in 'open' state
        """
        revstatus = getCurrentState(self, StateFlow.review)
        canstatus = getCurrentState(self, StateFlow.cancellation)
        return revstatus == BatchState.open \
            and canstatus == CancellationState.active

    def getLabelNames(self):
        uc = getToolByName(self, 'uid_catalog')
        uids = [uid for uid in self.Schema().getField('BatchLabels').get(self)]
        labels = [label.getObject().title for label in uc(UID=uids)]
        return labels

    def SearchableText(self):
        """
        Override searchable text logic based on the requirements.

        This method constructs a text blob which contains all full-text
        searchable text for this content item.
        https://docs.plone.org/develop/plone/searching_and_indexing/indexing.html#full-text-searching

        In some cases we may want to override plain_text_fields variable.
        To do this, an adapter must be added (providing
        bika.lims.interfaces.IBatchSearchableText) for that content type.
        """

        # Speed up string concatenation ops by using a buffer
        entries = []

        # plain text fields we index from ourselves,
        # a list of accessor methods of the class
        plain_text_fields = ("BatchID", "ClientBatchID")

        # Checking if an adapter exists. If yes, we will
        # get plain_text_fields from adapters.
        for name, adapter in getAdapters((self,), IBatchSearchableText):
            entries += adapter.get_plain_text_fields()

        def read(accessor):
            """
            Call a class accessor method to give a value for certain Archetypes
            field.
            """
            try:
                value = accessor()
            except:
                value = ""

            if value is None:
                value = ""

            return value

        # Concatenate plain text fields as they are
        for f in plain_text_fields:
            accessor = getattr(self, f)
            value = read(accessor)
            entries.append(value)

        # Plone accessor methods assume utf-8
        def convertToUTF8(text):
            if type(text) == unicode:
                return text.encode("utf-8")
            return text

        entries = [convertToUTF8(entry) for entry in entries]
        # Concatenate all strings to one text blob
        return " ".join(entries)

registerType(Batch, PROJECTNAME)


@indexer(IBatch)
def BatchDate(instance):
    return instance.Schema().getField('BatchDate').get(instance)
