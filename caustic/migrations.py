'''TEMPORARY: persistence should be done in another way!
'''

from database import collection
from models import Instruction
import json

collection.drop()

instructions = [
    {
        "name" : "property",
        "json" : json.dumps({
            "load" : "http://webapps.nyc.gov:8084/CICS/fin1/find001I",
            "method" : "post",
            "posts" : {
                "FHOUSENUM" : "{{Number}}",
                "FSTNAME"   : "{{Street}}",
                "FBORO"     : "{{Borough}}",
                "FAPTNUM"   : "{{Apt}}"
                },
            "then" : {
                "name" : "Owner",
                "find" : "<input\\s+type=\"hidden\"\\s+name=\"ownerName\\d?\"\\s+value=\"\\s*(\\w[^\"]*?)\\s*\"",
                "replace" : "$1"
                }
            })
        },
    {
        'name': 'manhattan',
        'tags': [10027],
        'json': json.dumps({
            "extends" : "/property",
            "posts" : {
                "FBORO"  : "1",
                "FAPTNUM": ""
                }
            })
        },
    {
        'name': 'bronx',
        'tags': [],
        'json': json.dumps({
            "extends" : "/property",
            "posts" : {
                "FBORO"  : "2",
                "FAPTNUM": ""
                }
            })
        },
    {
        'name': 'brooklyn',
        'tags': [11217],
        'json': json.dumps({
            "extends" : "/property",
            "posts" : {
                "FBORO"  : "3",
                "FAPTNUM": ""
                }
            })
        },
    {
        'name': 'queens',
        'tags': [],
        'json': json.dumps({
            "extends" : "/property",
            "posts" : {
                "FBORO"  : "4",
                "FAPTNUM": ""
                }
            })
        },
    {
        'name': 'staten island',
        'tags': [],
        'json': json.dumps({
            "extends" : "/property",
            "posts" : {
                "FBORO"  : "5",
                "FAPTNUM": ""
                }
            })
        }
]

for instruction in instructions:
    collection.save(Instruction(**instruction).to_python())
