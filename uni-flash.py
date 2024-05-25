from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
from fontTools.ttLib import TTFont

import os
import argparse
import shutil
import tempfile
import re
import csv
import json

UNICODE_RE = re.compile(r"^([0-9a-fA-F]|10)?[0-9a-fA-F]{0,4}$")

CUR_FOLDER = os.path.split(__file__)[0]

NOT_CHAR = [0xFFFE, 0xFFFF, 0x1FFFE, 0x1FFFF, 0x2FFFE, 0x2FFFF, 0x3FFFE, 0x3FFFF, 0x4FFFE, 0x4FFFF, 0x5FFFE, 0x5FFFF, 0x6FFFE, 0x6FFFF, 0x7FFFE, 0x7FFFF, 0x8FFFE, 0x8FFFF, 0x9FFFE, 0x9FFFF, 0xAFFFE, 0xAFFFF, 0xBFFFE, 0xBFFFF, 0xCFFFE, 0xCFFFF, 0xDFFFE, 0xDFFFF, 0xEFFFE, 0xEFFFF, 0xFFFFE, 0xFFFFF, 0x10FFFE, 0x10FFFF]
NOT_CHAR.extend(range(0xFDD0, 0xFDF0))
#CTRL_CHAR = (0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x7F, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F, 0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F)
HIDDEN_CHAR = set(
    [i for i in range(0x21)]  +
    [i for i in range(0x7F, 0xA1)] +
    [0xAD, 0x34F, 0x61C, 0x890,
     0x891, 0x180B, 0x180C, 0x180D,
     0x180E, 0x180F] +
    [i for i in range(0x2000, 0x2010)] +
    [0x2011] +
    [i for i in range(0x2028, 0x2030)] +
    [i for i in range(0x205F, 0x2070)] +
    [i for i in range(0x2400, 0x2422)] +
    [0x2424, 0x3000] +
    [i for i in range(0xFE00, 0xFE10)] +
    [0xFEFF] +
    [i for i in range(0xFFF9, 0xFFFD)] +
    [0x1107F, 0x11A47, 0x11D45, 0x11D97,
     0x11F42] +
    [i for i in range(0x13430, 0x13456)] +
    [0x16FE4, 0x1BC9D, 0x1BCA0, 0x1BCA1,
     0x1BCA2, 0x1BCA3, 0x1D159] +
    [i for i in range(0x1D173, 0x1D17B)] +
    [0x1DA9B, 0x1DA9C, 0x1DA9D, 0x1DA9E,
     0x1DA9F] +
    [i for i in range(0x1DAA1, 0x1DAB0)] +
    [0xE0001] +
    [i for i in range(0xE0020, 0xE0080)] +
    [i for i in range(0xE0100, 0xE01F0)]
)

with open(os.path.join(CUR_FOLDER, "Blocks.csv"), encoding="utf-8") as blocks_csv:
    reader = csv.reader(blocks_csv, delimiter='|')
    BLOCKS = {tuple(map(lambda rang: int(rang, 16), line[0].split(".."))): (line[2], "-".join(map(lambda rang: "U+" + rang, line[0].split(".."))), line[-1]) for line in reader}.items()

NAME_LIST = json.load(open(os.path.join(CUR_FOLDER, "NameList.json"), encoding="utf8"))
DEFINED_CHARACTER_LIST = set(json.load(open(os.path.join(CUR_FOLDER, "DefinedCharacterList.json"), encoding="utf8")))
EXAMPLE_FONT_SIZE = 220

font_path_times = os.path.join(CUR_FOLDER, "TH-Times.ttf")
font_path_kr = os.path.join(CUR_FOLDER, "NotoSansKR-Regular.ttf")
font_path_d0 = os.path.join(CUR_FOLDER, "TH-Disp-P0.ttf")
font_path_p1 = os.path.join(CUR_FOLDER, "PlangothicP1-Regular(allideo).ttf")
font_path_p2 = os.path.join(CUR_FOLDER, "PlangothicP2-Regular.ttf")
font_path_mh = os.path.join(CUR_FOLDER, "MonuHani-9.69.ttf")
font_path_ctrl = os.path.join(CUR_FOLDER, "CtrlCtrl-1.101.ttf")
font_path_mht = os.path.join(CUR_FOLDER, "MonuHanp-3.001.ttf")
font_path_last = os.path.join(CUR_FOLDER, "MonuLast-8.16-1.ttf")
font_path_noto = os.path.join(CUR_FOLDER, "NotoUnicode-7.3.ttf")

