from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
from fontTools.ttLib import TTFont
import cv2
import numpy as np

import os
import re
import csv
import json
import bisect
import itertools

# 常量的定义
UNICODE_RE = re.compile(r'^([0-9a-fA-F]|10)?[0-9a-fA-F]{0,4}$')

CUR_FOLDER = os.path.dirname(__file__)

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
with open(
    os.path.join(CUR_FOLDER, 'Blocks.csv'),
    encoding='utf-8'
) as blocks_csv:
    reader = list(csv.reader(blocks_csv, delimiter='|'))
    BLOCK_INFOS = {
        line[2]: (
            line[2],
            line[-1],
            '-'.join(map(lambda rang: 'U+' + rang, line[0].split('..'))),
            tuple(map(lambda i: int(i, 16), line[0].split('..')))
        ) for line in reader
    }
    BLOCK_START_LIST = [int(line[0].split('..')[0], 16) for line in reader]
    BLOCK_NAMES = [line[2] for line in reader]

with open(
    os.path.join(CUR_FOLDER, 'Planes.csv'),
    encoding='utf-8'
) as blocks_csv:
    reader = list(csv.reader(blocks_csv, delimiter='|'))
    PLANES = {
        tuple(map(lambda rang: int(rang, 16), line[0].split('..'))): (
             *line[1:],
             '-'.join(map(lambda rang: 'U+' + rang, line[0].split('..')))
        ) for line in reader
    }.items()


NAME_LIST = json.load(open(
    os.path.join(CUR_FOLDER, 'NameList.json'),
    encoding='utf8'
))
DEFINED_CHARACTER_LIST = set(json.load(open(
    os.path.join(CUR_FOLDER, 'DefinedCharacterList.json'),
    encoding='utf8'
)))
EXAMPLE_FONT_SIZE = 220
VARI_VIRAM_PUNCTUATION4 = {
    0x9E4,
    0xA64,
    0xAE4,
    0xB64,
    0xBE4,
    0xC64,
    0xCE4,
    0xD64
}
VARI_VIRAM_PUNCTUATION5 = {
    0x9E5,
    0xA65,
    0xAE5,
    0xB65,
    0xBE5,
    0xC65,
    0xCE5,
    0xD65
}

VERSION_RANGES = [
    ((0xE000, 0xF8FF), '6.0.0 or earlier'),
    ((0xF0000, 0xFFFFD), '6.0.0 or earlier'),
    ((0x100000, 0x10FFFD), '6.0.0 or earlier'),
    ((0x3400, 0x4DB5), '6.0.0 or earlier'),
    ((0x4E00, 0x9FCB), '6.0.0 or earlier'),
    ((0x20000, 0x2A6D6), '6.0.0 or earlier'),
    ((0x2A700, 0x2B734), '6.0.0 or earlier'),
    ((0x2B740, 0x2B81D), '6.0.0 or earlier'),
    ((0x9FCC, 0x9FCC), '6.1.0'),
    ((0x9FCD, 0x9FD5), '8.0.0'),
    ((0x2B820, 0x2CEA1), '8.0.0'),
    ((0x17000, 0x187EC), '9.0.0'),
    ((0x9FD6, 0x9FEA), '10.0.0'),
    ((0x2CEB0, 0x2EBE0), '10.0.0'),
    ((0x9FEB, 0x9FEF), '11.0.0'),
    ((0x187ED, 0x187F1), '11.0.0'),
    ((0xAC00, 0xD7A3), '6.0.0 or earlier'),
    ((0x187F2, 0x187F7), '12.0.0'),
    ((0x4DB6, 0x4DBF), '13.0.0'),
    ((0x9FF0, 0x9FFC), '13.0.0'),
    ((0x2A6D7, 0x2A6DD), '13.0.0'),
    ((0x30000, 0x3134A), '13.0.0'),
    ((0x18D00, 0x18D08), '13.0.0'),
    ((0x9FFD, 0x9FFF), '14.0.0'),
    ((0x2A6DE, 0x2A6DF), '14.0.0'),
    ((0x2B735, 0x2B738), '14.0.0'),
    ((0x2B739, 0x2B739), '15.0.0'),
    ((0x31350, 0x323AF), '15.0.0'),
    ((0x2EBF0, 0x2EE5D), '15.1.0'),
]

