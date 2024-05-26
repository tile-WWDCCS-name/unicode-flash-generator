import os
import json
import re

NAME_LIST_PATH = "/storage/emulated/0/下载/git/unicode快闪/NameList"
OUT_PATH = "/storage/emulated/0/下载/git/unicode快闪/NameList.json"
CTRL_NAME = {
    k: v for k, v in zip(tuple(range(0x20)) + tuple(range(0x7F, 0x100)), "NUL SOH STX ETX EOT ENQ ACK BEL BS HT LF VT FF CR SO SI DLE DC1 DC2 DC3 DC4 NAK SYN ETB CAN EM SUB ESC FS GS RS US DEL XXX(PAD) XXX(HOP) BPH NBH IND NEL SSA ESA HTS HTJ VTS PLD PLU R1 SS2 SS3 DCS PU1 PU2 STS CCH MW SPA EPA SOS XXX(SGCI) SCI CSI ST OSC PM APC".split())
}

def edit_reserved(o):
    return f"<reserved - U+{hex(o.id)[2:].upper().zfill(4)}, original U+{o.xref[0]}>"


UNICODE_RE = re.compile(r"^([0-9a-fA-F]|10)?[0-9a-fA-F]{0,4}$")

characters = {}
class OneCharacter:
    id = None
    name = None
    version = 0
    comment = []
    alias = []
    formal = []
    xref = []
    vari = []
    decomp = []
    compat = []
    def __init__(self, code, name, version):
        self.id = int(code, 16)
        self.name = name
        self.version = version
        self.comment = []
        self.alias = []
        self.formal = []
        self.xref = []
        self.vari = []
        self.decomp = []
        self.compat = []
    def update(self):
        global characters
        if self.id in characters:
            self.version = characters[self.id].version
        characters[self.id] = self
    def insert(self):
        global cur
        def list_to_str(l):
            return '\'' + '\n'.join(l) + '\'' if len(l) > 0 else 'NULL'
        exp = f'INSERT INTO name_table (id, words, name, version, comment, alias, formal, xref, vari, decomp, compat) values ({self.id}, \'{" ".join([self.name] + self.alias + self.formal)}\', \'{self.name}\', {self.version}, {list_to_str(self.comment)}, {list_to_str(self.alias)}, {list_to_str(self.formal)}, {list_to_str(self.xref)}, {list_to_str(self.vari)}, {list_to_str(self.decomp)}, {list_to_str(self.compat)});'
        try:
            cur.execute(exp)
        except:
            print(exp)
            raise


class CharacterEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, OneCharacter):
            return {"code": "U+" + hex(obj.id)[2:].upper().zfill(4),
                    "name": edit_reserved(obj) if (n := obj.name) == "<reserved>" else n,
                    "version": obj.version,
                    "comment": obj.comment,
                    "alias": obj.alias,
                    "formal alias": obj.formal,
                    "cross ref": obj.xref,
                    "variation": obj.vari,
                    "decomposition": obj.decomp,
                    "compat mapping": obj.compat}
        return super().default(obj)


def find_files_by_extension(directory, extension):
    file_list = []
    for file in os.listdir(directory):
        if file.endswith(extension):
            file_list.append(os.path.join(directory, file))
    return file_list


for fp in sorted(find_files_by_extension(NAME_LIST_PATH, ".txt"), key=lambda v: int(os.path.splitext(os.path.split(v)[1])[0].replace(".", ""))):
    version = os.path.splitext(os.path.split(fp)[1])[0]
    if version == "6.0.0":
        version = "6.0.0 or earlier"
    with open(fp) as f:
        current = None
        for line in f.readlines():
            def oneline(line):
                global current
                if len(line) == 0:
                    return
                elif line[0] in ['@', ';']:
                    return
                elif line[0] == '\t':
                    if current is None:
                        return
                    if len(line) < 3:
                        print(f'Malformed line: {line}', file=sys.stderr)
                        return
                    if line[1] == '\t':
                        return
                    if line[1] == '*':
                        current.comment.append(line[3:].replace('\'', '"'))
                    if line[1] == '=':
                        current.alias.append(line[3:].replace('\'', '"'))
                    if line[1] == '%':
                        current.formal.append(line[3:].replace('\'', '"'))
                    if line[1] == 'x':
                        current.xref.append("U+" + (line.split(' ')[-1][:-1] if line[3] == '(' else line[3:]).replace('\'', '"'))
                    if line[1] == '~':
                        current.vari.append(' '.join(("U+" + s if UNICODE_RE.search(s) else s) for s in line[3:].split(' ')).replace('\'', '"').rstrip(' '))
                    if line[1] == ':':
                        current.decomp.append(' '.join(("U+" + s if UNICODE_RE.search(s) else s) for s in line[3:].split(' ') if re.match('^[0-9A-F]+$', s)).replace('\'', '"'))
                    if line[1] == '#':
                        current.compat.append(' '.join(("U+" + s if UNICODE_RE.search(s) else s) for s in line[3:].split(' ') if re.match('^([0-9A-F]+|<.*>)$', s)).replace('\'', '"'))
                else:
                    if current is not None:
                        current.update()
                    tokens = line.split('\t')
                    if len(tokens) != 2:
                        print(f'Malformed line: {line}', file=sys.stderr)
                        return
                    if tokens[1] == '<not a character>':
                        current = None
                        return
                    if tokens[1] == '<control>':
                        tokens[1] = f'<control - {CTRL_NAME[int(tokens[0], 16)]}>'
                    current = OneCharacter(tokens[0], tokens[1], version)
            oneline(line.replace("\n", ""))
            if current is not None:
                current.update()


json.dump(characters, open(OUT_PATH, "w"), cls=CharacterEncoder, indent=2, ensure_ascii=False)