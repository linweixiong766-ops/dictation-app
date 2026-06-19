#!/usr/bin/env python3
"""
Generate pinyin audio files using edge-tts (Microsoft Edge TTS).

Usage:
  pip install edge-tts
  python generate-pinyin-audio.py

Output: public/audio/pinyin/**/*.mp3
"""

import asyncio
import os
import sys

try:
    import edge_tts
except ImportError:
    print("请先安装 edge-tts: pip install edge-tts")
    sys.exit(1)

# Voice options:
#   zh-CN-XiaoxiaoNeural (female, recommended)
#   zh-CN-YunxiNeural (male)
VOICE = "zh-CN-XiaoxiaoNeural"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "audio", "pinyin")

# ============================================================
#  Pinyin definitions
# ============================================================

PINYIN_MAP = {
    # 声母 (23个) - 用对应汉字发音
    "initials": {
        "b": "玻", "p": "坡", "m": "摸", "f": "佛",
        "d": "得", "t": "特", "n": "讷", "l": "勒",
        "g": "哥", "k": "科", "h": "喝",
        "j": "基", "q": "欺", "x": "希",
        "zh": "知", "ch": "吃", "sh": "诗", "r": "日",
        "z": "资", "c": "雌", "s": "思",
        "y": "衣", "w": "乌"
    },

    # 单韵母 (6个)
    "finals/single": {
        "a": "啊", "o": "哦", "e": "鹅", "i": "衣", "u": "乌", "ü": "鱼"
    },

    # 复韵母 (9个)
    "finals/compound": {
        "ai": "哎", "ei": "诶", "ui": "威", "ao": "熬", "ou": "欧",
        "iu": "优", "ie": "耶", "üe": "约", "er": "儿"
    },

    # 前鼻韵母 (5个)
    "finals/front-nasal": {
        "an": "安", "en": "恩", "in": "因", "un": "温", "ün": "云"
    },

    # 后鼻韵母 (4个)
    "finals/back-nasal": {
        "ang": "昂", "eng": "鞥", "ing": "英", "ong": "翁"
    },

    # 整体认读音节 (16个)
    "whole-syllables": {
        "zhi": "知", "chi": "吃", "shi": "诗", "ri": "日",
        "zi": "资", "ci": "雌", "si": "思",
        "yi": "衣", "wu": "乌", "yu": "鱼",
        "ye": "耶", "yue": "约", "yuan": "元",
        "yin": "因", "yun": "云", "ying": "英"
    },

    # 三拼音节 (常用)
    "triple-pinyin": {
        "jia": "家", "qia": "恰", "xia": "虾",
        "jiao": "交", "qiao": "敲", "xiao": "消",
        "jian": "间", "qian": "千", "xian": "先",
        "jiang": "江", "qiang": "枪", "xiang": "香",
        "jiong": "窘", "qiong": "穷", "xiong": "兄",
        "gua": "瓜", "kua": "夸", "hua": "花",
        "guo": "国", "kuo": "阔", "huo": "火",
        "guai": "乖", "kuai": "快", "huai": "怀",
        "guan": "关", "kuan": "宽", "huan": "欢",
        "guang": "光", "kuang": "狂", "huang": "黄",
        "juan": "卷", "quan": "全", "xuan": "宣",
        "zhua": "抓", "shua": "刷",
        "zhuo": "桌", "chuo": "戳", "shuo": "说", "ruo": "弱",
        "zhuai": "拽", "shuai": "摔",
        "zhuan": "专", "chuan": "穿", "shuan": "栓", "ruan": "软",
        "zhuang": "装", "chuang": "窗", "shuang": "双",
        "diao": "刁", "tiao": "挑", "niao": "鸟", "liao": "聊",
        "dian": "颠", "tian": "天", "nian": "年", "lian": "连",
        "liang": "良", "niang": "娘",
        "duo": "多", "tuo": "拖", "nuo": "挪", "luo": "罗",
        "duan": "端", "tuan": "团", "nuan": "暖", "luan": "乱",
        "zuo": "做", "cuo": "错", "suo": "所",
        "zuan": "钻", "cuan": "窜", "suan": "算"
    }
}

# Tone marks mapping
TONE_MARKS = {
    'a': ['ā', 'á', 'ǎ', 'à'],
    'o': ['ō', 'ó', 'ǒ', 'ò'],
    'e': ['ē', 'é', 'ě', 'è'],
    'i': ['ī', 'í', 'ǐ', 'ì'],
    'u': ['ū', 'ú', 'ǔ', 'ù'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ']
}

def get_toned_pinyin(base_pinyin, tone):
    """Convert base pinyin + tone number to toned pinyin."""
    if tone == 0:
        return base_pinyin

    # Find the main vowel to add tone mark
    # Priority: a > o > e > i > u > ü
    for vowel in ['a', 'o', 'e', 'ü']:
        if vowel in base_pinyin:
            idx = base_pinyin.index(vowel)
            return base_pinyin[:idx] + TONE_MARKS[vowel][tone-1] + base_pinyin[idx+1:]

    # For 'i' and 'u', handle special cases
    if 'iu' in base_pinyin:
        # Tone goes on 'u' in 'iu'
        idx = base_pinyin.index('u')
        return base_pinyin[:idx] + TONE_MARKS['u'][tone-1] + base_pinyin[idx+1:]

    if 'i' in base_pinyin:
        idx = base_pinyin.index('i')
        return base_pinyin[:idx] + TONE_MARKS['i'][tone-1] + base_pinyin[idx+1:]

    if 'u' in base_pinyin:
        idx = base_pinyin.index('u')
        return base_pinyin[:idx] + TONE_MARKS['u'][tone-1] + base_pinyin[idx+1:]

    return base_pinyin

async def generate_audio(text, output_path):
    """Generate a single audio file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

async def main():
    total = 0
    generated = 0
    failed = 0

    for category, pinyins in PINYIN_MAP.items():
        category_dir = os.path.join(OUTPUT_DIR, category)
        os.makedirs(category_dir, exist_ok=True)

        for base_pinyin, chinese_char in pinyins.items():
            if category == "initials":
                # 声母不带声调，用汉字发音
                total += 1
                output_path = os.path.join(category_dir, f"{base_pinyin}.mp3")
                if os.path.exists(output_path):
                    print(f"  [跳过] {output_path}")
                    generated += 1
                    continue
                try:
                    await generate_audio(chinese_char, output_path)
                    print(f"  [生成] {output_path} ({chinese_char})")
                    generated += 1
                except Exception as e:
                    print(f"  [失败] {output_path}: {e}")
                    failed += 1
            else:
                # 韵母和音节生成4个声调
                for tone in range(1, 5):
                    total += 1
                    toned = get_toned_pinyin(base_pinyin, tone)
                    filename = f"{base_pinyin}{tone}.mp3"
                    output_path = os.path.join(category_dir, filename)

                    if os.path.exists(output_path):
                        print(f"  [跳过] {output_path}")
                        generated += 1
                        continue

                    try:
                        await generate_audio(toned, output_path)
                        print(f"  [生成] {output_path} ({toned})")
                        generated += 1
                    except Exception as e:
                        print(f"  [失败] {output_path}: {e}")
                        failed += 1

    print(f"\n完成! 共 {total} 个文件, 成功 {generated} 个, 失败 {failed} 个")

if __name__ == "__main__":
    asyncio.run(main())
