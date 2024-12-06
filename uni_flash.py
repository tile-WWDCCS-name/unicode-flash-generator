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
EXAMPLE_FONT_SIZE = 220

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
    os.path.join(CUR_FOLDER, 'ToolFiles', 'Blocks.csv'),
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
    os.path.join(CUR_FOLDER, 'ToolFiles', 'Planes.csv'),
    encoding='utf-8'
) as blocks_csv:
    reader = list(csv.reader(blocks_csv, delimiter='|'))
    PLANE_START_LIST = [int(line[0].split('..')[0], 16) for line in reader]
    PLANE_INFOS = [
        (
            *line[1:],
            '-'.join(map(lambda rang: 'U+' + rang, line[0].split('..')))
        ) for line in reader
    ]


NAME_LIST = json.load(open(
    os.path.join(CUR_FOLDER, 'ToolFiles', 'NamesList.json'),
    encoding='utf8'
))
DEFINED_CHARACTER_LIST = set(json.load(open(
    os.path.join(CUR_FOLDER, 'ToolFiles', 'DefinedCharacterList.json'),
    encoding='utf8'
)))
FONTS = json.load(open(
    os.path.join(CUR_FOLDER, 'ToolFiles', 'FontFallback.json'),
    encoding='utf8'
))
FONTS = {
    k: (set(v), ImageFont.truetype(
        os.path.join(CUR_FOLDER, 'fonts', k + '.ttf'),
        EXAMPLE_FONT_SIZE
    ))
    for k, v in FONTS.items()
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
    ((0x2EBF0, 0x2EE5D), '15.1.0')
]

VERSION_RANGE_START = [i[0][0] for i in VERSION_RANGES]
VERSION_RANGE_END = [i[0][1] for i in VERSION_RANGES]


# 字体相关的函数
def get_font_name(font):
    return font['name'].getName(6, 3, 1, 1033).string.decode('utf-8').replace('\0', '')


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
        0xE000 <= code <= 0xF8FF
        or 0xF0000 <= code <= 0xFFFFD
        or 0x100000 <= code <= 0x10FFFD
    ):
        return f'Private Use-{code_u}'
    if (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0x20000 <= code <= 0x2A6DF
        or 0x2A700 <= code <= 0x2B738
        or 0x2B740 <= code <= 0x2B81D
        or 0x2B740 <= code <= 0x2B81D
        or 0x2B820 <= code <= 0x2CEA1
        or 0x2CEB0 <= code <= 0x2EBE0
        or 0x2EBF0 <= code <= 0x2EE5D
        or 0x30000 <= code <= 0x3134A
        or 0x31350 <= code <= 0x323AF
    ):
        return f'CJK Unified Ideograph-{code_u}'
    if 0xAC00 <= code <= 0xD7A3:
        return f'Hangul Syllable-{code_u}'
    if (
        0x17000 <= code <= 0x187F7
        or 0x18D00 <= code <= 0x18D08
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
        {'version': ('<future version>' if (code not in NOT_CHAR
                                            and not is_private_use(code)
                                            and not 0xD800 <= code <= 0xDFFF) else '<never>')}
    )['version']


def is_defined(code):
    if (
        code in DEFINED_CHARACTER_LIST
        or 0xE000 <= code <= 0xF8FF
        or 0xF0000 <= code <= 0xFFFFD
        or 0x100000 <= code <= 0x10FFFD
    ):
        return True
    return False


def is_private_use(code):
    if (0xE000 <= code <= 0xF8FF
        or 0xF0000 <= code <= 0xFFFFD
        or 0x100000 <= code <= 0x10FFFD):
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


