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
            "name" : "Owner",
            "load" : "http://webapps.nyc.gov:8084/CICS/fin1/find001I",
            "method" : "post",
            "posts" : {
                "FHOUSENUM" : "{{Number}}",
                "FSTNAME"   : "{{Street}}",
                "FBORO"     : "{{Borough}}",
                "FAPTNUM"   : "{{Apt}}"
                },
            "then" : [
                    {
                        "description" : "The names of the owners",
                        "name" : "Owner",
                        "find" : "<input\\s+type=\"hidden\"\\s+name=\"ownerName\\d?\"\\s+value=\"\\s*(\\w[^\"]*?)\\s*\"",
                        "replace" : "$1",
                        "then"    : "dos-corpsearch"
                        },
                    {
                        "description" : "Block number",
                        "name"    : "Block",
                        "find"    : "<input\\s+type=\"hidden\"\\s+name=\"q49_block_id\\d?\"\\s+value=\"(\\d+)\"",
                        "replace" : "$1",
                        "match"   : 0
                        },
                    {
                        "description" : "Lot number",
                        "name"    : "Lot",
                        "find"    : "<input\\s+type=\"hidden\"\\s+name=\"q49_lot\\d?\"\\s+value=\"(\\d+)\"",
                        "replace" : "$1",
                        "match"   : 0
                        },
                    "/acris-index-all-docs"
                    ]
            })
        },
    {
        'name': 'manhattan',
        'tags': [10026, 10027, 10030, 10037, 10039, 10001, 10011, 10018, 10019, 10020, 10036, 10029, 10035, 10010, 10016, 10017, 10022, 10012, 10013, 10014, 10004, 10005, 10006, 10007, 10038, 10280, 10002, 10003, 10009, 10021, 10028, 10044, 10128, 10023, 10024, 10025, 10031, 10032, 10033, 10034, 10040],
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
        'tags': [10453, 10457, 10460, 10458, 10467, 10468, 10451, 10452, 10456, 10454, 10455, 10459, 10474, 10463, 10471, 10466, 10469, 10470, 10475, 10461, 10462,10464, 10465, 10472, 10473],
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
        'tags': [11212, 11213, 11216, 11233, 11238, 11209, 11214, 11228, 11204, 11218, 11219, 11230, 11234, 11236, 11239, 11223, 11224, 11229, 11235, 11201, 11205, 11215, 11217, 11231, 11203, 11210, 11225, 11226, 11207, 11208, 11211, 11222, 11220, 11232, 11206, 11221, 11237],
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
        'tags': [11361, 11362, 11363, 11364, 11354, 11355, 11356, 11357, 11358, 11359, 11360, 11365, 11366, 11367, 11412, 11423, 11432, 11433, 11434, 11435, 11436, 11101, 11102, 11103, 11104, 11105, 11106, 11374, 11375, 11379, 11385, 11691, 11692, 11693, 11694, 11695, 11697, 11004, 11005, 11411, 11413, 11422, 11426, 11427, 11428, 11429, 11414, 11415, 11416, 11417, 11418, 11419, 11420, 11421, 11368, 11369, 11370, 11372, 11373, 11377, 11378],
        'json': json.dumps({
            "extends" : "/property",
            "posts" : {
                "FBORO"  : "4",
                "FAPTNUM": ""
                }
            })
        },
    {
        'name': 'staten-island',
        'tags': [10302, 10303, 10310, 10306, 10307, 10308, 10309, 10312, 10301, 10304, 10305, 10314],
        'json': json.dumps({
            "extends" : "/property",
            "posts" : {
                "FBORO"  : "5",
                "FAPTNUM": ""
                }
            })
        },
    {
        'name': 'acris-index-all-docs',
        'json': json.dumps({
                "extends"     : "acris-index",
                "description" : "Subsitutes in defaults that make acris-index grab all documents for all times (1966-present).",
                "posts" : {
                    "hid_selectdate": "To Current Date",
                    "hid_datefromm" : "",
                    "hid_datefromd" : "",
                    "hid_datefromy" : "",
                    "hid_datetom" : "",
                    "hid_datetod" : "",
                    "hid_datetoy" : "",
                    "hid_doctype" : ""
                    }
                })
        },
    {
        'name': 'acris-index',
        'json': json.dumps({
                "description" : "Index of all property transactions for BBL in NYC excluding Staten Island.",
                "name" : "Deeds & Mortgages",
                "load" : "http://a836-acris.nyc.gov/Scripts/DocSearch.dll/BBLResult",
                "cookies" : {
                    "JUMPPAGE" : "YES"
                    },
                "posts" : {
                    "hid_borough" : "{{Borough}}",
                    "hid_borough_name" : "",
                    "hid_block" : "{{Block}}",
                    "hid_lot"   : "{{Lot}}",
                    "hid_selectdate": "DR",
                    "hid_datefromm" : "{{FromMonth}}",
                    "hid_datefromd" : "{{FromDay}}",
                    "hid_datefromy" : "{{FromYear}}",
                    "hid_datetom" : "{{ToMonth}}",
                    "hid_datetod" : "{{ToDay}}",
                    "hid_datetoy" : "{{ToYear}}",
                    "hid_doctype" : "{{DocType}}",
                    "hid_doctype_name" : "",
                    "hid_max_rows" : "10000",
                    "hid_page" : "",
                    "hid_ReqId" : "",
                    "hid_SearchType" : "BBL",
                    "hid_ISIntranet" : "N",
                    "hid_EmployeeID" : ""
                    },
                "then" : {
                    "find" : "<!--Table Begin!-->(.*?)<!--Table End-->",
                    "match" : 0,
                    "then" : {
                        "extends" : "/html-row",
                        "min"  : 2,
                        "max"  : -1,
                        "then" : [{
                                "name"        : "Doc ID",
                                "find"     : "go_detail\\('([^']+)'\\)",
                                "replace" : "$1",
                                "match"       : 0
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Reel/Pg/File",
                                "match"   : 1
                                },{
                                "extends" : "/acris-column",
                                "name"    : "CRFN",
                                "match"   : 2
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Lot",
                                "match"   : 3
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Partial",
                                "match"   : 4
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Recorded / Filed",
                                "match"   : 5
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Document Type",
                                "match"   : 6
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Pages",
                                "match"   : 7
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Party1",
                                "match"   : 8
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Party2",
                                "match"   : 9
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Party 3/ Other",
                                "match"   : 10
                                },{
                                "extends" : "/acris-column",
                                "name"    : "More Party 1/2 Names",
                                "match"   : 11
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Corrected/ Remarks",
                                "match"   : 12
                                },{
                                "extends" : "/acris-column",
                                "name"    : "Doc Amount",
                                "match"   : 13
                                }]
                        }
                    }
                })
        },
    {
        'name': 'acris-column',
        'json': json.dumps({
                "description" : "ACRIS has a font definition for every column.",
                "find"     : "<\\s*font[^>]*>(.*?)</\\s*font\\s*>",
                "replace" : "$1"
                })
        },
    {
        'name': 'html-row',
        'json': json.dumps({
                "find"     : "<\\s*tr[^>]*>(.*?)</\\s*tr\\s*>",
                "replace" : "$1"
                })
        },
    {
        'name': 'dos-corpsearch',
        'json': json.dumps({
                "description": "Search the NYS DOS corporate entities listing using a partial search.  Requires 'searchname', returns a search results page with 0 to many pages of matching entities.",
                "load" : "http://appext9.dos.state.ny.us/corp_public/CORPSEARCH.SELECT_ENTITY",
                "name" : "Corporate Info",
                "posts": {
                    "p_entity_name" : "{{Owner}}",
                    "p_name_type"   : "%25",
                    "p_search_type" : "PARTIAL"
                    },
                "then" : [{
                        "description" : "Keep track of how many entities were found in the search.",
                        "name"        : "Number of matching entities",
                        "find"        : "<p\\s+title\\s*=\\s*\"messages\">([^<]*)</p>",
                        "match"       : 0,
                        "replace"     : "$1"
                        },{
                        "description" : "Split by each entity on the search results page.",
                        "find"        : "<a\\s+title\\s*=\\s*\"Link to entity information.*?</a>",
                        "name"        : "entity",
                        "then" : [{
                                "description" : "Finds the p_nameid",
                                "find"        : "p_nameid=(\\d+)",
                                "name"        : "p_nameid",
                                "replace"     : "$1",
                                "match"       : 0
                                },{
                                "description" : "Finds the p_corpid",
                                "find"        : "p_corpid=(\\d+)",
                                "name"        : "p_corpid",
                                "replace"     : "$1",
                                "match"       : 0
                                },{
                                "description" : "Resolve the href link for each entity against the site, load the page.",
                                "load"        : "http://appext9.dos.state.ny.us/corp_public/CORPSEARCH.ENTITY_INFORMATION?p_nameid={{p_nameid}}&p_corpid={{p_corpid}}&p_entity_name={{Owner}}&p_name_type=%25&p_search_type=PARTIAL",
                                "then" : [{
                                        "name"        : "Current Entity Name",
                                        "find"        : "<th scope=\"row\">Current Entity Name:</th>[^<]*<td>([^<]*)</td>",
                                        "replace"     : "$1"
                                        },{
                                        "name"        : "Initial DOS Filing Date",
                                        "find"        : "<th scope=\"row\">Initial DOS Filing Date:</th>[^<]*<td>([^<]*)</td>",
                                        "replace"     : "$1"
                                        },{
                                        "name"        : "County",
                                        "find"        : "<th scope=\"row\">County:</th>[^<]*<td>([^<]*)</td>",
                                        "replace"     : "$1"
                                        },{
                                        "name"        : "Jurisdiction",
                                        "find"        : "<th scope=\"row\">Jurisdiction:</th>[^<]*<td>([^<]*)</td>",
                                        "replace"     : "$1"
                                        },{
                                        "name"        : "Entity Type",
                                        "find"        : "<th scope=\"row\">Entity Type:</th>[^<]*<td>([^<]*)</td>",
                                        "replace"     : "$1"
                                        },{
                                        "name"        : "Current Entity Status",
                                        "find"        : "<th scope=\"row\">Current Entity Status:</th>[^<]*<td>([^<]*)</td>",
                                        "replace"     : "$1"
                                        },{
                                        "name"        : "DOS Process Address",
                                        "find"        : "<td headers=\"c1\">(.*?)</td>",
                                        "replace"     : "$1",
                                        "match"       : 0
                                        },{
                                        "name"        : "Registered Agent",
                                        "find"        : "<td headers=\"c1\">(.*?)</td>",
                                        "replace"     : "$1",
                                        "match"       : 1
                                        },{
                                        "name"        : "Filing Date",
                                        "find"        : "<td class=\"FileDt\">([^<])</th>",
                                        "replace"     : "$1"
                                        },{
                                        "name"        : "Name Type",
                                        "find"        : "<td class=\"NameType\">([^<])</th>",
                                        "replace"     : "$1"
                                        },{
                                        "name"        : "Entity Name",
                                        "find"        : "<td class=\"Entity Name\">([^<])</th>",
                                        "replace"     : "$1"
                                        }]
                                }]
                        }]
                })
        }
    ]

for instruction in instructions:
    collection.save(Instruction(**instruction).to_python())
