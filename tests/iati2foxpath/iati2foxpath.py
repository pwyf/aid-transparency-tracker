#!/usr/bin/env python

# Uses the IATI Standard schema to create a list of 
# tests for IATI Data Quality.

from lxml import etree
import re
import csv

organisations_schema = "iati-organisations-schema.xsd"
activities_schema = "iati-activities-schema.xsd"
common_schema = "iati-common.xsd"
codelists_mapping = "iati-codelists.csv"

NS = "{http://www.w3.org/2001/XMLSchema}"

activities_data = etree.parse(activities_schema)
common_data = etree.parse(common_schema)

datafiles = [activities_data, common_data]
supported_attributes = ['decimal', 'dateTime', 'date', 'positiveInteger', 'boolean', 'int']

elements = {}
attributes = {}
codes = {}

def getCodeLists(mapping=codelists_mapping):
    f = open(mapping)
    codelists = csv.DictReader(f)
    for codelist in codelists:
        codes[(codelist['element'], codelist['attribute'])] = codelist['codelist_name']
    f.close()

def cleanUpType(data):
    return re.sub("xsd:", "", data)

def getAttributes(data):
    zattributes = {}
    attributes = data.findall(NS+"attribute")
    for attribute in attributes:
        zattributes[attribute.get('name')] = cleanUpType(attribute.get('type'))
    return zattributes

def getElementAttributes(data, element_name):
    zattributes = {}
    try:
        theattributes = data.find(NS+"complexType").findall(NS+"attribute")
        for attribute in theattributes:
            try:
                attribute_name = attribute.get('name')
                attribute_type = cleanUpType(attribute.get('type'))
            except Exception:
                attribute_name = attribute.get('ref')
                attribute_type = attributes[attribute.get('ref')]
            
            try:
                attribute_codelist = codes[(element_name, attribute_name)]
                zattributes[attribute_name] = {'type': attribute_type,
                                               'codelist': attribute_codelist }
            except Exception:
                zattributes[attribute_name] = {'type': attribute_type}
                
    except Exception:
        pass
    return zattributes

def getSubElements(data):
    zsubelements = {}
    try:
        elements=data.find(NS+'complexType').find(NS+'choice').findall(NS+'element')
        for element in elements:
            try:
                element_name= element.get('name')
            except Exception:
                element_name=element.get('ref')
            zsubelements[element_name] = {}
            zsubelements[element_name]['attributes'] = getElementAttributes(element, element_name)
            zsubelements[element_name]['elements'] = getSubElements(element)
    except Exception:
        pass
    return zsubelements

def getElements(data):
    zelements = {}
    elements=data.findall(NS+"element")
    
    for element in elements:
        try:
            element_name= element.get('name')
        except Exception:
            element_name=element.get('ref')
        zelements[element_name] = {}
        zelements[element_name]['attributes'] = getElementAttributes(element, element_name)
        zelements[element_name]['elements'] = getSubElements(element)
    return zelements

def printAttributes(element, attributes, parent_element=None):
    for attribute, attribute_data in attributes.items():
        if attribute is not None:
            if parent_element is not None:
                parent = parent_element
            else:
                parent = element
            print parent + "/@" + attribute + " exists?"
            if attribute_data['type'] in supported_attributes:
                print parent + "/@" + attribute + " is a " + attribute_data['type'] + "?"
            if 'codelist' in attribute_data:
                print parent + "/@" + attribute + " is on codelist " + attribute_data['codelist'] + "?"

def printElements(elements, parent_element=None):
    for element, element_data in elements.items():
        if ((element != "elements") and (element != "attributes") and (element != None)):
            if (parent_element is not None):
                print str(parent_element) + "/" + str(element) + " exists?"
            else:
                print element, "exists?"
            if ((parent_element is not None) and (element is not None)):
                parent = parent_element + "/" + element
            else:
                parent = element
            printAttributes(element, element_data['attributes'], parent)
            printElements(element_data['elements'], parent_element=parent)

def run():
    getCodeLists()

    for datafile in datafiles:
        attributes.update(getAttributes(datafile))
    attributes['xml:lang'] = "string"

    for datafile in datafiles:
        elements.update(getElements(datafile))

    printElements(elements)

if __name__ == '__main__':
    run()