block_name_font_path = os.path.join(CUR_FOLDER, "AlibabaPuHuiTi-3-55-Regular.ttf")
range_font_path = os.path.join(CUR_FOLDER, "AlibabaPuHuiTi-3-55-Regular.ttf")
code_font_path = os.path.join(CUR_FOLDER, "monaco.ttf")
name_font_path = os.path.join(CUR_FOLDER, "AlibabaPuHuiTi-3-55-Regular.ttf")
hex_font_path = os.path.join(CUR_FOLDER, "monaco.ttf")
other_font_path = os.path.join(CUR_FOLDER, "AlibabaPuHuiTi-3-55-Regular.ttf")

tfont_times = TTFont(font_path_times)
tfont_kr = TTFont(font_path_kr)
tfont_d0 = TTFont(font_path_d0)
tfont_p1 = TTFont(font_path_p1)
tfont_p2 = TTFont(font_path_p2)
tfont_noto = TTFont(font_path_noto)

font_cmap_times = tfont_times["cmap"].tables
font_cmap_kr = tfont_kr["cmap"].tables
font_cmap_d0 = tfont_d0["cmap"].tables
font_cmap_p1 = tfont_p1["cmap"].tables
font_cmap_p2 = tfont_p2["cmap"].tables
font_cmap_noto = tfont_noto["cmap"].tables

font_times = ImageFont.truetype(font_path_times, EXAMPLE_FONT_SIZE)
font_kr = ImageFont.truetype(font_path_kr, EXAMPLE_FONT_SIZE)
font_d0 = ImageFont.truetype(font_path_d0, EXAMPLE_FONT_SIZE)
font_p1 = ImageFont.truetype(font_path_p1, EXAMPLE_FONT_SIZE)
font_p2 = ImageFont.truetype(font_path_p2, EXAMPLE_FONT_SIZE)
font_mh = ImageFont.truetype(font_path_mh, EXAMPLE_FONT_SIZE)
font_ctrl = ImageFont.truetype(font_path_ctrl, EXAMPLE_FONT_SIZE)
font_mht = ImageFont.truetype(font_path_mht, EXAMPLE_FONT_SIZE)
font_last = ImageFont.truetype(font_path_last, EXAMPLE_FONT_SIZE)
font_noto = ImageFont.truetype(font_path_noto, EXAMPLE_FONT_SIZE)

def merge_iterables(*iterables):
    result_list = []
    for subiterable in iterables:
        result_list.extend(subiterable)
    return result_list


def get_all_codes_from_font(fp):
    font = TTFont(fp)
    codes = sorted(list(set(merge_iterables(*map(lambda table: list(table.cmap.keys()), font["cmap"].tables)))))
    return codes


def check_glyph_in_font(font_cmap, code):
    for table in font_cmap:
        if code in table.cmap:
            return True
    return False


def get_char_name(code):
    code_u = "U+" + hex(code)[2:].upper()
    
    if code in NOT_CHAR:
        return f"<not a character-{code_u}>"
    if 0xD800 <= code <= 0xDFFF:
        return f"Surrogate-{code_u}"
    if (0xE000 <= code <= 0xF8FF or
        0xF0000 <= code <= 0xFFFFD or
        0x100000 <= code <= 0x10FFFD):
        return f"Private Use-{code_u}"
    if (0x3400 <= code <= 0x4DBF or
        0x4E00 <= code <= 0x9FFF or
        0x20000 <= code <= 0x2A6DF or
        0x2A700 <= code <= 0x2B738 or
        0x2B740 <= code <= 0x2B81D or
        0x2B740 <= code <= 0x2B81D or
        0x2B820 <= code <= 0x2CEA1 or
        0x2CEB0 <= code <= 0x2EBE0 or
        0x2EBF0 <= code <= 0x2EE5D or
        0x30000 <= code <= 0x3134A or
        0x31350 <= code <= 0x323AF):
        return f"CJK Unified Ideograph-{code_u}"
    if 0xAC00 <= code <= 0xD7A3:
        return f"Hangul Syllable-{code_u}"
    if (0x17000 <= code <= 0x187F7 or
        0x18D00 <= code <= 0x18D08):
        return f"Tangut-{code_u}"
    return NAME_LIST.get(str(code), {"name": f"<undefined character-{code_u}>"})['name']


