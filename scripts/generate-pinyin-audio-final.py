"""
使用 edge-tts 生成所有拼音音频文件
- 声母: 使用对应汉字发音
- 韵母/音节: 使用拼音+声调说明
"""
import asyncio
import os
import sys
import edge_tts

# Windows GBK fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'audio', 'pinyin')

# 声母 → 对应汉字
INITIALS_MAP = {
    'b': '玻', 'p': '坡', 'm': '摸', 'f': '佛',
    'd': '得', 't': '特', 'n': '讷', 'l': '勒',
    'g': '哥', 'k': '科', 'h': '喝',
    'j': '鸡', 'q': '七', 'x': '西',
    'zh': '知', 'ch': '吃', 'sh': '诗', 'r': '日',
    'z': '资', 'c': '雌', 's': '思',
    'y': '衣', 'w': '乌'
}

# 单韵母 → 对应汉字
SINGLE_FINALS_MAP = {
    'a': '啊', 'o': '哦', 'e': '鹅', 'i': '衣', 'u': '乌', 'ü': '鱼'
}

# 韵母列表
COMPOUND_FINALS = ['ai', 'ei', 'ao', 'ou', 'ia', 'ie', 'ua', 'uo', 'üe']
FRONT_NASAL = ['an', 'en', 'in', 'un', 'ün']
BACK_NASAL = ['ang', 'eng', 'ing', 'ong']

# 整体认读音节
WHOLE_SYLLABLES = [
    'zhi', 'chi', 'shi', 'ri', 'zi', 'ci', 'si', 'yi',
    'wu', 'yu', 'ye', 'yue', 'yuan', 'yin', 'yun', 'ying'
]

# 三拼音节
TRIPLE_PINYIN = [
    'ia', 'iao', 'ian', 'iang', 'iong',
    'ua', 'uai', 'uan', 'uang', 'üan',
    'üe', 'ün'
]

# 声调映射
TONE_MAP = {
    'a': ['ā', 'á', 'ǎ', 'à'],
    'o': ['ō', 'ó', 'ǒ', 'ò'],
    'e': ['ē', 'é', 'ě', 'è'],
    'i': ['ī', 'í', 'ǐ', 'ì'],
    'u': ['ū', 'ú', 'ǔ', 'ù'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ']
}

def get_tone_pinyin(pinyin, tone):
    """获取带声调的拼音"""
    for vowel, tones in TONE_MAP.items():
        if vowel in pinyin:
            return pinyin.replace(vowel, tones[tone - 1])
    return pinyin

async def generate_audio(text, output_path, voice="zh-CN-XiaoxiaoNeural"):
    """生成单个音频文件"""
    if os.path.exists(output_path):
        return True
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

async def main():
    print("开始生成拼音音频文件...")

    # 创建目录
    dirs = {
        'initials': os.path.join(OUTPUT_DIR, 'initials'),
        'single': os.path.join(OUTPUT_DIR, 'finals', 'single'),
        'compound': os.path.join(OUTPUT_DIR, 'finals', 'compound'),
        'front_nasal': os.path.join(OUTPUT_DIR, 'finals', 'front-nasal'),
        'back_nasal': os.path.join(OUTPUT_DIR, 'finals', 'back-nasal'),
        'whole': os.path.join(OUTPUT_DIR, 'whole-syllables'),
        'triple': os.path.join(OUTPUT_DIR, 'triple-pinyin')
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    total = 0
    success = 0
    failed = 0

    # 1. 声母 (23个)
    print("\n=== 声母 (23个) ===")
    for pinyin, char in INITIALS_MAP.items():
        path = os.path.join(dirs['initials'], f"{pinyin}.mp3")
        total += 1
        if await generate_audio(char, path):
            print(f"✓ {pinyin} ({char})")
            success += 1
        else:
            print(f"✗ {pinyin}")
            failed += 1
        await asyncio.sleep(0.3)

    # 2. 单韵母 (6个 × 4声调 = 24个)
    print("\n=== 单韵母 (24个) ===")
    for pinyin, char in SINGLE_FINALS_MAP.items():
        for tone in range(1, 5):
            filename = f"{pinyin}{tone}.mp3"
            path = os.path.join(dirs['single'], filename)
            total += 1
            if await generate_audio(char, path):
                print(f"✓ {filename}")
                success += 1
            else:
                print(f"✗ {filename}")
                failed += 1
            await asyncio.sleep(0.3)

    # 3. 复韵母 (9个 × 4声调 = 36个)
    print("\n=== 复韵母 (36个) ===")
    for pinyin in COMPOUND_FINALS:
        for tone in range(1, 5):
            filename = f"{pinyin}{tone}.mp3"
            path = os.path.join(dirs['compound'], filename)
            toned = get_tone_pinyin(pinyin, tone)
            total += 1
            if await generate_audio(toned, path):
                print(f"✓ {filename} → {toned}")
                success += 1
            else:
                print(f"✗ {filename}")
                failed += 1
            await asyncio.sleep(0.3)

    # 4. 前鼻韵母 (5个 × 4声调 = 20个)
    print("\n=== 前鼻韵母 (20个) ===")
    for pinyin in FRONT_NASAL:
        for tone in range(1, 5):
            filename = f"{pinyin}{tone}.mp3"
            path = os.path.join(dirs['front_nasal'], filename)
            toned = get_tone_pinyin(pinyin, tone)
            total += 1
            if await generate_audio(toned, path):
                print(f"✓ {filename} → {toned}")
                success += 1
            else:
                print(f"✗ {filename}")
                failed += 1
            await asyncio.sleep(0.3)

    # 5. 后鼻韵母 (4个 × 4声调 = 16个)
    print("\n=== 后鼻韵母 (16个) ===")
    for pinyin in BACK_NASAL:
        for tone in range(1, 5):
            filename = f"{pinyin}{tone}.mp3"
            path = os.path.join(dirs['back_nasal'], filename)
            toned = get_tone_pinyin(pinyin, tone)
            total += 1
            if await generate_audio(toned, path):
                print(f"✓ {filename} → {toned}")
                success += 1
            else:
                print(f"✗ {filename}")
                failed += 1
            await asyncio.sleep(0.3)

    # 6. 整体认读音节 (16个 × 4声调 = 64个)
    print("\n=== 整体认读音节 (64个) ===")
    for pinyin in WHOLE_SYLLABLES:
        for tone in range(1, 5):
            filename = f"{pinyin}{tone}.mp3"
            path = os.path.join(dirs['whole'], filename)
            toned = get_tone_pinyin(pinyin, tone)
            total += 1
            if await generate_audio(toned, path):
                print(f"✓ {filename} → {toned}")
                success += 1
            else:
                print(f"✗ {filename}")
                failed += 1
            await asyncio.sleep(0.3)

    # 7. 三拼音节 (12个 × 4声调 = 48个)
    print("\n=== 三拼音节 (48个) ===")
    for pinyin in TRIPLE_PINYIN:
        for tone in range(1, 5):
            filename = f"{pinyin}{tone}.mp3"
            path = os.path.join(dirs['triple'], filename)
            toned = get_tone_pinyin(pinyin, tone)
            total += 1
            if await generate_audio(toned, path):
                print(f"✓ {filename} → {toned}")
                success += 1
            else:
                print(f"✗ {filename}")
                failed += 1
            await asyncio.sleep(0.3)

    print(f"\n{'='*50}")
    print(f"生成完成!")
    print(f"总计: {total}, 成功: {success}, 失败: {failed}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"{'='*50}")

if __name__ == '__main__':
    asyncio.run(main())
