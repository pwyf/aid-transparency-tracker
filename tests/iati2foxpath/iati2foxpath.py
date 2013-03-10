#!/usr/bin/env python

# Uses the IATI Standard schema to create a list of 
# tests for IATI Data Quality.

from lxml import etree

organisations_schema = "iati-organisations-schema.xsd"
activities_schema = "iati-activities-schema.xsd"
common_schema = "iati-common.xsd"

NS = "{http://www.w3.org/2001/XMLSchema}"

activities_data = etree.parse(activities_schema)
common_data = etree.parse(common_schema)

datafiles = [activities_data, common_data]

elements = {}

def getAttributes(data):
    zattributes = {}
    try:
        attributes = data.find(NS+"complexType").findall(NS+"attribute")
        for attribute in attributes:
            zattributes[attribute.get('name')] = {}
    except Exception:
        pass
    return zattributes

def getSubElements(data):
    zsubelements = {}
    try:
        elements=data.find(NS+'complexType').find(NS+'choice').findall(NS+'element')
        #print etree.tostring(elements)
        for element in elements:
            try:
                element_name= element.get('name')
            except Exception:
                element_name=element.get('ref')
            zsubelements[element_name] = {}
            zsubelements[element_name]['attributes'] = getAttributes(element)
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
        zelements[element_name]['attributes'] = getAttributes(element)
        zelements[element_name]['elements'] = getSubElements(element)
    return zelements

def printAttributes(element, attributes, parent_element=None):
    for attribute in attributes:
        if attribute is not None:
            if parent_element is not None:
                parent = parent_element
            else:
                parent = element
            print parent + "/@" + attribute + " exists?"

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
        elements.update(getElements(datafile))

    printElements(elements)

run()