def get_char_alias(code):
    return NAME_LIST.get(str(code), {"alias": []})['alias']


def get_char_comment(code):
    return NAME_LIST.get(str(code), {"comment": []})['comment']


def get_char_version(code):
    if (0xE000 <= code <= 0xF8FF or
        0xF0000 <= code <= 0xFFFFD or
        0x100000 <= code <= 0x10FFFD):
        return "6.0.0 or earlier"
    if (0x3400 <= code <= 0x4DB5 or
        0x4E00 <= code <= 0x9FCB or
        0x20000 <= code <= 0x2A6D6 or
        0x2A700 <= code <= 0x2B734 or
        0x2B740 <= code <= 0x2B81D):
        return "6.0.0 or earlier"
    if (code == 0x9FCC):
        return "6.1.0"
    if (0x9FCD <= code <= 0x9FD5 or
        0x2B820 <= code <= 0x2CEA1):
        return "8.0.0"
    if (0x17000 <= code <= 0x187EC):
        return "9.0.0"
    if (0x9FD6 <= code <= 0x9FEA or
        0x2CEB0 <= code <= 0x2EBE0):
        return "10.0.0"
    if (0x9FEB <= code <= 0x9FEF or
        0x187ED <= code <= 0x187F1):
        return "11.0.0"
    if (0xAC00 <= code <= 0xD7A3):
        return "6.0.0 or earlier"
    if (0x187F2 <= code <= 0x187F7):
        return "12.0.0"
    if (0x4DB6 <= code <= 0x4DBF or
        0x9FF0 <= code <= 0x9FFC or
        0x2A6D7 <= code <= 0x2A6DD or
        0x30000 <= code <= 0x3134A):
        return "13.0.0"
    if (0x18D00 <= code <= 0x18D08):
        return "13.0.0"
    if (0x9FFD <= code <= 0x9FFF or
        0x2A6DE <= code <= 0x2A6DF or
        0x2B735 <= code <= 0x2B738):
        return "14.0.0"
    if (code == 0x2B739 or
        0x31350 <= code <= 0x323AF):
        return "15.0.0"
    if (0x2EBF0 <= code <= 0x2EE5D):
        return "15.1.0"
    return NAME_LIST.get(str(code), {"version": "<future version>"})['version']


def is_defined(code):
    if (code in DEFINED_CHARACTER_LIST or
       0xE000 <= code <= 0xF8FF or
       0xF0000 <= code <= 0xFFFFD or
       0x100000 <= code <= 0x10FFFD):
        return True
    return False


def is_private_use(code):
    if (0xE000 <= code <= 0xF8FF or
       0xF0000 <= code <= 0xFFFFD or
       0x100000 <= code <= 0x10FFFD):
        return True
    return False


def inverse_color(c):
    return (255 - c[0], 255 - c[1], 255 - c[2])


def gray(c):
    return ((_l := int(c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114)), _l, _l)


def auto_width(string, font, width):
    char_widths = [(bbox := font.getbbox(char))[2] - bbox[0] for char in string]
    current_width = 0
    processed_string = ''
    
    if (bbox := font.getbbox(string))[2] - bbox[0] <= width:
        return string

    for i in range(len(string)):
        char = string[i]
        char_width = char_widths[i]
        
        if char == ' ' and current_width + char_width > width:
            processed_string += '\n  '
            current_width = (bbox := font.getbbox("  "))[2] - bbox[0]
        elif current_width + char_width > width:
            processed_string_list = list(processed_string)
            last_space_index = processed_string.rfind(" ")
            processed_string_list[last_space_index] = "\n  "
            processed_string = "".join(processed_string_list)
            processed_string += char
            current_width = sum(char_widths[last_space_index+1:i+1]) + (bbox := font.getbbox("  "))[2] - bbox[0]
        else:
            processed_string += char
            current_width += char_width
    return processed_string


