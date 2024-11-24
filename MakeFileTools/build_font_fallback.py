import os
import json
from fontTools.ttLib import TTFont

CUR_FOLDER = os.path.dirname(__file__)
DEFINED_CHARACTER_LIST = set(json.load(open(
    os.path.join(
        os.path.dirname(CUR_FOLDER),
        'ToolFiles', 'DefinedCharacterList.json'
    )
)))
fonts: list[str] = [
    'Ctrl-Ctrl',
    'PlangothicP1',
    'PlangothicP2',
    'Noto-Unicode',
    'NotoSansSC',
    'NotoSansKR',
    'Monu-Temp',
    'MonuHanp_3_55Ra_L3',
    'SegoeUI',
    'SegoeUISymbol',
    'SegoeUIHistoric',
    'SegoeUIEmoji',
    'MicrosoftTaiLe',
    'MicrosoftNewTaiLue',
    'Microsoft-Yi-Baiti',
    'MicrosoftPhagsPa',
    'MVBoli',
    'Ebrima',
    'NirmalaUI',
    'LeelawadeeUI',
    'MyanmarText',
    'Calibri',
    'Gadugi',
    'JavaneseText'
]

already_can_display_codes: set[int] = set()
res: dict[str, list[int]] = {}

for path in fonts:
    abs_path: str = os.path.abspath(
        os.path.join(os.path.dirname(CUR_FOLDER), 'fonts', path + '.ttf')
    )
    font: TTFont = TTFont(abs_path)
    cmap: dict[int, str] = font.getBestCmap()
    codes = cmap.keys()
    need_codes = list(filter(lambda code: code not in already_can_display_codes and code in DEFINED_CHARACTER_LIST, codes))
    already_can_display_codes |= set(need_codes)
    res[path] = list(need_codes)

json.dump(
    res,
    open(
        os.path.join(
            os.path.dirname(CUR_FOLDER),
            'ToolFiles', 'fontFallback.json'
        ), 'w'
    ),
    # indent=2,
    ensure_ascii=False
)
