import os
import json

folder = 'D:/First-cc/first_cc/dictation-app/public/audio/pinyin/all-pinyin'
files = [f.replace('.mp3', '') for f in os.listdir(folder) if f.endswith('.mp3')]

def remove_tones(s):
    result = ''
    for c in s:
        if c in 'āáǎà': result += 'a'
        elif c in 'ēéěè': result += 'e'
        elif c in 'īíǐì': result += 'i'
        elif c in 'ōóǒò': result += 'o'
        elif c in 'ūúǔù': result += 'u'
        elif c in 'ǖǘǚǜ': result += 'v'
        elif c == 'ü': result += 'v'
        else: result += c
    return result

initials_list = ['zh', 'ch', 'sh', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'r', 'z', 'c', 's', 'y', 'w']

initial_sounds = {
    'b': 'b', 'p': 'p', 'm': 'm', 'f': 'f',
    'd': 'd', 't': 't', 'n': 'n', 'l': 'l',
    'g': 'g', 'k': 'k', 'h': 'h',
    'j': 'j', 'q': 'q', 'x': 'x',
    'zh': 'zh', 'ch': 'ch', 'sh': 'sh', 'r': 'r',
    'z': 'z', 'c': 'c', 's': 's',
    'y': 'y', 'w': 'w'
}

