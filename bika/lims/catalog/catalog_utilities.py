# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

import copy
from Products.CMFCore.utils import getToolByName
# Bika LIMS imports
from bika.lims import logger
from bika.lims.catalog.analysisrequest_catalog import\
    bika_catalog_analysisrequest_listing_definition
from bika.lims.catalog.analysis_catalog import \
    bika_catalog_analysis_listing_definition
from bika.lims.catalog.autoimportlogs_catalog import \
    bika_catalog_autoimportlogs_listing_definition
from bika.lims.catalog.worksheet_catalog import \
    bika_catalog_worksheet_listing_definition
import transaction
import traceback


def getCatalogDefinitions():
    """
    Returns a dictionary with catalogs definitions.
    """
    final = {}
    analysis_request = bika_catalog_analysisrequest_listing_definition
    analysis = bika_catalog_analysis_listing_definition
    autoimportlogs = bika_catalog_autoimportlogs_listing_definition
    worksheet = bika_catalog_worksheet_listing_definition
    # Merging the catalogs
    final.update(analysis_request)
    final.update(analysis)
    final.update(autoimportlogs)
    final.update(worksheet)
    return final


def getCatalog(instance, field='UID'):
    """
    Returns the catalog that stores objects of instance passed in type.
    If an object is indexed by more than one catalog, the first match
    will be returned.

    :param instance: A single object
    :type instance: ATContentType
    :returns: The first catalog that stores the type of object passed in
    """
    uid = instance.UID()
    if 'workflow_skiplist' in instance.REQUEST and \
        [x for x in instance.REQUEST['workflow_skiplist']
         if x.find(uid) > -1]:
        return None
    else:
        # grab the first catalog we are indexed in.
        # we're only indexed in one.
        at = getToolByName(instance, 'archetype_tool')
        plone = instance.portal_url.getPortalObject()
        catalog_name = instance.portal_type in at.catalog_map \
            and at.catalog_map[instance.portal_type][0] or 'portal_catalog'
        catalog = getToolByName(plone, catalog_name)
        return catalog

