from lxml import etree
import msgpack
import zlib
import os

CUR_FOLDER = os.path.dirname(__file__)
UCD_XLM_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'data', 'ucd.nounihan.flat.xml')
NAMES_LIST_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'ToolFiles', 'NamesList.mp.zlib')
VERSIONS_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'ToolFiles', 'Versions.mp.zlib')
COMMON_NAMES_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'ToolFiles', 'CommonNames.mp.zlib')

with open(NAMES_LIST_PATH, 'rb') as f:
    names_list = msgpack.unpackb(zlib.decompress(f.read()), strict_map_key=False)

versions = {
    'single': {},
    'range': {}
}
common_names = {}

namespaces = {'ucd': 'http://www.unicode.org/ns/2003/ucd/1.0'}

context = etree.iterparse(
    UCD_XLM_PATH, 
    events=('end',), 
    tag=(
        '{http://www.unicode.org/ns/2003/ucd/1.0}char',
        '{http://www.unicode.org/ns/2003/ucd/1.0}surrogate',
        '{http://www.unicode.org/ns/2003/ucd/1.0}standardized-variant'
    )
)

alias_type_translator = {
    'abbreviation': '缩写',
    'alternate': '备用',
    'control': '控制字符名',
    'correction': '修正',
    'figment': '虚构的'
}

for event, elem in context:
    if elem.tag == '{http://www.unicode.org/ns/2003/ucd/1.0}char':
        name_aliases = elem.findall('ucd:name-alias', namespaces)
        
        cp = elem.get('cp')
        if cp is not None:
            cp_int = int(cp, 16)
            versions['single'][cp_int] = elem.get('age')
            if cp_int not in names_list:
                character = {
                    'code': f'U+{cp}',
                    'name': elem.get('na').replace('#', cp),
                    'comment': [],
                    'alias': [],
                    'formal alias': [],
                    'cross references': [],
                    'variation': [],
                    'decomposition': [],
                    'compat mapping': []
                }
                names_list[cp_int] = character
            else:
                character = names_list[cp_int]
                
            for name_alias in name_aliases:
                alias_type = name_alias.get('type')
                if alias_type == 'correction':
                    character['formal alias'].append(name_alias.get('alias') + '(' + alias_type_translator[alias_type] + ')')
                else:
                    character['alias'].append(name_alias.get('alias') + '(' + alias_type_translator[alias_type] + ')')
            
            if elem.get('na'):
                character['name'] = elem.get('na').replace('#', cp)
            dm = elem.get('dm')
            character['decomposition'] = dm.split() if dm != '#' else []
        else:
            fcp = elem.get('first-cp')
            lcp = elem.get('last-cp')
            
            fcp_int = int(fcp, 16)
            lcp_int = int(lcp, 16)
            
            name = elem.get('na')
            if fcp == 'E000' or fcp == 'F0000' or fcp == '100000':
                name = 'PRIVATE USE-#'
            
            versions['range'][(fcp_int, lcp_int)] = elem.get('age')
            common_names[(fcp_int, lcp_int)] = name
    elif elem.tag == '{http://www.unicode.org/ns/2003/ucd/1.0}surrogate':
        cp = elem.get('cp')
        if cp is not None:
            cp_int = int(cp, 16)
            versions['single'][cp_int] = elem.get('age')
        else:
            fcp = elem.get('first-cp')
            lcp = elem.get('last-cp')
            
            fcp_int = int(fcp, 16)
            lcp_int = int(lcp, 16)
            
            versions['range'][(fcp_int, lcp_int)] = elem.get('age')
    elif elem.tag == '{http://www.unicode.org/ns/2003/ucd/1.0}standardized-variant':
        cps = elem.get('cps').split()
        variation_target = str(int(cps[0], 16))
        desc = elem.get('desc')
        if variation_target in names_list:
            names_list[variation_target]['variation'].append(' '.join(map(lambda c: 'U+' + c, cps)) + (f'({desc})' if desc else ''))
        else:
            character = {
                'code': f'U+{cps[0]}',
                'name': '{common_name}',
                'comment': [],
                'alias': [],
                'formal alias': [],
                'cross references': [],
                'variation': [' '.join(map(lambda c: 'U+' + c, cps)) + (f'({desc})' if desc else '')],
                'decomposition': [],
                'compat mapping': []
            }
            names_list[cp_int] = character
    
    elem.clear()
    while elem.getprevious() is not None:
        del elem.getparent()[0]

with (
    open(NAMES_LIST_PATH, 'wb') as nlf,
    open(VERSIONS_PATH, 'wb') as vf,
    open(COMMON_NAMES_PATH, 'wb') as cnf
):
    nlf.write(zlib.compress(msgpack.packb(names_list)))
    vf.write(zlib.compress(msgpack.packb(versions)))
    cnf.write(zlib.compress(msgpack.packb(common_names)))