def get_group(groups, group_lens, code_index):
    for i in range(0, len(group_lens)):
        if sum(group_lens[:i + 1]) >= code_index + 1:
            return groups[i], code_index - sum(group_lens[:i])


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
def auto_width(string, font, width, indent='  '):
    if font.getlength(string) <= width:
        return string

    char_widths = [
        font.getlength(char) for char in string
    ]
    current_width = 0
    indent_width = font.getlength(indent)
    processed_string = ''

    for i in range(len(string)):
        char = string[i]
        char_width = char_widths[i]

        if char in ' -' and current_width + char_width > width:
            processed_string += (char if char != ' ' else '') +  '\n' + indent
            current_width = indent_width
        elif current_width + char_width > width:
            processed_string_list = list(processed_string)
            last_space_index = max(processed_string.rfind(' '), processed_string.rfind('-'))
            last_space_char = processed_string_list[last_space_index]
            processed_string_list[last_space_index] = (last_space_char if last_space_char != ' ' else '') + '\n' + indent
            processed_string = ''.join(processed_string_list)
            processed_string += char
            current_width = (
                sum(char_widths[last_space_index+1:i+1])
                + indent_width
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
def generate_a_image(_code,
                     group,
                     dimensions,
                     img_properties,
                     info_fonts,
                     custom_fonts,
                     opts):
    (
        bar_height,
        margin_top,
        margin_bottom,
        margin_left,
        margin_right
    ) = (
        dimensions['bar_height'],
        dimensions['margin_top'],
        dimensions['margin_bottom'],
        dimensions['margin_left'],
        dimensions['margin_right'],
    )
    w, h = img_properties['width'], img_properties['height']
    (
        top_font,
        right_middle_font,
        left_bottom_font,
        middle_bottom_font,
        right_bottom_font,
        cannot_display_default_font,
        percent_font
    ) = (
        info_fonts['top'],
        info_fonts['right_middle'],
        info_fonts['left_bottom'],
        info_fonts['middle_bottom'],
        info_fonts['right_bottom'],
        info_fonts['cannot_display_default'],
        info_fonts['percent']
    )
    last_type, show_private, show_undefined = opts['last_type'], opts['show_private'], opts['show_undefined']

    font = None
    for _font, font_cmap, _font_name in custom_fonts:
        if _code in font_cmap:
            font = _font
            font_name = _font_name
            break
    if _code == 0xA:
        text = '\u240A'
    elif _code == 0xD:
        text = '\u240D'
    else:
        text = chr(_code)
    utf8 = 'UTF-8: ' + gap(to_utf8_hex(_code))
    utf16le = 'UTF-16LE: ' + gap(to_utf16le_hex(_code))
    utf16be = 'UTF-16BE: ' + gap(to_utf16be_hex(_code))

    bgc = 20
    textc = 235
    group, intra_group_index = get_group(**group)
    block_infos, _ = group
    block_cn_name, block_en_name, block_range = block_infos
    
    plane_index = bisect.bisect_right(PLANE_START_LIST, _code) - 1
    plane = PLANE_INFOS[plane_index]

    plane_num, plane_en, plane_cn = (
        f'{plane[0]}({plane[1]})',
        plane[2],
        plane[3]
    )

    font_name = 'unknown'
    if font is None:
        if (
            show_private and is_private_use(_code)
            or not is_private_use(_code)
        ):
            for font_name_ in FONTS:
                can_display_chars, font_ = FONTS[font_name_]
                if _code in can_display_chars:
                    font = font_
                    font_name = font_name_
                    break
        if font is None:
            if last_type == 2:
                font = font_mlst
                font_name = font_name_mlst
            elif last_type == 1:
                font = font_last
                font_name = font_name_last
            else:
                font_name = 'Sarasa-Mono-SC-Regular'

    code = 'U+' + hex(_code)[2:].upper().zfill(4)
    image = Image.new('L', (w, h), color=bgc)

    draw = ImageDraw.Draw(image)

    mb_text = '\n'.join([utf16be, utf16le, utf8])
    mb_text_left, _ , mb_text_right, _ = draw.textbbox((w / 2, h - 15), mb_text, font=middle_bottom_font, anchor='md', align='center')
    draw.text((w / 2, h - margin_bottom), mb_text, fill=textc, font=middle_bottom_font, anchor='md', align='center')

    fn = auto_width('字体：' + font_name, rb_font, w - mb_text_right - 15)
    rb_text = '\n'.join([fn, code])
    draw.text((w - 15, h - margin_bottom), rb_text, font=right_bottom_font, fill=textc, anchor='rd', align='right')

    block_en = auto_width(block_en_name, left_bottom_font, mb_text_left - 15)
    name = auto_width(get_char_name(_code), left_bottom_font, mb_text_left - 15)
    lb_text = '\n'.join([name, block_range, block_cn_name, block_en])
    draw.text((margin_left, h - margin_bottom), lb_text, fill=textc, font=left_bottom_font, anchor='ld')

    rm_text = '\n'.join([plane_cn, plane_en, plane_num])
    draw.text((w - margin_right, h / 2), rm_text, fill=textc, font=right_middle_font, anchor='rm', align='right')

    progress = (intra_group_index + 1) / group[1]
    draw.rectangle([0, 0, round(progress * w), bar_height], textc)

    percent = f'{progress * 100: .2f}%'
    percent_left = draw.textbbox((w - 15, bar_height + 15), percent, font=middle_bottom_font, anchor='rt')[0]
    draw.text((w - margin_right, bar_height + margin_top), percent, font=percent_font, fill=textc, anchor='rt')

    alias = ', '.join(get_char_alias(_code))
    formal_alias = ', '.join(NAME_LIST.get(
        str(_code),
        {'formal alias': []})['formal alias']
    )
    comment = '; '.join(get_char_comment(_code))
    cross_ref = ', '.join(NAME_LIST.get(
        str(_code),
        {'cross ref': []})['cross ref']
    )
    variation = ', '.join(NAME_LIST.get(
        str(_code),
        {'variation': []})['variation']
    )
    decomposition = ', '.join(NAME_LIST.get(
        str(_code),
        {'decomposition': []})['decomposition']
    )
    compat_mapping = ', '.join(NAME_LIST.get(
        str(_code),
        {'compat mapping': []})['compat mapping']
    )
    version = '版本：' + get_char_version(_code)
    alias = auto_width('别名：' + alias, top_font, percent_left - 15) if alias else ''
    formal_alias = auto_width('正式别名：' + formal_alias, top_font, percent_left - 15) if formal_alias else ''
    comment = auto_width('说明：' + comment, top_font, percent_left - 15) if comment else ''
    cross_ref = auto_width('交叉参考：' + cross_ref, top_font, percent_left - 15) if cross_ref else ''
    variation = auto_width('变体：' + variation, top_font, percent_left - 15) if variation else ''
    decomposition = auto_width('拆解' + decomposition, top_font, percent_left - 15) if decomposition else ''
    compat_mapping = auto_width('兼容性映射：' + compat_mapping, top_font, percent_left - 15) if compat_mapping else ''
    t_text = '\n'.join(filter(bool, [
        compat_mapping,
        decomposition,
        variation,
        cross_ref,
        comment,
        formal_alias,
        alias,
        version
    ]))
    draw.text((margin_left, bar_height + margin_top), t_text, font=top_font, fill=textc)
    if (is_defined(_code) and not is_private_use(_code) or last_type
        or show_private and font is not None and is_private_use(_code)
        or show_undefined and font is not None and not is_defined(_code)):
        draw.text((w / 2, h / 2), text, font=font, fill=textc, anchor='mm')
    else:
        if _code in NOT_CHAR:
            text = f'非字符 {code}'
        elif 0xD800 <= _code <= 0xDB7F:
            text = f'高位替代字符 {code}'
        elif 0xDB80 <= _code <= 0xDBFF:
            text = f'高位私用替代字符 {code}'
        elif 0xDC00 <= _code <= 0xDFFF:
            text = f'低位替代字符 {code}'
        elif is_private_use(_code):
            text = f'私用区字符 {code}'
        else:
            text = f'未定义字符 {code}'
        draw.text((w / 2, h / 2), text, font=cannot_display_default_font, fill=textc, anchor='mm')
    return image


def generate_unicode_flash(codes,
                           out_path,
                           dimensions,
                           video_properties,
                           info_fonts,
                           custom_font_paths,
                           opts):
    groups = [
        (
            (*get_block_infos(k)[:-1], ),
            len(list(g))
        ) for k, g in itertools.groupby(codes, get_block)
    ]
    group_lens = [l for _, l in groups]

    custom_fonts = tuple(zip(
        map(
            lambda f: ImageFont.truetype(f, EXAMPLE_FONT_SIZE),
            custom_font_paths
        ),
        map(
            lambda f: get_all_codes_from_font(TTFont(f)),
            custom_font_paths
        ),
        map(
            lambda f: get_font_name(TTFont(f)),
            custom_font_paths
        )
    ))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(
        out_path,
        fourcc,
        video_properties['fps'],
        (video_properties['width'], video_properties['height'])
    )

    for code_index, code in enumerate(tqdm(codes)):
        try:
            image = generate_a_image(code,
                                     {
                                         'groups': groups,
                                         'group_lens': group_lens,
                                         'code_index': code_index
                                     },
                                     dimensions,
                                     {
                                         'width': video_properties['width'],
                                         'height': video_properties['height']
                                     },
                                     info_fonts,
                                     custom_fonts,
                                     opts)
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
    parser.add_argument('-mt', '--margin_top', type=int, default=15,
                        help='上边距，默认15')
    parser.add_argument('-mb', '--margin_bottom', type=int, default=15,
                        help='下边距，默认15')
    parser.add_argument('-ml', '--margin_left', type=int, default=30,
                        help='左边距，默认30')
    parser.add_argument('-mr', '--margin_right', type=int, default=30,
                        help='右边距，默认30')

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
    top_font_path = os.path.join(CUR_FOLDER, 'Sarasa-Mono-SC-Regular.ttf')
    right_middle_font_path = os.path.join(CUR_FOLDER, 'Sarasa-Mono-SC-Regular.ttf')
    left_bottom_font_path = os.path.join(CUR_FOLDER, 'Sarasa-Mono-SC-Regular.ttf')
    middle_bottom_font_path = os.path.join(CUR_FOLDER, 'Sarasa-Mono-SC-Regular.ttf')
    right_bottom_font_path = os.path.join(CUR_FOLDER, 'Sarasa-Mono-SC-Regular.ttf')
    cannot_display_default_font_path = os.path.join(CUR_FOLDER, 'Sarasa-Mono-SC-Regular.ttf')
    percent_font_path = os.path.join(CUR_FOLDER, 'Sarasa-Mono-SC-Regular.ttf')

    t_font = ImageFont.truetype(top_font_path, 21)
    rm_font = ImageFont.truetype(right_middle_font_path, 25)
    lb_font = ImageFont.truetype(left_bottom_font_path, 25)
    rb_font = ImageFont.truetype(right_bottom_font_path, 40)
    mb_font = ImageFont.truetype(middle_bottom_font_path, 20)
    cdd_font = ImageFont.truetype(cannot_display_default_font_path, 40)
    p_font = ImageFont.truetype(percent_font_path, 20)

    font_path_mlst = os.path.join(CUR_FOLDER, 'Monu-Last.ttf')
    font_path_last = os.path.join(CUR_FOLDER, 'LastResort-Regular.ttf')
    tfont_mlst = TTFont(font_path_mlst)
    tfont_last = TTFont(font_path_last)
    font_mlst = ImageFont.truetype(font_path_mlst, EXAMPLE_FONT_SIZE)
    font_last = ImageFont.truetype(font_path_last, EXAMPLE_FONT_SIZE)
    font_name_mlst = 'Monu-Last'
    font_name_last = 'LastResort-Regular'

    codes = []
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
                skip_long and 0x323B0 <= code <= 0xDFFFF
                or skip_undefined and not is_defined(code)
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

    generate_unicode_flash(codes,
                           args.out_path,
                           {
                               'bar_height': args.bar_height,
                               'margin_top': args.margin_top,
                               'margin_bottom': args.margin_bottom,
                               'margin_left': args.margin_left,
                               'margin_right': args.margin_right,
                           },
                           {
                               'width': args.width,
                               'height': args.height,
                               'fps': args.fps
                           },
                           {
                              'top': t_font,
                              'right_middle': rm_font,
                              'left_bottom': lb_font,
                              'middle_bottom': mb_font,
                              'right_bottom': rb_font,
                              'cannot_display_default': cdd_font,
                              'percent': p_font
                           },
                           args.fonts,
                           {
                               'last_type': 1 if args.use_last else 2 if args.use_mlst else 0,
                               'show_private': args.show_private,
                               'show_undefined': args.show_undefined
                           })