def setup_catalogs(
        portal, catalogs_definition={},
        force_reindex=False, catalogs_extension={}):
    """
    Setup the given catalogs. Redefines the map between content types and
    catalogs and then checks the indexes and metacolumns, if one index/column
    doesn't exist in the catalog_definition any more it will be
    removed, otherwise, if a new index/column is found, it will be created.

    :param portal: The Plone's Portal object
    :param catalogs_definition: a dictionary with the following structure
        {
            CATALOG_ID: {
                'types':   ['ContentType', ...],
                'indexes': {
                    'UID': 'FieldIndex',
                    ...
                },
                'columns': [
                    'Title',
                    ...
                ]
            }
        }
    :type catalogs_definition: dict
    :param force_reindex: Force to reindex the catalogs even if there's no need
    :type force_reindex: bool
    :param catalog_extensions: An extension for the primary catalogs definition
        Same dict structure as param catalogs_definition. Allows to add
        columns and indexes required by Bika-specific add-ons.
    :type catalog_extensions: dict
    """
    # This dictionary will contain the different modifications to carry on
    # for each catalog.
    # {'id_catalog': {
    #       new_indexes:[], new_columns:[], removal_types:[], added_types:[]}
    catalog_modifications = {}
    # If not given catalogs_definition, use the LIMS one
    if not catalogs_definition:
        catalogs_definition = getCatalogDefinitions()
    #
    # # Merge the catalogs definition of the extension with the primary
    # # catalog definition
    # definition = _merge_catalog_definitions(catalogs_definition,
    #                                         catalogs_extension)

    archetype_tool = getToolByName(portal, 'archetype_tool')
    # Mapping content types in catalogs depending on the catalog definition.
    # This variable will be used to reindex the catalog.
    # catalog_modifications = _map_content_types(
    #         archetype_tool, definition, catalog_modifications)
    #
    # # Indexing
    # for cat_id in definition.keys():
    #     catalog_modifications = _setup_catalog(
    #         portal, cat_id, definition.get(cat_id, {}), catalog_modifications)
    # # Reindex the catalogs which needs it
    # _cleanAndRebuildIfNeeded(portal, catalog_modifications)

    ### PHARMAWAY
    uid_catalog = getToolByName(portal, 'uid_catalog', None)
    if uid_catalog is None:
        logger.warning('Could not find the %s tool.' % ('uid_catalog'))
        return False
    for cat_id in catalogs_definition.keys():
        logger.info('Setting up catalog "{}"...'.format(cat_id))
        catalog = getToolByName(portal, cat_id, None)
        if catalog is None:
            logger.warning('Could not find the %s tool.' % (cat_id))
            continue

        cat_def = catalogs_definition.get(cat_id)
        # Mapping types to each catalog
        for type_id in cat_def.get('types'):
            # Getting the previous mapping
            prev_catalogs_list = archetype_tool.catalog_map.get(type_id, [])
            # uncataloging items from old catalogs
            for prev_cat in prev_catalogs_list:
                if prev_cat == 'uid_catalog':
                    continue
                if prev_cat == cat_id:
                    archetype_tool.setCatalogsByType(type_id, [cat_id])
                    continue
                catalog_old = getToolByName(portal, prev_cat, None)
                if catalog_old is None:
                    logger.warning(
                        'Could not find the %s tool.' % prev_cat)
                    continue
                logger.info('uncatalogging "{}" from {}'.format(type_id,
                                                                prev_cat))
                brains_to_uncat = catalog_old(portal_type=type_id)
                progress = 0
                total = len(brains_to_uncat)
                for brain in brains_to_uncat:
                    catalog_old.uncatalog_object(brain.getPath())
                    progress += 1
                    if progress % 100 == 0:
                        logger.info(
                            'Progress: {}/{} objects have been uncataloged '
                            'from {}.'.format(progress, total, prev_cat))
            logger.info('Mapping {} type in {}...'.format(type_id, cat_id))
            archetype_tool.setCatalogsByType(type_id, [cat_id])
        for index_id, index_type in cat_def.get('indexes').items():
            _addIndex(catalog, index_id, index_type)
        for column in cat_def.get('columns'):
            _addColumn(catalog, column)
        # reindexing objects
        brains = uid_catalog(portal_type=cat_def.get('types'))
        progress = 0
        total = len(brains)
        logger.info('indexing {} objects in {}...'.format(total, cat_id))
        # for brain in brains:
        #     # reindexing only vital indexes
        #         catalog.catalog_object(
        #             brain.getObject(),
        #             idxs=['UID', 'path', 'review_state', 'portal_type'],
        #             update_metadata=0)
        #     progress += 1
        #     if progress % 100 == 0:
        #         logger.info(
        #             'Progress: {}/{} objects have been indexed '
        #             'in {}.'.format(progress, total, cat_id))
        #         if progress % 1000 == 0:
        #             transaction.commit()


def _merge_catalog_definitions(dict1, dict2):
    """
    Merges two dictionaries that represent catalogs definitions. The first
    dictionary contains the catalogs structure by default and the second dict
    contains additional information. Usually, the former is the Bika LIMS
    catalogs definition and the latter is the catalogs definition of an add-on
    The structure of each dict as follows:
        {
            CATALOG_ID: {
                'types':   ['ContentType', ...],
                'indexes': {
                    'UID': 'FieldIndex',
                    ...
                },
                'columns': [
                    'Title',
                    ...
                ]
            }
        }

    :param dict1: The dictionary to be used as the main template (defaults)
    :type dict1: dict
    :param dict2: The dictionary with additional information
    :type dict2: dict
    :returns: A merged dict with the same structure as the dicts passed in
    :rtype: dict
    """
    if not dict2:
        return dict1.copy()

    outdict = {}
    # Use dict1 as a template
    for k, v in dict1.items():
        if k not in dict2 and isinstance(v, dict):
            outdict[k] = v.copy()
            continue
        if k not in dict2 and isinstance(v, list):
            outdict[k] = v[:]
            continue
        if k == 'indexes':
            sdict1 = v.copy()
            sdict2 = dict2[k].copy()
            sdict1.update(sdict2)
            outdict[k] = sdict1
            continue
        if k in ['types', 'columns']:
            list1 = v
            list2 = dict2[k]
            outdict[k] = list(set(list1 + list2))
            continue
        if isinstance(v, dict):
            sdict1 = v.copy()
            sdict2 = dict2[k].copy()
            outdict[k] = _merge_catalog_definitions(sdict1, sdict2)

    # Now, add the rest of keys from dict2 that don't exist in dict1
    for k, v in dict2.items():
        if k in outdict:
            continue
        outdict[k] = v.copy()
    return outdict


