import os
import json
from fontTools.ttLib import TTFont
import msgpack
import zlib

CUR_FOLDER = os.path.dirname(__file__)
DEFINED_CHARACTER_LIST_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'ToolFiles', 'DefinedCharacterList.mp.zlib')
NAMES_LIST_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'ToolFiles', 'NamesList.mp.zlib')
COMMON_NAMES_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'ToolFiles', 'CommonNames.mp.zlib')
OUT_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'ToolFiles', 'FontFallback.mp.zlib')

with (
    open(DEFINED_CHARACTER_LIST_PATH, 'rb') as dclf,
    open(NAMES_LIST_PATH, 'rb') as nlf,
    open(COMMON_NAMES_PATH, 'rb') as cnf
):
    DEFINED_CHARACTER_LIST = set(msgpack.unpackb(zlib.decompress(dclf.read())))
    NAMES_LIST = msgpack.unpackb(zlib.decompress(nlf.read()), strict_map_key=False)
    COMMON_NAMES = msgpack.unpackb(zlib.decompress(cnf.read()), strict_map_key=False, use_list=False)

NOT_CHAR = [
    0xFFFE, 0xFFFF, 0x1FFFE, 0x1FFFF, 0x2FFFE,
    0x2FFFF, 0x3FFFE, 0x3FFFF, 0x4FFFE, 0x4FFFF,
    0x5FFFE, 0x5FFFF, 0x6FFFE, 0x6FFFF, 0x7FFFE,
    0x7FFFF, 0x8FFFE, 0x8FFFF, 0x9FFFE, 0x9FFFF,
    0xAFFFE, 0xAFFFF, 0xBFFFE, 0xBFFFF, 0xCFFFE,
    0xCFFFF, 0xDFFFE, 0xDFFFF, 0xEFFFE, 0xEFFFF,
    0xFFFFE, 0xFFFFF, 0x10FFFE, 0x10FFFF
]
NOT_CHAR.extend(range(0xFDD0, 0xFDF0))

def get_char_name(code):
    if code in NOT_CHAR:
        return f'<not a character-{code:04X}>'
    if 0xD800 <= code <= 0xDFFF:
        return f'SURROGATE-{code:04X}'
    name = NAMES_LIST.get(
        code,
        {'name': None}
    )['name']
    
    if name is not None:
        return name
    else:
        for k, v in COMMON_NAMES.items():
            s, e = k
            if s <= code <= e:
                return v.replace('#', f'{code:04X}')
    
    return f'<undefined character-{code:04X}>'

def is_control(code):
    if get_char_name(code).startswith('<control'):
        return True
    return False


def is_reserved(code):
    if get_char_name(code).startswith('<reserved'):
        return True
    return False


def get_all_cmap_unicodes(font: TTFont) -> Set[int]:
    all_unicodes = set()
    
    if 'cmap' in font:
        for table in font['cmap'].tables:
            if table.cmap:
                all_unicodes.update(table.cmap.keys())
    
    return all_unicodes


fonts: list[str] = [
    'Ctrl-Ctrl',
    'PlangothicP1-Regular',
    'PlangothicP2-Regular',
    'NotoSansSC',
    'NotoEmoji-Regular',
    'NotoSansSuper',
    'NotoUnicode-7.3',
    'MonuTemp-0.920',
]

already_can_display_codes: set[int] = set()
res: dict[str, list[int]] = {}

for path in fonts:
    abs_path: str = os.path.abspath(
        os.path.join(os.path.dirname(CUR_FOLDER), 'fonts', path + '.ttf')
    )
    font: TTFont = TTFont(abs_path)
    codes: set[int] = get_all_cmap_unicodes(font)
    need_codes = list(filter(lambda code: code not in already_can_display_codes and (code in DEFINED_CHARACTER_LIST or is_control(code) or is_reserved(code)), codes))
    already_can_display_codes |= set(need_codes)
    res[path] = list(need_codes)

with open(OUT_PATH, 'wb') as f:
    f.write(zlib.compress(msgpack.packb(res)))

print('无法显示的字符：')
print(sorted(map(lambda c: hex(c)[2:], list(DEFINED_CHARACTER_LIST - set(already_can_display_codes)))))