def to_utf8_hex(code):
    if 0 <= code <= 0x7F:
        return hex(code)[2:].upper().zfill(2)
    if 0x80 <= code <= 0x7FF:
        return hex(
            (((code >> 6) + 0b11000000) << 8) +
            ((code & 0b111111) + 0b10000000)
        )[2:].upper()
    if 0x800 <= code <= 0xFFFF:
        return hex(
            (((code >> 12) + 0b11100000) << 16) +
            ((((code >> 6) & 0b111111) + 0b10000000) << 8) +
            ((code & 0b111111) + 0b10000000)
        )[2:].upper()
    if 0x10000 <= code <= 0x10FFFF:
        return hex(
            (((code >> 18) + 0b11110000) << 24) +
            ((((code >> 12) & 0b111111) + 0b10000000) << 16) +
            ((((code >> 6) & 0b111111) + 0b10000000) << 8) +
            ((code & 0b111111) + 0b10000000)
        )[2:].upper()


def to_utf16be_hex(code):
    if 0 <= code <= 0xFFFF:
        return hex(code)[2:].upper().zfill(4)
    else:
        return hex(
            ((((code - 0x10000) >> 10) + 0xD800) << 16) + 
            (((code - 0x10000) & 0b1111111111) + 0xDC00)
        )[2:].upper().zfill(8)


def to_utf16le_hex(code):
    if 0 <= code <= 0xFFFF:
        be = hex(code)[2:].upper().zfill(4)
        return be[2:4] + be[:2]
    else:
        be = hex(
            ((((code - 0x10000) >> 10) + 0xD800) << 16) + 
            (((code - 0x10000) & 0b1111111111) + 0xDC00)
        )[2:].upper().zfill(8)
        return be[2:4] + be[:2] + be[6:8] + be[4:6]


def gap(s):
    return " ".join([s[i:i+2] for i in range(0, len(s), 2)])


