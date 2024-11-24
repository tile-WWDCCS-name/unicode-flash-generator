import os
import json

CUR_FOLDER = os.path.dirname(__file__)
NAMES_LIST_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'ToolFiles', 'NamesList.json')
NAMES_LIST = json.load(open(NAMES_LIST_PATH))

res = list(map(int, NAMES_LIST.keys()))

res.extend(range(0x3400, 0x4DBF + 1))
res.extend(range(0x4E00, 0x9FFF + 1))
res.extend(range(0x20000, 0x2A6DF + 1))
res.extend(range(0x2A700, 0x2B738 + 1))
res.extend(range(0x2B740, 0x2B81D + 1))
res.extend(range(0x2B820, 0x2CEA1 + 1))
res.extend(range(0x2CEB0, 0x2EBE0 + 1))
res.extend(range(0x2EBF0, 0x2EE5D + 1))
res.extend(range(0x30000, 0x3134A + 1))
res.extend(range(0x31350, 0x323AF + 1))

res.extend(range(0xAC00, 0xD7A3 + 1))

res.extend(range(0x17000, 0x187F7 + 1))
res.extend(range(0x18D00, 0x18D08 + 1))
res.sort()

json.dump(
    res,
    open(
        os.path.join(
            os.path.dirname(CUR_FOLDER),
            'ToolFiles', 'DefinedCharacterList.json'
        ), 'w'
    ),
)