whole_syllables = ['zhi', 'chi', 'shi', 'ri', 'zi', 'ci', 'si', 'yi', 'wu', 'yu', 'ye', 'yue', 'yuan', 'yin', 'yun', 'ying']
medials = ['i', 'u', 'v']
single_vowels = ['a', 'o', 'e', 'i', 'u', 'v']
compound_vowels = ['ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 've', 'er']
compound_vowels_extended = compound_vowels + ['ue']
front_nasal = ['an', 'en', 'in', 'un', 'vn']
back_nasal = ['ang', 'eng', 'ing', 'ong']
valid_finals = single_vowels + compound_vowels + front_nasal + back_nasal

words = []
seen = set()

# 首先添加整体认读音节
whole_syllable_data = [
    ('zhi', 'zh'), ('chi', 'ch'), ('shi', 'sh'), ('ri', 'r'),
    ('zi', 'z'), ('ci', 'c'), ('si', 's'),
    ('yi', 'y'), ('wu', 'w'), ('yu', 'y'),
    ('ye', 'y'), ('yue', 'y'), ('yuan', 'y'),
    ('yin', 'y'), ('yun', 'y'), ('ying', 'y')
]

for base, initial in whole_syllable_data:
    # 找到所有带声调的版本
    for f in files:
        if remove_tones(f) == base and f not in seen:
            seen.add(f)
            initial_sound = initial_sounds.get(initial, initial)
            words.append({
                'word': f,
                'meaning': '拼读练习',
                'pinyin': f,
                'unit': '整体认读拼读',
                'initial': initial,
                'medial': None,
                'initialSound': initial_sound,
                'blendParts': [initial_sound, f]
            })

for pinyin in sorted(files):
    base = remove_tones(pinyin)
    if pinyin in seen:
        continue
    seen.add(pinyin)
    if base in whole_syllables:
        continue

    initial = None
    for i in initials_list:
        if base.startswith(i):
            initial = i
            break
    if not initial:
        continue

    rest_base = base[len(initial):]
    rest_pinyin = pinyin[len(initial):]
    initial_sound = initial_sounds.get(initial, initial)

    # 先检查是否是两拼音节（initial + final）
    if rest_base in single_vowels or rest_base in compound_vowels or rest_base in front_nasal or rest_base in back_nasal:
        medial = None
        final = rest_pinyin
        blend_parts = [initial_sound, final, pinyin]

        if rest_base in single_vowels:
            category = '单韵母拼读'
        elif rest_base in compound_vowels:
            category = '复韵母拼读'
        elif rest_base in front_nasal:
            category = '前鼻韵母拼读'
        elif rest_base in back_nasal:
            category = '后鼻韵母拼读'
    # 检查是否是三拼音节（initial + medial + final）
    elif len(rest_base) >= 2 and rest_base[0] in medials:
        medial = rest_base[0]
        final_base = rest_base[1:]
        final_pinyin = rest_pinyin[1:]

        # 检查 medial + final 是否组成复韵母
        combined = medial + final_base
        if combined in compound_vowels_extended:
            # 这是复韵母，不是三拼音节
            # 将 ue 转换为 ve 以便音频文件查找
            def convert_ue_to_ve(s):
                result = ''
                for c in s:
                    if c in 'ēéěè':
                        if result and result[-1] == 'u':
                            result = result[:-1] + 'v'
                        result += c
                    else:
                        result += c
                return result

            final = convert_ue_to_ve(rest_pinyin)
            medial = None
            blend_parts = [initial_sound, final, pinyin]
            category = '复韵母拼读'
        elif final_base in valid_finals:
            # 三拼音节：介母读轻声
            medial_sound = medial
            blend_parts = [initial_sound, medial_sound, final_pinyin, pinyin]
            category = '三拼音节拼读'
        else:
            medial = None
            final = rest_pinyin
            blend_parts = [initial_sound, final, pinyin]
            category = '其他拼读'
    else:
        medial = None
        final = rest_pinyin
        blend_parts = [initial_sound, final, pinyin]
        category = '其他拼读'

    words.append({
        'word': pinyin,
        'meaning': '拼读练习',
        'pinyin': pinyin,
        'unit': category,
        'initial': initial,
        'medial': medial,
        'initialSound': initial_sound,
        'blendParts': blend_parts
    })

# 添加缺失的 y/w 拼音
yw_missing = [
    ('yā', 'y', 'ā'), ('yá', 'y', 'á'), ('yǎ', 'y', 'ǎ'), ('yà', 'y', 'à'),
    ('yān', 'y', 'ān'), ('yán', 'y', 'án'), ('yǎn', 'y', 'ǎn'), ('yàn', 'y', 'àn'),
    ('yāng', 'y', 'āng'), ('yáng', 'y', 'áng'), ('yǎng', 'y', 'ǎng'), ('yàng', 'y', 'àng'),
    ('yāo', 'y', 'āo'), ('yáo', 'y', 'áo'), ('yǎo', 'y', 'ǎo'), ('yào', 'y', 'ào'),
    ('yō', 'y', 'ō'), ('yó', 'y', 'ó'), ('yǒ', 'y', 'ǒ'), ('yò', 'y', 'ò'),
    ('yōng', 'y', 'ōng'), ('yóng', 'y', 'óng'), ('yǒng', 'y', 'ǒng'), ('yòng', 'y', 'òng'),
    ('yōu', 'y', 'ōu'), ('yóu', 'y', 'óu'), ('yǒu', 'y', 'ǒu'), ('yòu', 'y', 'òu'),
    ('wā', 'w', 'ā'), ('wá', 'w', 'á'), ('wǎ', 'w', 'ǎ'), ('wà', 'w', 'à'),
    ('wāi', 'w', 'āi'), ('wái', 'w', 'ái'), ('wǎi', 'w', 'ǎi'), ('wài', 'w', 'ài'),
    ('wān', 'w', 'ān'), ('wán', 'w', 'án'), ('wǎn', 'w', 'ǎn'), ('wàn', 'w', 'àn'),
    ('wāng', 'w', 'āng'), ('wáng', 'w', 'áng'), ('wǎng', 'w', 'ǎng'), ('wàng', 'w', 'àng'),
    ('wēi', 'w', 'ēi'), ('wéi', 'w', 'éi'), ('wěi', 'w', 'ěi'), ('wèi', 'w', 'èi'),
    ('wēn', 'w', 'ēn'), ('wén', 'w', 'én'), ('wěn', 'w', 'ěn'), ('wèn', 'w', 'èn'),
    ('wēng', 'w', 'ēng'), ('wéng', 'w', 'éng'), ('wěng', 'w', 'ěng'), ('wèng', 'w', 'èng'),
    ('wō', 'w', 'ō'), ('wó', 'w', 'ó'), ('wǒ', 'w', 'ǒ'), ('wò', 'w', 'ò'),
]

for pinyin, initial, final in yw_missing:
    if pinyin not in seen:
        seen.add(pinyin)
        initial_sound = initial_sounds.get(initial, initial)

        final_base = remove_tones(final)
        if final_base in single_vowels:
            category = '单韵母拼读'
        elif final_base in compound_vowels:
            category = '复韵母拼读'
        elif final_base in front_nasal:
            category = '前鼻韵母拼读'
        elif final_base in back_nasal:
            category = '后鼻韵母拼读'
        else:
            category = '复韵母拼读'

        words.append({
            'word': pinyin,
            'meaning': '拼读练习',
            'pinyin': pinyin,
            'unit': category,
            'initial': initial,
            'medial': None,
            'initialSound': initial_sound,
            'blendParts': [initial_sound, final, pinyin]
        })

# 添加缺失的 yué 和 yuě
extra_missing = [
    ('yué', 'y', 'ué'),
    ('yuě', 'y', 'uě'),
]

for pinyin, initial, final in extra_missing:
    if pinyin not in seen:
        seen.add(pinyin)
        initial_sound = initial_sounds.get(initial, initial)
        words.append({
            'word': pinyin,
            'meaning': '拼读练习',
            'pinyin': pinyin,
            'unit': '复韵母拼读',
            'initial': initial,
            'medial': None,
            'initialSound': initial_sound,
            'blendParts': [initial_sound, final, pinyin]
        })

words.sort(key=lambda x: (x['unit'], remove_tones(x['word'])))

data = {
    'name': '学前拼音-拼读',
    'language': 'zh',
    'category': '学前拼音-拼读',
    'words': words
}

output = 'D:/First-cc/first_cc/dictation-app/public/data/zh/pinyin-reading.json'
with open(output, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

from collections import Counter
cats = Counter(w['unit'] for w in words)
print('Summary:')
for cat, count in sorted(cats.items()):
    print(f'  {cat}: {count}')
print(f'  Total: {len(words)}')

# Show juē, quē, xuē
print('\njuē, quē, xuē:')
for w in words:
    if w['word'] in ['juē', 'quē', 'xuē']:
        print(f'  {w["word"]}: {w["unit"]} -> {w["blendParts"]}')