bc = 0
bgcs = tuple(map(
    lambda c: (c, gray(inverse_color(c))),
    [
        (171, 223, 86),
        (109, 231, 78),
        (104, 245, 159),
        (0, 190, 157),
        (0, 203, 129),
        (168, 253, 154),
        (153, 254, 169),
        (152, 252, 202),
        (152, 254, 235),
        (151, 236, 253),
        (51, 226, 253),
        (52, 181, 223),
        (0, 149, 224),
        (205, 155, 255),
        (171, 155, 255),
        (238, 154, 255),
        (255, 154, 240),
        (254, 154, 204),
        (255, 154, 170),
        (252, 171, 154),
        (251, 201, 154),
        (253, 236, 153),
        (238, 254, 153),
        (207, 255, 155)
    ]
))
def generate_a_image(w, h, _code, c_font, b_font, o_font, r_font, h_font, n_font, fonts, use_last, show_private, skip_no_glyph, skip_undefined, show_undefined, skip_long):
    if (skip_long and 0x323B0 <= _code <= 0xDFFFF) or (skip_undefined and not is_defined(_code)):
        return "skip"
    font = None
    for _font, font_cmap in fonts:
        if check_glyph_in_font(font_cmap, _code):
            font = _font
            break
    if skip_no_glyph and font is None:
        return "skip"
    if _code == 0xA:
        text = "␊"
    elif _code == 0xD:
        text = "␍"
    else:
        text = chr(_code)
    utf8 = "UTF-8: " + gap(to_utf8_hex(_code))
    utf16le = "UTF-16LE: " + gap(to_utf16le_hex(_code))
    utf16be = "UTF-16BE: " + gap(to_utf16be_hex(_code))
    
    mode = "RGB" if bc else "L"
    
    if not bc:
        bgc = 20
        textc = 235
    r = ("未定义", "未定义", "undefined")
    for index, item in enumerate(BLOCKS):
        if item[0][0] <= _code <= item[0][1]:
            r = item[1]
            if bc:
                bgc, textc = bgcs[(index + 1) % len(bgcs)]
            break
    else:
        if bc:
            bgc, textc = ((20, 20, 20), (235, 235, 235))
    
    if font is not None:
        ...
    elif _code in HIDDEN_CHAR:
        font = font_ctrl
    elif 0x20000 <= _code <= 0x2A6DF:
        font = font_mht
    elif 0x2A700 <= _code <= 0x2FFFF and check_glyph_in_font(font_cmap_p1, _code):
        font = font_p1
    elif 0x30000 <= _code <= 0x3FFFF and check_glyph_in_font(font_cmap_p2, _code):
        font = font_p2
    elif (0x4E00 <= _code <= 0x9FFF or
          0x2E80 <= _code <= 0x2EF3 or
          0x2F00 <= _code <= 0x2FD5 or
          0x2FF0 <= _code <= 0x2FFF or
          0x31C0 <= _code <= 0x31E3 or
          _code == 0x31EF or
          0x3400 <= _code <= 0x4DBF):
        font = font_mh
    elif check_glyph_in_font(font_cmap_kr, _code):
        font = font_kr
    elif check_glyph_in_font(font_cmap_noto, _code):
        font = font_noto
    elif check_glyph_in_font(font_cmap_times, _code):
        font = font_times
    elif check_glyph_in_font(font_cmap_d0, _code):
        font = font_d0
    
    code = "U+" + hex(_code)[2:].upper().zfill(4)
    image = Image.new(mode, (w, h), color=bgc)

    draw = ImageDraw.Draw(image)
    
    bbox = c_font.getbbox(code)
    code_width = bbox[2] - bbox[0]
    code_height = bbox[3] - bbox[1]
    code_x = w - code_width - 15
    code_y = h - code_height*1.5 - 5
    draw.text((code_x, code_y), code, font=c_font, fill=textc)
    
    bbox = h_font.getbbox(utf8)
    utf8_width = bbox[2] - bbox[0]
    utf8_height = bbox[3] - bbox[1]
    utf8_y = h - utf8_height*1.5 - 5
    draw.text(((w - utf8_width)/2, utf8_y), utf8, fill=textc, font=h_font)
    
    bbox = h_font.getbbox(utf16le)
    utf16le_width = bbox[2] - bbox[0]
    utf16le_height = bbox[3] - bbox[1]
    utf16le_y = utf8_y - utf16le_height*1.5 - 5
    draw.text(((w - utf16le_width)/2, utf16le_y), utf16le, fill=textc, font=h_font)
    
    bbox = h_font.getbbox(utf16be)
    utf16be_width = bbox[2] - bbox[0]
    utf16be_height = bbox[3] - bbox[1]
    draw.text(((w - utf16be_width)/2, utf16le_y - utf16be_height*1.5 - 5), utf16be, fill=textc, font=h_font)

    block_en = auto_width(r[2], n_font, (w - utf8_width)/2)
    bbox = draw.textbbox(xy=(0, 0), text=block_en, font=n_font)
    block_en_height = bbox[3] - bbox[1]
    block_en_y = h - block_en_height*1.25 - 5
    draw.text((35, block_en_y), block_en, font=n_font, fill=textc)
    
    bbox = b_font.getbbox(r[0])
    block_height = bbox[3] - bbox[1]
    block_y = block_en_y - block_height - 5
    draw.text((35, block_y), r[0], font=b_font, fill=textc)

    bbox = r_font.getbbox(r[1])
    r_height = bbox[3] - bbox[1]
    r_y = block_y - r_height - 5
    draw.text((35, r_y), r[1], font=r_font, fill=textc)
    
    name = auto_width(get_char_name(_code), n_font, w - 35)
    bbox = draw.textbbox(xy=(0, 0), text=name, font=n_font)
    name_height = bbox[3] - bbox[1]
    draw.text((35, r_y-name_height-5), name, font=n_font, fill=textc)
    
    alias = ", ".join(get_char_alias(_code))
    if alias:
        alias = auto_width("aliases: " + alias, n_font, w-35)
    else:
        alias = "aliases: <no aliases>"
    bbox = draw.textbbox(xy=(0, 0), text=alias, font=n_font)
    alias_height = bbox[3] - bbox[1]
    draw.text((35, 5), alias, font=n_font, fill=textc)
        
    comment = ".".join(get_char_comment(_code))
    if comment:
        comment = auto_width("comment: " + comment + ".", n_font, w-35)
    else:
        comment = "comment: <no comment>"
    bbox = draw.textbbox(xy=(0, 0), text=comment, font=n_font)
    comment_height = bbox[3] - bbox[1]
    draw.text((35, alias_height + 10), comment, font=n_font, fill=textc)
    
    version = "version: " + get_char_version(_code)
    draw.text((35, alias_height + comment_height + 15), version, font=n_font, fill=textc)
    
    if is_defined(_code) and (not is_private_use(_code)):
        if font is not None:
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = w/2 - text_width/2
            y = h/2 - text_height/2
            draw.text((x, y), text, font=font, fill=textc)
    elif show_private and font is not None and is_private_use(_code):
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = w/2 - text_width/2
        y = h/2 - text_height/2
        draw.text((x, y), text, font=font, fill=textc)
    elif show_undefined and font is not None and not is_defined(_code):
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = w/2 - text_width/2
        y = h/2 - text_height/2
        draw.text((x, y), text, font=font, fill=textc)
    elif use_last:
        bbox = font_last.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = w/2 - text_width/2
        y = h/2 - text_height/2
        draw.text((x, y), text, font=font_last, fill=textc)
    else:
        text = None
        if _code in NOT_CHAR:
            text = f"非字符 {code}"
        elif 0xD800 <= _code <= 0xDB7F:
            text = f"高位替代字符 {code}"
        elif 0xDB80 <= _code <= 0xDBFF:
            text = f"高位私用替代字符 {code}"
        elif 0xDC00 <= _code <= 0xDFFF:
            text = f"低位替代字符 {code}"
        elif (0xE000 <= _code <= 0xF8FF or
              0xF0000 <= _code <= 0xFFFFD or
              0x100000 <= _code <= 0x10FFFD):
            text = f"私用区字符 {code}"
        else:
            text = f"未定义字符 {code}"
        bbox = o_font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = w/2 - text_width/2
        y = h/2 - text_height/2
        draw.text((x, y), text, font=o_font, fill=textc)
    return image


