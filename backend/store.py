# -*- coding: utf-8 -*-
#
# backend - query/update graphs for the Commons Machinery metadata catalog
#
# Copyright 2014 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an AGPLv3 license, please see LICENSE in the top dir.

import RDF

NS_CATALOG = "http://catalog.commonsmachinery.se/ns#"
NS_REM3 = "http://scam.sf.net/schema#"
NS_XSD = "http://www.w3.org/2001/XMLSchema#"

work_properties_rdf = {
    'id':           NS_CATALOG  + "id",
    'resource':     NS_REM3     + "resource",
    'metadata':     NS_REM3     + "metadata",
    'created':      NS_CATALOG  + "created",
    'creator':      NS_CATALOG  + "creator",
    'updated':      NS_CATALOG  + "updated",
    'updatedBy':    NS_CATALOG  + "updatedBy",
    'visibility':   NS_CATALOG  + "visibility",
    'state':        NS_CATALOG  + "state",
    'post':         NS_CATALOG  + "post",
    'source':       NS_CATALOG  + "source",
}

work_properties_json = {}
for key, value in work_properties_rdf.iteritems():
    work_properties_json[value] = key

work_properties_types = {
    'id': int,
    'created': int,
    'updated': int,
}

WORK_METADATA_CONTEXT = "urn:work-metadata-%d"
WORK_PROPERTIES_CONTEXT = "urn:work-properties-%d"

class EntryStore(object):
    def __init__(self, name):
        self._store = RDF.HashStorage(name, options="hash-type='bdb',dir='.',contexts='yes'")
        self._model = RDF.Model(self._store)

    def store_work(self, data):
        data = data.copy()

        context = RDF.Node(uri_string=WORK_METADATA_CONTEXT % data["id"])

        for subject in data["metadataGraph"].keys():
            subject_node = RDF.Node(uri_string=subject)

            for predicate in data["metadataGraph"][subject].keys():
                predicate_node = RDF.Node(uri_string=predicate)

                for object in data["metadataGraph"][subject][predicate]:
                    value = object["value"]
                    type = object["type"]
                    #datatype = object["datatype"]
                    # TODO: support lang

                    if type == "literal":
                        object_node = RDF.Node(literal=value)
                    elif type == "uri":
                        object_node = RDF.Node(uri_string=value)
                    elif type == "bnode":
                        object_node = RDF.Node(blank=value)

                    statement = RDF.Statement(subject_node, predicate_node, object_node)

                    if (statement, context) not in self._model:
                        self._model.append(statement, context=context)

        del data["metadataGraph"]

        # save remaining properties under the properties context

        context = RDF.Node(uri_string=WORK_PROPERTIES_CONTEXT % data["id"])
        subject_node = RDF.Node(uri_string="urn:properties")

        for key, value in data.iteritems():
            if key not in work_properties_rdf:
                raise RuntimeError("Unknown work property %s" % key)

            predicate_node = RDF.Node(uri_string=work_properties_rdf[key])
            object_node = RDF.Node(literal=str(value))

            statement = RDF.Statement(subject_node, predicate_node, object_node)
            if (statement, context) not in self._model:
                        self._model.append(statement, context=context)

    def get_work(self, id):
        data = {}

        context = RDF.Node(uri_string=WORK_PROPERTIES_CONTEXT % int(id))

        for statement in self._model.as_stream(context=context):
            property_uri = unicode(statement.predicate.uri)
            if property_uri not in work_properties_json:
                raise RuntimeError("Unknown work property %s" % property_uri)

            property_name = work_properties_json[property_uri]
            if property_name in work_properties_types:
                property_value = work_properties_types[property_name](statement.object.literal[0])
            else:
                property_value = statement.object.literal[0]

            data[unicode(property_name)] = property_value

        if len(data) == 0:
            raise RuntimeError("Entry not found in the store.")

        data["metadataGraph"] = {}
        metadata_graph = data["metadataGraph"]

        context = RDF.Node(uri_string=WORK_METADATA_CONTEXT % int(id))

        for statement in self._model.as_stream(context=context):
            subject_uri = unicode(statement.subject.uri)
            predicate_uri = unicode(statement.predicate.uri)

            if not metadata_graph.has_key(subject_uri):
                metadata_graph[subject_uri] = {}

            if not metadata_graph[subject_uri].has_key(predicate_uri):
                metadata_graph[subject_uri][predicate_uri] = []

            object = {}

            if statement.object.is_literal():
                # TODO: support lang
                object[u"type"] = u"literal"
                object[u"datatype"] = u"http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral"
                object[u"value"] = statement.object.literal[0]
            elif statement.object.is_resource():
                object[u"type"] = u"uri"
                object[u"value"] = unicode(statement.object.uri)
            elif statement.object.is_blank():
                object[u"type"] = u"bnode"
                object[u"value"] = unicode(statement.object.blank)

            metadata_graph[subject_uri][predicate_uri].append(object)

        return data