VERSION_RANGE_START = [i[0][0] for i in VERSION_RANGES]
VERSION_RANGE_END = [i[0][1] for i in VERSION_RANGES]


# 字体相关的函数
def get_font_name(names):
    for record in names:
        if (
            record.nameID == 4 and
            record.langID == 0x404 and
            record.toUnicode()
        ):
            return record.toStr()
    for record in names:
        if record.nameID == 4 and record.toUnicode() != '':
            return record.toStr()


def get_all_codes_from_font(font):
    codes = set(font.getBestCmap().keys())
    return codes


# 字符信息相关的函数
def get_char_name(code):
    code_u = 'U+' + hex(code)[2:].upper()

    if code in NOT_CHAR:
        return f'<not a character-{code_u}>'
    if 0xD800 <= code <= 0xDFFF:
        return f'Surrogate-{code_u}'
    if (
        0xE000 <= code <= 0xF8FF or
        0xF0000 <= code <= 0xFFFFD or
        0x100000 <= code <= 0x10FFFD
    ):
        return f'Private Use-{code_u}'
    if (
        0x3400 <= code <= 0x4DBF or
        0x4E00 <= code <= 0x9FFF or
        0x20000 <= code <= 0x2A6DF or
        0x2A700 <= code <= 0x2B738 or
        0x2B740 <= code <= 0x2B81D or
        0x2B740 <= code <= 0x2B81D or
        0x2B820 <= code <= 0x2CEA1 or
        0x2CEB0 <= code <= 0x2EBE0 or
        0x2EBF0 <= code <= 0x2EE5D or
        0x30000 <= code <= 0x3134A or
        0x31350 <= code <= 0x323AF
    ):
        return f'CJK Unified Ideograph-{code_u}'
    if 0xAC00 <= code <= 0xD7A3:
        return f'Hangul Syllable-{code_u}'
    if (
        0x17000 <= code <= 0x187F7 or
        0x18D00 <= code <= 0x18D08
    ):
        return f'Tangut-{code_u}'
    return NAME_LIST.get(
        str(code),
        {'name': f'<undefined character-{code_u}>'}
    )['name']


def get_char_alias(code):
    return NAME_LIST.get(str(code), {'alias': []})['alias']


def get_char_comment(code):
    return NAME_LIST.get(str(code), {'comment': []})['comment']


def get_char_version(code):
    index = bisect.bisect_right(VERSION_RANGE_START, code) - 1

    if (
        index != -1 and
        VERSION_RANGE_END[index] >= code
    ):
        return VERSION_RANGES[index][1]
    return NAME_LIST.get(
        str(code),
        {'version': '<future version>'}
    )['version']


def is_defined(code):
    if (
        code in DEFINED_CHARACTER_LIST or
        0xE000 <= code <= 0xF8FF or
        0xF0000 <= code <= 0xFFFFD or
        0x100000 <= code <= 0x10FFFD
    ):
        return True
    return False


def is_private_use(code):
    if (0xE000 <= code <= 0xF8FF or
       0xF0000 <= code <= 0xFFFFD or
       0x100000 <= code <= 0x10FFFD):
        return True
    return False


# 区段相关的函数
def get_block(code):
    index = bisect.bisect_right(BLOCK_START_LIST, code) - 1

    if (
        index != -1 and
        code <= get_block_infos(block_name := BLOCK_NAMES[index])[3][1]
    ):
        return block_name
    return None


def get_block_infos(block_name):
    return BLOCK_INFOS.get(
        block_name,
        ('未定义', 'Undefined', 'U+?-U+?', (-1, -1))
    )


def get_group(group, group_lens, index):
    for i in range(0, len(group_lens)):
        if sum(group_lens[:i + 1]) >= index + 1:
            return group[i], index - sum(group_lens[:i])
    return


# 编码相关的函数
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


# 其他函数
def auto_width(string, font, width):
    char_widths = [
        (bbox := font.getbbox(char))[2] - bbox[0] for char in string
    ]
    current_width = 0
    processed_string = ''

    if (bbox := font.getbbox(string))[2] - bbox[0] <= width:
        return string

    for i in range(len(string)):
        char = string[i]
        char_width = char_widths[i]

        if char == ' ' and current_width + char_width > width:
            processed_string += '\n  '
            current_width = (bbox := font.getbbox('  '))[2] - bbox[0]
        elif current_width + char_width > width:
            processed_string_list = list(processed_string)
            last_space_index = processed_string.rfind(' ')
            processed_string_list[last_space_index] = '\n  '
            processed_string = ''.join(processed_string_list)
            processed_string += char
            current_width = (
                sum(char_widths[last_space_index+1:i+1]) +
                (bbox := font.getbbox('  '))[2] - bbox[0]
            )
        else:
            processed_string += char
            current_width += char_width
    return processed_string