def generate_unicode_flash(width, height, out_path, codes, fps, _fonts, c_font, b_font, o_font, r_font, h_font, n_font, use_last, no_dynamic, show_private, no_music, skip_no_glyph, skip_undefined, save_bmp, show_undefined, skip_long, music):
    fonts = tuple(zip(map(lambda f: ImageFont.truetype(f, EXAMPLE_FONT_SIZE), _fonts), map(lambda f: TTFont(f)["cmap"].tables, _fonts)))
    a = []
    count = 0
    temp_dir = os.path.join(CUR_FOLDER, "res")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    #with tempfile.TemporaryDirectory() as temp_dir:
    print(f"gif dir: {temp_dir}")
    in_p = os.path.join(temp_dir, "input.txt")
    
    with open(in_p, "w", encoding="utf8") as f:
        for code in tqdm(codes):
            try:
                image = generate_a_image(width, height, code, c_font, b_font, o_font, r_font, h_font, n_font, fonts, use_last, show_private, skip_no_glyph, skip_undefined, show_undefined, skip_long)
            except OSError:
                print(f"在U+{hex(code)[2:].upper().zfill(4)}处发生raster overflow，已跳过。")
                continue
            if image == "skip":
                continue
            if bc or no_dynamic:
                if save_bmp:
                    ires_path = os.path.join(temp_dir, f"{code}.bmp")
                else:
                    ires_path = os.path.join(temp_dir, f"{code}.gif")
                image.save(ires_path)
                f.write(f"file '{ires_path}'\n")
            else:
                a.append(image)
                if len(a) % 300 == 0 and len(a) != 0:
                    count += 1
                    ires_path = os.path.join(temp_dir, f"{count}.gif")
                    a[0].save(ires_path, save_all=True, append_images=a[1:], optimize=False, duration=int(1000/fps), loop=0)
                    f.write(f"file '{ires_path}'\n")
                    a.clear()
        if not bc and not no_dynamic and a:
            count += 1
            ires_path = os.path.join(temp_dir, f"{count}.gif")
            a[0].save(ires_path, save_all=True, append_images=a[1:], optimize=False, duration=int(1000/fps), loop=0)
            f.write(f"file '{ires_path}'\n")
            a.clear()
    if not open(in_p, encoding="utf8").read():
        raise ValueError('你这个傻逼，图片全都跳过了，我日你仙人！')
    if no_music:
        os.system(f'ffmpeg -r {fps} -f concat -safe 0 -i {os.path.abspath(in_p)} -pix_fmt yuv420p {os.path.abspath(out_path)} -hide_banner')
    else:
        os.system(f'ffmpeg -r {fps} -f concat -safe 0 -i {os.path.abspath(in_p)} -pix_fmt yuv420p {os.path.join(temp_dir, "out.mp4")} -hide_banner')
        os.system(f'ffmpeg -i {os.path.join(temp_dir, "out.mp4")} -stream_loop -1 -i {music} -c copy -shortest {os.path.abspath(out_path)} -hide_banner')


