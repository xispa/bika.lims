from plone.theme.interfaces import IDefaultPloneLayer
from zope.interface import Interface

class IBikaLIMS(Interface):
    """Marker interface that defines a Zope 3 browser layer.
       If you need to register a viewlet only for the
       "bika" theme, this interface must be its layer
    """

class IClientFolder(Interface):
    """Client folder"""

class IClient(Interface):
    """Client"""

class IBatchFolder(Interface):
    """Batch folder"""

class IBatch(Interface):
    """Batch"""

class IBatchLabels(Interface):
    """Batch label"""

class IAnalysisRequest(Interface):
    """Analysis Request"""

class IAnalysisRequestAddView(Interface):
    """ AR Add view """

class IAnalysisRequestsFolder(Interface):
    """AnalysisRequests Folder"""

class IAnalysis(Interface):
    """Analysis"""

class IAnalysisSpec(Interface):
    """Analysis Specs"""

class IDuplicateAnalysis(Interface):
    """DuplicateAnalysis"""

class IQueryFolder(Interface):
    """Queries Folder"""

class IQuery(Interface):
    """Query collection object"""

class IReferenceAnalysis(Interface):
    """Reference Analyses """

class IReportFolder(Interface):
    """Report folder"""

class ISample(Interface):
    """Sample"""

class ISampleCondition(Interface):
    """Sample Condition"""

class ISampleConditions(Interface):
    """Sample Conditions"""

class ISampleMatrix(Interface):
    """Sample Matrix"""

class ISampleMatrices(Interface):
    """Sample Matrices"""

class ISamplePartition(Interface):
    """Sample"""

class ISamplesFolder(Interface):
    """Samples Folder"""

class ISamplingDeviation(Interface):
    """Sampling Deviation"""

class ISamplingDeviations(Interface):
    """Sampling Deviations"""

class IWorksheetFolder(Interface):
    """WorksheetFolder"""

class IWorksheet(Interface):
    """Worksheet"""

class IReferenceSample(Interface):
    """Reference Sample"""

class IReferenceSamplesFolder(Interface):
    """Reference Samples Folder"""

class IReportsFolder(Interface):
    """Reports Folder"""

class IInvoice(Interface):
    """Invoice"""

class IInvoiceBatch(Interface):
    """Invoice Batch"""

class IInvoiceFolder(Interface):
    """Invoices Folder"""

class IHaveNoBreadCrumbs(Interface):
    """Items which do not display breadcrumbs"""

class IIdServer(Interface):
    """ Interface for ID server """
    def generate_id(self, portal_type, batch_size = None):
        """ Generate a new id for 'portal_type' """

class IBikaSetup(Interface):
    ""

class IAnalysisCategory(Interface):
    ""
class IAnalysisCategories(Interface):
    ""
class IAnalysisService(Interface):
    ""
class IAnalysisServices(Interface):
    ""
class IAttachmentTypes(Interface):
    ""
class ICalculation(Interface):
    ""
class ICalculations(Interface):
    ""
class IContacts(Interface):
    ""
class IContact(Interface):
    ""
class IDepartments(Interface):
    ""
class IContainers(Interface):
    ""
class IContainerTypes(Interface):
    ""
class IInstrument(Interface):
    ""
class IInstruments(Interface):
    ""
class IInstrumentType(Interface):
    ""
class IInstrumentTypes(Interface):
    ""
class IAnalysisSpecs(Interface):
    ""
class IAnalysisProfiles(Interface):
    ""
class IARTemplates(Interface):
    ""
class ILabContacts(Interface):
    ""
class ILabContact(Interface):
    ""
class IManufacturer(Interface):
    ""
class IManufacturers(Interface):
    ""
class IMethods(Interface):
    ""
class ILabProducts(Interface):
    ""
class ISamplePoint(Interface):
    ""
class ISamplePoints(Interface):
    ""
class ISampleType(Interface):
    ""
class ISampleTypes(Interface):
    ""
class ISupplier(Interface):
    ""
class ISuppliers(Interface):
    ""
class IPreservations(Interface):
    ""
class IReferenceDefinitions(Interface):
    ""
class IWorksheetTemplates(Interface):
    ""

class IBikaCatalog(Interface):
    "Marker interface for custom catalog"

class IBikaAnalysisCatalog(Interface):
    "Marker interface for custom catalog"

class IBikaSetupCatalog(Interface):
    "Marker interface for custom catalog"


class IDisplayListVocabulary(Interface):
    """Make vocabulary from catalog query.
    Return a DisplayList.
    kwargs are added to contentFilter.
    """
    def __call__(**kwargs):
        """
        """


class IWidgetVisibility(Interface):
    """Adapter to modify the default list of fields to show on each view.
    Returns a dictionary, the keys are the keys of any field's "visibility"
    property dicts found in the schema, and the values are field names.
        """

    def __call__():
        """
        """


class IAnalysisRangeAlerts(Interface):
    """ Adapter to retrieve the out-of-range values for analyses results.
    Returns a dictionary: the keys are the Analyses UIDs and the values are
    another dictionary with the keys 'result', 'icon', 'alertmessage'
    """

    def getOutOfRangeAlerts(self):
        """
        """

class ISetupDataImporter(Interface):
    """ISetupDataImporter adapters are responsible for importing sections of
    the load_setup_data xlsx spreadsheets."""
