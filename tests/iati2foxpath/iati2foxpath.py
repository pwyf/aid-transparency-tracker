#!/usr/bin/env python

# Uses the IATI Standard schema to create a list of 
# tests for IATI Data Quality.

from lxml import etree
import re

organisations_schema = "iati-organisations-schema.xsd"
activities_schema = "iati-activities-schema.xsd"
common_schema = "iati-common.xsd"

NS = "{http://www.w3.org/2001/XMLSchema}"

activities_data = etree.parse(activities_schema)
common_data = etree.parse(common_schema)

datafiles = [activities_data, common_data]

elements = {}
attributes = {}

def cleanUpType(data):
    return re.sub("xsd:", "", data)

def getAttributes(data):
    zattributes = {}
    attributes = data.findall(NS+"attribute")
    for attribute in attributes:
        zattributes[attribute.get('name')] = cleanUpType(attribute.get('type'))
    return zattributes

def getElementAttributes(data):
    zattributes = {}
    try:
        theattributes = data.find(NS+"complexType").findall(NS+"attribute")
        for attribute in theattributes:
            try:
                zattributes[attribute.get('name')] = cleanUpType(attribute.get('type'))
            except Exception:
                zattributes[attribute.get('ref')] = attributes[attribute.get('ref')]
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
            zsubelements[element_name]['attributes'] = getElementAttributes(element)
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
        zelements[element_name]['attributes'] = getElementAttributes(element)
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
            print parent + "/@" + attribute + " is a " + attribute_data + "?"

def printElements(elements, parent_element=None):
    for element, element_data in elements.items():
        if ((element != "elements") and (element != "attributes")):
            if (parent_element is not None):
                print str(parent_element) + "/" + str(element) + " exists?"
            else:
                print element, "exists?"
            if parent_element is not None:
                parent = parent_element + "/" + element
            else:
                parent = element
            try:
                printAttributes(element, element_data['attributes'], parent)
            except Exception:
                pass
            try:
                printElements(element_data['elements'], parent_element=parent)
            except Exception:
                pass

def run():
    for datafile in datafiles:
        attributes.update(getAttributes(datafile))
    attributes['xml:lang'] = "string"

    for datafile in datafiles:
        elements.update(getElements(datafile))

    printElements(elements)

run()
