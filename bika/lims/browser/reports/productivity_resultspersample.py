from Products.CMFCore.utils import getToolByName
from bika.lims.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import bikaMessageFactory as _
from bika.lims.utils import t
from bika.lims.browser.reports.selection_macros import SelectionMacrosView
from bika.lims.utils import formatDateQuery, formatDateParms, logged_in_client
from plone.app.layout.globals.interfaces import IViewView
from zope.interface import implements
import csv
import StringIO
import datetime


class Report(BrowserView):
    implements(IViewView)
    template = ViewPageTemplateFile("templates/report_out.pt")

    def __init__(self, context, request, report=None):
        super(Report, self).__init__(context, request)
        self.report = report
        self.selection_macros = SelectionMacrosView(self.context, self.request)

    def __call__(self):
        # get all the data into datalines
        pc = getToolByName(self.context, 'portal_catalog')
        self.report_content = {}
        parm_lines = {}
        parms = []
        headings = {}
        headings['header'] = _("Analyses result per sample")
        count_all = 0
        query = {'portal_type': 'Sample', 'sort_on': 'created'}
        client_title = None
        # Getting the query filters
        val = self.selection_macros.parse_client(self.request)
        if val:
            query[val['contentFilter'][0]] = val['contentFilter'][1]
            parms.append(val['parms'])

        val = self.selection_macros.parse_sampletype(self.request)
        if val:
            query[val['contentFilter'][0]] = val['contentFilter'][1]
            parms.append(val['parms'])

        val = self.selection_macros.parse_analysisservice(self.request)
        allowd_services_uids = []
        if val:
            # query[val['contentFilter'][0]] = val['contentFilter'][1]
            # Lets get the analysis services uids list only.
            allowd_services_uids = val['contentFilter'][1]
            parms.append(val['parms'])

        val = self.selection_macros.parse_daterange(self.request,
                                                    'created',
                                                    'Created')
        if val:
            query[val['contentFilter'][0]] = val['contentFilter'][1]
            parms.append(val['parms'])

        formats = {'columns': 8,
                   'col_heads': [
                        _('Request ID'),
                        _('Client reference'),
                        _('Client Sample ID'),
                        _('Date'),
                        _('Sample type'),
                        _('Storage location'),
                        _('Analysis'),
                        _('Result')], }
        # and now lets do the actual report lines
        datalines = []
        for sample_b in pc(query):
            sample = sample_b.getObject()
            analyses = []
            for ar in sample.getAnalysisRequests():
                analyses += list(ar.getAnalyses(full_objects=True))
                for analysis in analyses:
                    if allowd_services_uids == [] or analysis.getServiceUID() in allowd_services_uids:
                        dataline = []
                        ars = sample.getAnalysisRequests()
                        ars_ids = ''
                        # Request ID
                        for ar in ars:
                            ars_ids = ars_ids + ar.getId() + ' '
                        dataitem = {
                            'value': ars_ids}
                        dataline.append(dataitem)
                        # Client reference
                        dataline.append({'value':  sample.getClientSampleID()})
                        # Client Sample ID
                        dataline.append(
                            {'value':  sample.getClientReference()})
                        # Date
                        date = sample.getDateSampled() if\
                            sample.getDateSampled() else\
                            sample.getDateReceived()
                        dataitem = {
                            'value': self.ulocalized_time(date)}
                        dataline.append(dataitem)
                        # Sample type
                        dataitem = {'value': sample.getSampleType().Title()}
                        dataline.append(dataitem)
                        # Storage location
                        location = sample.getStorageLocation().Title()\
                            if sample.getStorageLocation() else ''
                        dataitem = {'value': location}
                        dataline.append(dataitem)
                        # Analysis
                        dataitem = {'value': analysis.Title()}
                        dataline.append(dataitem)
                        # Result
                        dataitem = {'value': analysis.getFormattedResult()}
                        dataline.append(dataitem)
                        count_all += 1
                        datalines.append(dataline)

        # footer data
        footlines = []
        footline = []
        footitem = {'value': _('Total'),
                    'class': 'total_label'}
        footline.append(footitem)
        footitem = {'value': count_all}
        footline.append(footitem)
        footlines.append(footline)

        self.report_content = {
            'headings': headings,
            'parms': parms,
            'formats': formats,
            'datalines': datalines,
            'footings': footlines}

        if self.request.get('output_format', '') == 'CSV':
            fieldnames = [
                _('Request ID'),
                _('Client reference'),
                _('Client Sample ID'),
                _('Date'),
                _('Sample type'),
                _('Storage location'),
                _('Analysis'),
                _('Result'),
            ]
            output = StringIO.StringIO()
            dw = csv.DictWriter(output, extrasaction='ignore',
                                fieldnames=fieldnames)
            dw.writerow(dict((fn, fn) for fn in fieldnames))
            for row in datalines:
                dw.writerow({
                    'Request ID': row[0]['value'],
                    'Client reference': row[1]['value'],
                    'Client sample ID': row[2]['value'],
                    'Date': row[3]['value'],
                    'Sample type': row[4]['value'],
                    'Storage location': row[5]['value'],
                    'Analysis': row[6]['value'],
                    'Result': row[7]['value'],
                })
            report_data = output.getvalue()
            output.close()
            date = datetime.datetime.now().strftime("%Y%m%d%H%M")
            setheader = self.request.RESPONSE.setHeader
            setheader('Content-Type', 'text/csv')
            setheader("Content-Disposition",
                      "attachment;filename=\"analysisresultpersample_%s.csv\"" % date)
            self.request.RESPONSE.write(report_data)
        else:
            return {'report_title': t(headings['header']),
                    'report_data': self.template()}