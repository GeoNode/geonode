import json
from lxml import etree

from django.http import QueryDict
from  collections import OrderedDict

class MessageHelperJSON:

    @staticmethod
    def get_dict_msg(success=False, msg='', data_dict=None):

        if isinstance(data_dict, dict) or isinstance(data_dict, list) or isinstance(data_dict, tuple):
            if msg:
                return { 'success': success, 'message' : msg, 'data' : data_dict }
            else:
                return { 'success': success, 'data' : data_dict }
    
        return { 'success': success, 'message' : msg }

    @staticmethod
    def get_json_msg_from_dict(dict_to_dump):

        try:        
            return json.dumps(dict_to_dump)
        except:
            return json.dumps({ 'success': False, 'message' : 'Convert to JSON message failed' })

    @staticmethod
    def get_json_fail_msg(msg, data_dict=None):
        return MessageHelperJSON.get_json_msg(success=False, msg=msg, data_dict=data_dict)

    @staticmethod
    def get_json_success_msg(msg=None, data_dict=None):
        return MessageHelperJSON.get_json_msg(success=True, msg=msg, data_dict=data_dict)


    @staticmethod
    def get_json_msg(success=False, msg='', data_dict=None):
    
        d = MessageHelperJSON.get_dict_msg(success, msg, data_dict)
        return MessageHelperJSON.get_json_msg_from_dict(d)


def remove_whitespace_from_xml(xml_str):
    if xml_str is None:
        return None
        
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        elem = etree.XML(xml_str, parser=parser)
        return etree.tostring(elem)
    except:
        return None