def merge_iterables(*iterables):
    result_list = []
    for subiterable in iterables:
        result_list.extend(subiterable)
    return result_list


def gap(s):
    return ' '.join([s[i:i+2] for i in range(0, len(s), 2)])


# 主要函数
def generate_a_image(w, h, bar_height, _code, groups, group_lens, code_index,
                     c_font, b_font, be_font, o_font, r_font, h_font, n_font, fn_font, i_font, p_font,
                     fonts, last_type, show_private, show_undefined):
    font = None
    for _font, font_cmap, _font_name in fonts:
        if _code in font_cmap:
            font = _font
            font_name = _font_name
            break
    if _code == 0xA:
        text = '\u240A'
    elif _code == 0xD:
        text = '\u240D'
    elif _code in VARI_VIRAM_PUNCTUATION4:
        text = '\u0964'
        font = main_fonts[1][2]
        font_name = main_fonts[1][1]
    elif _code in VARI_VIRAM_PUNCTUATION5:
        text = '\u0965'
        font = main_fonts[1][2]
        font_name = main_fonts[1][1]
    elif _code == 0x2072:
        text = '\u00B2'
        font = main_fonts[1][2]
        font_name = main_fonts[1][1]
    elif _code == 0x2073:
        text = '\u00B3'
        font = main_fonts[1][2]
        font_name = main_fonts[1][1]
    else:
        text = chr(_code)
    utf8 = 'UTF-8: ' + gap(to_utf8_hex(_code))
    utf16le = 'UTF-16LE: ' + gap(to_utf16le_hex(_code))
    utf16be = 'UTF-16BE: ' + gap(to_utf16be_hex(_code))

    bgc = 20
    textc = 235
    group, intra_group_index = get_group(groups, group_lens, code_index)
    block_infos, _ = group
    block_cn_name, block_en_name, block_range = block_infos

    if font is None:
        if (
            show_private and is_private_use(_code) or
            not is_private_use(_code)
        ):
            for cmap, name, main_font in main_fonts:
                if _code in cmap:
                    font = main_font
                    font_name = name
                    break
            else:
                if is_defined(_code):
                    for subsidiary_font, name, rangs in subsidiary_fonts:
                        for rang in rangs:
                            if rang[0] <= _code <= rang[1]:
                                font = subsidiary_font
                                font_name = name
                                break
        if font is None:
            if last_type == 2:
                font = font_mlst
                font_name = font_name_mlst
            elif last_type == 1:
                font = font_last
                font_name = font_name_last
            else:
                font_name = 'no font'

    code = 'U+' + hex(_code)[2:].upper().zfill(4)
    image = Image.new('L', (w, h), color=bgc)

    draw = ImageDraw.Draw(image)

    bbox = c_font.getbbox(code)
    code_width = bbox[2] - bbox[0]
    code_height = bbox[3] - bbox[1]
    code_x = w - code_width - 15
    code_y = h - code_height*1.5 - 5
    draw.text((code_x, code_y), code, font=c_font, fill=textc)

    fn = '字体: ' + font_name
    bbox = fn_font.getbbox(fn)
    fn_width = bbox[2] - bbox[0]
    fn_height = bbox[3] - bbox[1]
    draw.text(
        (w - fn_width - 15, code_y - fn_height - 5),
        fn,
        font=fn_font,
        fill=textc
    )

    bbox = h_font.getbbox(utf8)
    utf8_width = bbox[2] - bbox[0]
    utf8_height = bbox[3] - bbox[1]
    utf8_y = h - utf8_height*1.5 - 5
    draw.text(((w - utf8_width)/2, utf8_y), utf8, fill=textc, font=h_font)

    bbox = h_font.getbbox(utf16le)
    utf16le_width = bbox[2] - bbox[0]
    utf16le_height = bbox[3] - bbox[1]
    utf16le_y = utf8_y - utf16le_height*1.5 - 5
    draw.text(
        ((w - utf16le_width)/2, utf16le_y),
        utf16le,
        fill=textc,
        font=h_font
    )

    bbox = h_font.getbbox(utf16be)
    utf16be_width = bbox[2] - bbox[0]
    utf16be_height = bbox[3] - bbox[1]
    draw.text(
        ((w - utf16be_width)/2, utf16le_y - utf16be_height*1.5 - 5),
        utf16be,
        fill=textc,
        font=h_font
    )

    block_en = auto_width(block_en_name, n_font, (w - utf8_width)/2)
    bbox = draw.textbbox(xy=(0, 0), text=block_en, font=be_font)
    block_en_height = bbox[3] - bbox[1]
    block_en_y = (
        h -
        block_en_height -
        ((_b := be_font.getbbox('a'))[3] - _b[1])*0.5 -
        5
    )
    draw.text((35, block_en_y), block_en, font=be_font, fill=textc)

    bbox = b_font.getbbox(block_cn_name)
    block_height = bbox[3] - bbox[1]
    block_y = block_en_y - block_height - 5
    draw.text((35, block_y), block_cn_name, font=b_font, fill=textc)

    bbox = r_font.getbbox(block_range)
    r_height = bbox[3] - bbox[1]
    r_y = block_y - r_height - 5
    draw.text((35, r_y), block_range, font=r_font, fill=textc)

    name = auto_width(get_char_name(_code), n_font, w - 35)
    bbox = draw.textbbox(xy=(0, 0), text=name, font=n_font)
    name_height = bbox[3] - bbox[1]
    draw.text((35, r_y-name_height-5), name, font=n_font, fill=textc)

    progress = (intra_group_index + 1) / group[1]
    draw.rectangle([0, 0, round(progress * w), bar_height], textc)

    percent = f'{progress * 100: .2f}%'
    bbox = draw.textbbox(xy=(0, 0), text=percent, font=i_font)
    percent_height = bbox[3] - bbox[1]
    percent_width = bbox[2] - bbox[0]
    percent_y = bar_height + 5
    draw.text(
        (w - percent_width - 20, percent_y),
        percent,
        font=i_font,
        fill=textc
    )

    alias = ', '.join(get_char_alias(_code))
    if alias:
        alias = auto_width('alias: ' + alias, i_font, w-35)
        bbox = draw.textbbox(xy=(0, 0), text=alias, font=i_font)
        alias_height = bbox[3] - bbox[1]
        alias_y = percent_y + percent_height + 5
        draw.text((35, alias_y), alias, font=i_font, fill=textc)
    else:
        alias_height = 0
        alias_y = percent_y + percent_height

    formal_alias = ', '.join(NAME_LIST.get(
        str(_code),
        {'formal alias': []})['formal alias']
    )
    if formal_alias:
        formal_alias = auto_width(
            'formal alias: ' + formal_alias,
            i_font,
            w-35
        )
        bbox = draw.textbbox(xy=(0, 0), text=formal_alias, font=i_font)
        formal_alias_height = bbox[3] - bbox[1]
        formal_alias_y = alias_y + alias_height + 5
        draw.text((35, formal_alias_y), formal_alias, font=i_font, fill=textc)
    else:
        formal_alias_height = 0
        formal_alias_y = alias_y + alias_height

    comment = '.'.join(get_char_comment(_code))
    if comment:
        comment = auto_width('comment: ' + comment + '.', i_font, w-35)
        bbox = draw.textbbox(xy=(0, 0), text=comment, font=i_font)
        comment_height = bbox[3] - bbox[1]
        comment_y = formal_alias_y + formal_alias_height + 5
        draw.text((35, comment_y), comment, font=i_font, fill=textc)
    else:
        comment_height = 0
        comment_y = formal_alias_y + formal_alias_height

    cross_ref = ', '.join(NAME_LIST.get(
        str(_code),
        {'cross ref': []})['cross ref']
    )
    if cross_ref:
        cross_ref = auto_width('cross ref: ' + cross_ref, i_font, w-35)
        bbox = draw.textbbox(xy=(0, 0), text=cross_ref, font=i_font)
        cross_ref_height = bbox[3] - bbox[1]
        cross_ref_y = comment_y + comment_height + 5
        draw.text((35, cross_ref_y), cross_ref, font=i_font, fill=textc)
    else:
        cross_ref_height = 0
        cross_ref_y = comment_y + comment_height

    variation = ', '.join(NAME_LIST.get(
        str(_code),
        {'variation': []})['variation']
    )
    if variation:
        variation = auto_width('variation: ' + variation, i_font, w-35)
        bbox = draw.textbbox(xy=(0, 0), text=variation, font=i_font)
        variation_height = bbox[3] - bbox[1]
        variation_y = cross_ref_y + cross_ref_height + 5
        draw.text((35, variation_y), variation, font=i_font, fill=textc)
    else:
        variation_height = 0
        variation_y = cross_ref_y + cross_ref_height

    decomposition = ', '.join(NAME_LIST.get(
        str(_code),
        {'decomposition': []})['decomposition']
    )
    if decomposition:
        decomposition = auto_width(
            'decomposition: ' + decomposition,
            i_font,
            w-35
        )
        bbox = draw.textbbox(xy=(0, 0), text=decomposition, font=i_font)
        decomposition_height = bbox[3] - bbox[1]
        decomposition_y = variation_y + variation_height + 5
        draw.text(
            (35, decomposition_y),
            decomposition,
            font=i_font,
            fill=textc
        )
    else:
        decomposition_height = 0
        decomposition_y = variation_y + variation_height

    compat_mapping = ', '.join(NAME_LIST.get(
        str(_code),
        {'compat mapping': []})['compat mapping']
    )
    if compat_mapping:
        compat_mapping = auto_width(
            'compat mapping: ' + compat_mapping,
            i_font,
            w-35
        )
        bbox = draw.textbbox(xy=(0, 0), text=compat_mapping, font=i_font)
        compat_mapping_height = bbox[3] - bbox[1]
        compat_mapping_y = decomposition_y + decomposition_height + 5
        draw.text(
            (35, compat_mapping_y),
            compat_mapping,
            font=i_font,
            fill=textc
        )
    else:
        compat_mapping_height = 0
        compat_mapping_y = decomposition_y + decomposition_height

    version = 'version: ' + get_char_version(_code)
    draw.text(
        (35, compat_mapping_y + compat_mapping_height + 5),
        version,
        font=i_font,
        fill=textc
    )

    if (is_defined(_code) and not is_private_use(_code)) or last_type:
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
    else:
        if _code in NOT_CHAR:
            text = f'非字符 {code}'
        elif 0xD800 <= _code <= 0xDB7F:
            text = f'高位替代字符 {code}'
        elif 0xDB80 <= _code <= 0xDBFF:
            text = f'高位私用替代字符 {code}'
        elif 0xDC00 <= _code <= 0xDFFF:
            text = f'低位替代字符 {code}'
        elif (0xE000 <= _code <= 0xF8FF or
              0xF0000 <= _code <= 0xFFFFD or
              0x100000 <= _code <= 0x10FFFD):
            text = f'私用区字符 {code}'
        else:
            text = f'未定义字符 {code}'
        bbox = o_font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = w/2 - text_width/2
        y = h/2 - text_height/2
        draw.text((x, y), text, font=o_font, fill=textc)

    for item in PLANES:
        if item[0][0] <= _code <= item[0][1]:
            plane = item[1]
            break

    plane_num, plane_en, plane_cn = (
        f'{plane[0]}({plane[1]})',
        plane[2],
        plane[3]
    )

    bbox = p_font.getbbox(plane_en)
    plane_en_width = bbox[2] - bbox[0]
    plane_en_height = bbox[3] - bbox[1]
    plane_en_x = w - plane_en_width - 15
    plane_en_y = h/2 - plane_en_height/2
    draw.text((plane_en_x, plane_en_y), plane_en, font=p_font, fill=textc)

    bbox = p_font.getbbox(plane_num)
    plane_num_width = bbox[2] - bbox[0]
    plane_num_height = bbox[3] - bbox[1]
    plane_num_x = w - plane_num_width - 15
    plane_num_y = plane_en_y - plane_num_height - 5
    draw.text((plane_num_x, plane_num_y), plane_num, font=p_font, fill=textc)

    bbox = p_font.getbbox(plane_cn)
    plane_cn_width = bbox[2] - bbox[0]
    plane_cn_height = bbox[3] - bbox[1]
    plane_cn_x = w - plane_cn_width - 15
    plane_cn_y = plane_num_y + plane_cn_height + plane_num_height + 10
    draw.text((plane_cn_x, plane_cn_y), plane_cn, font=p_font, fill=textc)

    return image


