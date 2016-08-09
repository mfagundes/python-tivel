#coding: utf-8

import logging
import json
from django.core import serializers


def loads(objs, fields=None):
    obj_json = serializers.serialize('json', objs, fields=fields)
    objs = json.loads(obj_json)
    data = []
    for obj in objs:
        obj_dict = {'id': obj['pk']}
        obj_dict.update(obj['fields'])
        data.append(obj_dict)
    return data


