#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

# Adapted from InaSAFE

from xml.etree import ElementTree
from lxml import etree


# XML Namespaces
XML_NS = {
    'gmi': 'http://www.isotc211.org/2005/gmi',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}

ElementTree.register_namespace('gmi', XML_NS['gmi'])
ElementTree.register_namespace('gco', XML_NS['gco'])
ElementTree.register_namespace('gmd', XML_NS['gmd'])
ElementTree.register_namespace('xsi', XML_NS['xsi'])

properties = {
    'organisation': (
        'gmd:contact/'
        'gmd:CI_ResponsibleParty/'
        'gmd:organisationName/'
        'gco:CharacterString'),
    'email': (
        'gmd:contact/'
        'gmd:CI_ResponsibleParty/'
        'gmd:contactInfo/'
        'gmd:CI_Contact/'
        'gmd:address/'
        'gmd:CI_Address/'
        'gmd:electronicMailAddress/'
        'gco:CharacterString'),
    'date': (
        'gmd:dateStamp/'
        'gco:Date'),
    'abstract': (
        'gmd:identificationInfo/'
        'gmd:MD_DataIdentification/'
        'gmd:abstract/'
        'gco:CharacterString'),
    'title': (
        'gmd:identificationInfo/'
        'gmd:MD_DataIdentification/'
        'gmd:citation/'
        'gmd:CI_Citation/'
        'gmd:title/'
        'gco:CharacterString'),
    'license': (
        'gmd:identificationInfo/'
        'gmd:MD_DataIdentification/'
        'gmd:resourceConstraints/'
        'gmd:MD_Constraints/'
        'gmd:useLimitation/'
        'gco:CharacterString'),
    'url': (
        'gmd:distributionInfo/'
        'gmd:MD_Distribution/'
        'gmd:transferOptions/'
        'gmd:MD_DigitalTransferOptions/'
        'gmd:onLine/'
        'gmd:CI_OnlineResource/'
        'gmd:linkage/'
        'gmd:URL'),
}


def insert_xml_element(root, element_path):
    """insert an XML element in an other creating the needed parents.
    :param root: The container
    :type root: ElementTree.Element
    :param element_path: The path relative to root
    :type element_path: str
    :return: ElementTree.Element
    :rtype : ElementTree.Element
    """
    element_path = element_path.split('/')
    parent = root
    # iterate all parents of the missing element
    for level in range(len(element_path)):
        path = '/'.join(element_path[0:level + 1])
        tag = element_path[level]
        element = root.find(path, XML_NS)
        if element is None:
            # if a parent is missing insert it at the right place
            try:
                element = ElementTree.SubElement(parent, tag)
            except Exception:
                # In some cases we can't add parent because the tag name is
                # not specific
                pass
        parent = element
    return element


def update_xml(xml_file, new_values):
    """Update xml file with new_values.

    :param xml_file: Path to the xml_file.
    :type xml_file: str

    :param new_values: Dictionary of key and the new value.
    :type new_values: dict
    """
    exml = etree.parse(xml_file)
    root = exml.getroot()

    for name, path in properties.items():
        if name in new_values:
            elem = root.find(path, XML_NS)
            if elem is None:
                # create elem
                elem = insert_xml_element(root, path)
            elem.text = new_values[name]

    exml.write(open(xml_file, 'w'))