def generate_unicode_flash(width, height, bar_height, out_path, codes, fps, _fonts,
                           c_font, b_font, be_font, o_font, r_font, h_font, n_font, fn_font, i_font, p_font,
                           last_type, show_private, show_undefined):
    groups = [
        (
            (*get_block_infos(k)[:-1], ),
            len(list(g))
        ) for k, g in itertools.groupby(codes, get_block)
    ]
    group_lens = [l for _, l in groups]

    fonts = tuple(zip(
        map(
            lambda f: ImageFont.truetype(f, EXAMPLE_FONT_SIZE),
            _fonts
        ),
        map(
            lambda f: get_all_codes_from_font(TTFont(f)),
            _fonts
        ),
        map(
            lambda f: get_font_name(TTFont(f)['name'].names),
            _fonts
        )
    ))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(
        out_path,
        fourcc,
        fps,
        (width, height)
    )

    for code_index, code in enumerate(tqdm(codes)):
        try:
            image = generate_a_image(width, height, bar_height, code, groups, group_lens, code_index,
                                     c_font, b_font, be_font, o_font, r_font, h_font, n_font, fn_font, i_font, p_font,
                                     fonts, last_type, show_private, show_undefined)
        except OSError:
            print(f'在U+{hex(code)[2:].upper().zfill(4)}处发生raster overflow，已跳过。')
            continue
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        video_writer.write(img_cv)

    video_writer.release()