def _map_content_types(
        archetype_tool, catalogs_definition, catalog_modifications):
    """
    Updates the mapping for content_types against catalogs.
    This function returns which types has been removed from a catalog and
    which types have been added to a catalog and which this is.
    :archetype_tool: an archetype_tool object
    :catalogs_definition: a dictionary like
        {
            CATALOG_ID: {
                'types':   ['ContentType', ...],
                'indexes': {
                    'UID': 'FieldIndex',
                    ...
                },
                'columns': [
                    'Title',
                    ...
                ]
            }
        }
    :catalog_modifications: a dictionary containing all the modifications
    to carry on.
        {'id_catalog': {
            new_indexes:[], new_columns:[], removal_types:[], added_types:[],
            ...}
    """
    # This will be a dictionary like {'content_type':['catalog_id', ...]}
    ct_map = {}
    # This list will contain the catalog ids to be modified
    for catalog_id in catalogs_definition.keys():
        # Getting the defined structure for each catalog.
        catalog_info = catalogs_definition.get(catalog_id, {})
        # Mapping the catalog with the defined types
        types = catalog_info.get('types', [])
        for t in types:
            tmp_l = ct_map.get(t, [])
            tmp_l.append(catalog_id)
            ct_map[t] = tmp_l
    # Mapping for each type
    for t in ct_map.keys():
        current_catalogs_list = ct_map[t]
        # Getting the previous mapping
        perv_catalogs_list = archetype_tool.catalog_map.get(t, [])
        current_catalogs_set = set(current_catalogs_list)
        perv_catalogs_set = set(perv_catalogs_list)
        # two situations can happen:
        # 1- type deleted from  catalog
        # 2- type added into a catalog
        # If the mapping has changed, update it
        if current_catalogs_set != perv_catalogs_set:
            # Setting catalogs to the type
            archetype_tool.setCatalogsByType(t, current_catalogs_list)

            # Checking situation 1
            removed_from_catalogs = perv_catalogs_set - current_catalogs_set
            for cat_id in removed_from_catalogs:
                # Getting the removal_types list for this catalog
                catalog_dict = catalog_modifications.get(cat_id, {})
                cat_types_l = catalog_dict.get('removal_types', [])
                # Adding the new id
                cat_types_l.append(t)
                # saving the value in catalog
                catalog_dict['removal_types'] = cat_types_l
                catalog_modifications[cat_id] = catalog_dict

            # Checking situation 2
            added_to_catalogs = current_catalogs_set - perv_catalogs_set
            for cat_id in added_to_catalogs:
                # Getting the removal_types list for this catalog
                catalog_dict = catalog_modifications.get(cat_id, {})
                cat_types_l = catalog_dict.get('added_types', [])
                # Adding the new id
                cat_types_l.append(t)
                # saving the value in catalog
                catalog_dict['added_types'] = cat_types_l
                catalog_modifications[cat_id] = catalog_dict

    return catalog_modifications