if __name__ == "__main__":
    def _ve(v):
        raise ValueError(f"无效Unicode码位 {v}")


    c_font = ImageFont.truetype(code_font_path, 40)
    b_font = ImageFont.truetype(block_name_font_path, 45)
    o_font = ImageFont.truetype(other_font_path, 40)
    r_font = ImageFont.truetype(range_font_path, 40)
    h_font = ImageFont.truetype(hex_font_path, 25)
    n_font = ImageFont.truetype(name_font_path, 30)
    
    parser = argparse.ArgumentParser(description="这是一个Unicode快闪生成脚本")
    parser.add_argument('fps', type=float,
                        help='帧率，建议15，可以为小数')
    parser.add_argument('-width', type=int, default=1920,
                        help='视频宽度，默认1920')
    parser.add_argument('-height', type=int, default=1080,
                        help='视频宽度，默认1080')
    parser.add_argument('-fonts', type=str, nargs="*", default=[],
                        help='字体路径列表，按输入顺序计算优先级')
    parser.add_argument('-out_path', type=str, default=os.path.join(CUR_FOLDER, "res.mp4"),
                        help="生成视频的路径")
    parser.add_argument('-use_last', action='store_true',
                        help="使用MonuLast(典迹末境)字体")
    parser.add_argument('-no_dynamic', action='store_true',
                        help='以静态图片模式保存临时图片')
    parser.add_argument('-show_private', action='store_true',
                        help='展示私用区字符')
    parser.add_argument('-show_undefined', action='store_true',
                        help='展示在自定义字体中有字形的未定义字符')
    parser.add_argument('-no_music', action='store_true',
                        help='不添加音乐')
    parser.add_argument('-skip_no_glyph', action='store_true',
                        help='跳过在所有自定义字体中都没有字形的字符')
    parser.add_argument('-skip_undefined', action='store_true',
                        help='跳过未定义字符、非字符、代理字符等')
    parser.add_argument('-skip_long', action='store_true',
                        help='跳过U+323B0-U+DFFFF')
    parser.add_argument('-music', type=str, default=os.path.join(CUR_FOLDER, "UFM.mp3"),
                        help='背景音乐文件路径')
    parser.add_argument('-save_bmp', action='store_true',
                        help='存为bmp格式，仅在-no_dynamic启用时生效，能大幅增加生成速度，但有更大概率抛出OSError: raster overflow错误。')
    chars_group = parser.add_mutually_exclusive_group(required=True)
    chars_group.add_argument('-rang', type=str, nargs=2,
                            help='快闪字符的范围，不带0x的十六进制数')
    chars_group.add_argument('-from_file', type=argparse.FileType('r'),
                            help='通过一个文件获取将要快闪的字符')
    chars_group.add_argument('-from_font', action='store_true',
                            help='从字体文件列表获取将要快闪的字符')
    args = parser.parse_args()
    if args.rang:
        if not (UNICODE_RE.search(args.rang[0]) and UNICODE_RE.search(args.rang[1])):
            raise ValueError('Unicode码位无效')
        s = int(args.rang[0], 16)
        e = int(args.rang[1], 16)
        codes = range(s, e+1)
    elif args.from_file:
        codes = map(lambda v: int(v) if UNICODE_RE.search(v) else _ve(v), args.from_file.read().split(","))
    elif args.from_font:
        codes = sorted(list(set(merge_iterables(*[get_all_codes_from_font(font) for font in args.fonts]))))
    generate_unicode_flash(args.width, args.height, args.out_path, codes, args.fps, args.fonts, c_font, b_font, o_font, r_font, h_font, n_font, args.use_last, args.no_dynamic, args.show_private, args.no_music, args.skip_no_glyph, args.skip_undefined, args.save_bmp, args.show_undefined, args.skip_long, args.music)