if __name__ == '__main__':
    import argparse
    from argparse_range import range_action

    def _ve(v):
        raise ValueError(f'无效Unicode码位 {v}')

    def hex_number(number):
        if isinstance(number, int):
            return number
        return int(number, 16)

    parser = argparse.ArgumentParser(description='这是一个Unicode快闪生成脚本')
    parser.add_argument('fps', type=float,
                        help='帧率，建议15，可以为小数')
    parser.add_argument('-wt', '--width', type=int, default=1920,
                        help='视频宽度，默认1920')
    parser.add_argument('-ht', '--height', type=int, default=1080,
                        help='视频宽度，默认1080')
    parser.add_argument('-bh', '--bar_height', type=int, default=36,
                        help='顶部进度条高度，默认36')
    parser.add_argument('-f', '--fonts', type=str, nargs='*', default=[],
                        help='字体路径列表，按输入顺序计算优先级')
    parser.add_argument('-op', '--out_path', type=str,
                        default=os.path.join(CUR_FOLDER, 'res.mp4'),
                        help='生成视频的路径')
    parser.add_argument('-sp', '--show_private', action='store_true',
                        help='展示在字体中有字形的私用区字符')
    parser.add_argument('-sng', '--skip_no_glyph', action='store_true',
                        help='跳过在所有自定义字体中都没有字形的字符')
    parser.add_argument('-sl', '--skip_long', action='store_true',
                        help='跳过U+323B0-U+DFFFF')

    undef_group = parser.add_mutually_exclusive_group()
    undef_group.add_argument('-su', '--skip_undefined', action='store_true',
                             help='跳过未定义字符、非字符、代理字符等')
    undef_group.add_argument('-shu', '--show_undefined', action='store_true',
                             help='展示在自定义字体中有字形的未定义字符、非字符、代理字符等')
    last_group = parser.add_mutually_exclusive_group()
    last_group.add_argument('-um', '--use_mlst', action='store_true',
                            help='使用MonuLast(典迹末境)字体')
    last_group.add_argument('-ul', '--use_last', action='store_true',
                            help='使用LastResort(最后手段)字体')
    chars_group = parser.add_mutually_exclusive_group(required=True)
    chars_group.add_argument('-r', '--rang', type=hex_number,
                             nargs=2, action=range_action(
                                 0, 0x10FFFF,
                                 range_formatter=lambda i: hex(i)
                                 .replace('0x', '').upper()
                             ),
                             help='快闪字符的范围，不带0x的十六进制数')
    chars_group.add_argument('-fcf', '--from_code_file',
                             type=argparse.FileType('r'),
                             help='通过一个写着Unicode编码（不带0x的十六进制数，多个编码间用「,」分隔）的文件获取将要快闪的字符')
    chars_group.add_argument('-ftf', '--from_text_file',
                             type=argparse.FileType('r'),
                             help='通过一个一般的文本文件获取将要快闪的字符')
    chars_group.add_argument('-ff', '--from_font', action='store_true',
                             help='从字体文件列表获取将要快闪的字符')
    args = parser.parse_args()

    # 要用到的字体
    main_fonts = [
        os.path.join(CUR_FOLDER, 'CtrlCtrl.ttf'),
        os.path.join(CUR_FOLDER, 'NotoUnicode.ttf'),
        os.path.join(CUR_FOLDER, 'MonuHani.ttf'),
        os.path.join(CUR_FOLDER, 'MonuHanp.ttf'),
        os.path.join(CUR_FOLDER, 'MonuHan2.ttf'),
        os.path.join(CUR_FOLDER, 'MonuHan3.ttf'),
        os.path.join(CUR_FOLDER, 'MonuTemp.ttf'),
    ]
    subsidiary_fonts = [
        (os.path.join(CUR_FOLDER, 'NotoSerifTangut.ttf'), '17000..18AFF,18D00..18D7F'),
        (os.path.join(CUR_FOLDER, 'SegoeUIHistoric.ttf'), '700..74F,1680..169F,10280..102DF,10330..1034F,10380..1047F,10800..1085F,10900..1093F,10A60..10A7F,10B40..10B7F,10C00..10C4F,12400..1247F'),
        (os.path.join(CUR_FOLDER, 'MVBoli.ttf'), '780..7BF'),
        (os.path.join(CUR_FOLDER, 'Ebrima.ttf'), '7C0..7FF,1200..139F,2D30..2DDF,A500..A63F,AB00..AB2F,10480..104AF,1E900..1E95F'),
        (os.path.join(CUR_FOLDER, 'NirmalaUI.ttf'), 'B80..BFF,1C50..1C7F,ABC0..ABFF,110D0..110FF'),
        (os.path.join(CUR_FOLDER, 'LeelawadeeUI.ttf'), 'E00..E7F,1780..17FF,19E0..1A1F'),
        (os.path.join(CUR_FOLDER, 'MyanmarText.ttf'), '1000..109F,A9E0..A9FF,AA60..AA7F'),
        (os.path.join(CUR_FOLDER, 'Calibri.ttf'), '10A0..10FF,1C90..1CBF,2D00..2D2F'),
        (os.path.join(CUR_FOLDER, 'MalgunGothic.ttf'), '1100..11FF,3130..318F,A960..A97F,AC00..D7FF'),
        (os.path.join(CUR_FOLDER, 'Gadugi.ttf'), '13A0..167F,18B0..18FF,AB70..ABBF,104B0..104FF'),
        (os.path.join(CUR_FOLDER, 'MicrosoftTaiLe.ttf'), '1950..197F'),
        (os.path.join(CUR_FOLDER, 'MicrosoftNewTaiLue.ttf'), '1980..19DF'),
        (os.path.join(CUR_FOLDER, 'SegoeUISymbol.ttf'), '2190..22FF,2400..2AFF,2C80..2CFF,4DC0..4DFF,1D300..1D35F,1D400..1D7FF,1F030..1F0FF,1F650..1F67F'),
        (os.path.join(CUR_FOLDER, '微软雅黑.ttf'), '3040..30FF,3190..319F,31F0..31FF,FE10..FE1F,FE30..FE6F'),
        (os.path.join(CUR_FOLDER, 'YuGothic.ttf'), '3300..33FF'),
        (os.path.join(CUR_FOLDER, 'MicrosoftYiBaiti.ttf'), 'A000..A4CF'),
        (os.path.join(CUR_FOLDER, 'SegoeUI.ttf'), 'A4D0..A4FF,A700..A71F'),
        (os.path.join(CUR_FOLDER, 'MicrosoftPhagsPa.ttf'), 'A840..A87F'),
        (os.path.join(CUR_FOLDER, 'JavaneseText.ttf'), 'A980..A9DF'),
        (os.path.join(CUR_FOLDER, 'MicrosoftJhengHei.ttf'), 'FF00..FFEF'),
        (os.path.join(CUR_FOLDER, 'SegoeUIEmoji.ttf'), '1F000..1F02F,1F600..1F64F')
    ]
    block_name_font_path = os.path.join(CUR_FOLDER, 'SarasaGothicSC-Regular.ttf')
    block_name_en_font_path = os.path.join(CUR_FOLDER, 'SarasaGothicSC-Regular.ttf')
    range_font_path = os.path.join(CUR_FOLDER, 'SarasaGothicSC-Regular.ttf')
    code_font_path = os.path.join(CUR_FOLDER, 'monaco.ttf')
    name_font_path = os.path.join(CUR_FOLDER, 'SarasaGothicSC-Regular.ttf')
    hex_font_path = os.path.join(CUR_FOLDER, 'monaco.ttf')
    font_name_font_path = os.path.join(CUR_FOLDER, '微软雅黑.ttf')
    info_font_path = os.path.join(CUR_FOLDER, 'SarasaGothicSC-Regular.ttf')
    plane_font_path = os.path.join(CUR_FOLDER, 'SarasaGothicSC-Regular.ttf')
    other_font_path = os.path.join(CUR_FOLDER, 'SarasaGothicSC-Regular.ttf')

    font_path_mlst = os.path.join(CUR_FOLDER, 'MonuLast.ttf')
    font_path_last = os.path.join(CUR_FOLDER, 'LastResort.ttf')
    tfont_mlst = TTFont(font_path_mlst)
    tfont_last = TTFont(font_path_last)
    font_mlst = ImageFont.truetype(font_path_mlst, EXAMPLE_FONT_SIZE)
    font_last = ImageFont.truetype(font_path_last, EXAMPLE_FONT_SIZE)
    font_name_mlst = get_font_name(tfont_mlst['name'].names)
    font_name_last = get_font_name(tfont_last['name'].names)

    main_fonts = [(p, TTFont(p)) for p in main_fonts]
    main_fonts = [(
        get_all_codes_from_font(tf),
        get_font_name(tf['name'].names),
        ImageFont.truetype(p, EXAMPLE_FONT_SIZE)
    ) for p, tf in main_fonts]
    subsidiary_fonts = [(
        ImageFont.truetype(p, EXAMPLE_FONT_SIZE),
        get_font_name(TTFont(p)['name'].names),
        list(map(
            lambda i: tuple(
                map(lambda j: int(j, 16), i.split('..'))
            ),
            r.split(','))
        )
    ) for p, r in subsidiary_fonts]

    c_font = ImageFont.truetype(code_font_path, 40)
    b_font = ImageFont.truetype(block_name_font_path, 45)
    be_font = ImageFont.truetype(block_name_en_font_path, 30)
    o_font = ImageFont.truetype(other_font_path, 40)
    r_font = ImageFont.truetype(range_font_path, 40)
    h_font = ImageFont.truetype(hex_font_path, 25)
    n_font = ImageFont.truetype(name_font_path, 30)
    fn_font = ImageFont.truetype(font_name_font_path, 40)
    i_font = ImageFont.truetype(info_font_path, 30)
    p_font = ImageFont.truetype(plane_font_path, 30)

    if args.rang:
        codes = list(range(
            args.rang[0], args.rang[1] + 1
        ))
    elif args.from_code_file:
        codes = list(map(
            lambda v: int(v, 16) if UNICODE_RE.search(v) else _ve(v),
            args.from_code_file.read().split(','))
        )
    elif args.from_text_file:
        codes = list(map(lambda char: ord(char), args.from_text_file.read()))
    elif args.from_font:
        codes = sorted(merge_iterables(
            *(get_all_codes_from_font(TTFont(font)) for font in args.fonts)
        ))

    skip_long = args.skip_long
    skip_undefined = args.skip_undefined
    skip_no_glyph = args.skip_no_glyph
    if skip_long or skip_undefined:
        codes = list(filter(
            lambda code: not (
                skip_long and 0x323B0 <= code <= 0xDFFFF or
                skip_undefined and not is_defined(code)
            ), codes
        ))
    if skip_no_glyph:
        all_glyphs = set(merge_iterables(*map(
            lambda f: get_all_codes_from_font(TTFont(f)),
            args.fonts
        )))

        codes = list(filter(
            lambda c: c in all_glyphs, codes
        ))

    generate_unicode_flash(args.width, args.height, args.bar_height, args.out_path, codes, args.fps, args.fonts,
                           c_font, b_font, be_font, o_font, r_font, h_font, n_font, fn_font, i_font, p_font,
                           (1 if args.use_last else 2 if args.use_mlst else 0), args.show_private, args.show_undefined)