def _setup_catalog(
            portal, catalog_id, catalog_definition, catalog_modifications):
    """
    Given a catalog definition it updates the indexes, columns and content_type
    definitions of the catalog.
    :portal: the Plone site object
    :catalog_id: a string as the catalog id
    :catalog_definition: a dictionary like
        {
            'types':   ['ContentType', ...],
            'indexes': {
                'UID': 'FieldIndex',
                ...
            },
            'columns': [
                'Title',
                ...
            ]
        }
    :catalog_modifications: a dictionary containing all the modifications
    to carry on.
        {'id_catalog': {
            new_indexes:[], new_columns:[], removal_types:[], added_types:[],
            ...}
    """

    catalog = getToolByName(portal, catalog_id, None)
    if catalog is None:
        logger.warning('Could not find the %s tool.' % (catalog_id))
        return False
    # Indexes
    indexes_ids = catalog_definition.get('indexes', {}).keys()
    # Indexing
    for idx in indexes_ids:
        # The function returns if the index needs to be reindexed
        indexed = _addIndex(catalog, idx, catalog_definition['indexes'][idx])


    # Removing indexes
    in_catalog_idxs = catalog.indexes()
    to_remove = list(set(in_catalog_idxs)-set(indexes_ids))
    for idx in to_remove:
        # The function returns if the index has been deleted
        desindexed = _delIndex(catalog, idx)
        reindex = True if desindexed else reindex
    # Columns
    columns_ids = catalog_definition.get('columns', [])
    for col in columns_ids:
        created = _addColumn(catalog, col)
        reindex = True if created else reindex
    # Removing columns
    in_catalog_cols = catalog.schema()
    to_remove = list(set(in_catalog_cols)-set(columns_ids))
    for col in to_remove:
        # The function returns if the index has been deleted
        desindexed = _delColumn(catalog, col)
        reindex = True if desindexed else reindex
    return reindex


def _addIndex(catalog, index, indextype):
    """
    This function indexes the index element into the catalog if it isn't yet.
    :catalog: a catalog object
    :index: an index id as string
    :indextype: the type of the index as string
    :returns: a boolean as True if the element has been indexed and it returns
    False otherwise.
    """
    if index not in catalog.indexes():
        try:
            catalog.addIndex(index, indextype)
            logger.info('Catalog index %s added to %s.' % (index, catalog.id))
            return True
        except:
            logger.error(
                'Catalog index %s error while adding to %s.'
                % (index, catalog.id))
    return False


def _addColumn(cat, col):
    """
    This function adds a metadata column to the acatalog.
    :cat: a catalog object
    :col: a column id as string
    :returns: a boolean as True if the element has been added and
        False otherwise
    """
    # First check if the metadata column already exists
    if col not in cat.schema():
        try:
            cat.addColumn(col)
            logger.info('Column %s added to %s.' % (col, cat.id))
            return True
        except:
            logger.error(
                'Catalog column %s error while adding to %s.' % (col, cat.id))
    return False


def _delIndex(catalog, index):
    """
    This function desindexes the index element from the catalog.
    :catalog: a catalog object
    :index: an index id as string
    :returns: a boolean as True if the element has been desindexed and it
    returns False otherwise.
    """
    if index in catalog.indexes():
        try:
            catalog.delIndex(index)
            logger.info(
                'Catalog index %s deleted from %s.' % (index, catalog.id))
            return True
        except:
            logger.error(
                'Catalog index %s error while deleting from %s.'
                % (index, catalog.id))
    return False


def _delColumn(cat, col):
    """
    This function deletes a metadata column of the acatalog.
    :cat: a catalog object
    :col: a column id as string
    :returns: a boolean as True if the element has been removed and
        False otherwise
    """
    # First check if the metadata column already exists
    if col in cat.schema():
        try:
            cat.delColumn(col)
            logger.info('Column %s deleted from %s.' % (col, cat.id))
            return True
        except:
            logger.error(
                'Catalog column %s error while deleting from %s.'
                % (col, cat.id))
    return False


def _cleanAndRebuildIfNeeded(portal, cleanrebuild):
    """
    Rebuild the given catalogs.
    :portal: the Plone portal object
    :cleanrebuild: a list with catalog ids
    """
    for cat in cleanrebuild:
        catalog = getToolByName(portal, cat)
        if catalog:
            catalog.clearFindAndRebuild()
        else:
            logger.warning('%s do not found' % cat)

