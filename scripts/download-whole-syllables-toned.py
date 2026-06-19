#!/usr/bin/env python3
"""
下载带声调的整体认读音节
从 https://img.zdic.net/audio/zd/py/ 下载
"""

import os
import urllib.request
import urllib.parse

# 基础URL
BASE_URL = "https://img.zdic.net/audio/zd/py"

# 输出目录
OUTPUT_DIR = "public/audio/pinyin/whole-syllables"

# 整体认读音节列表
WHOLE_SYLLABLES = [
    "zhi", "chi", "shi", "ri", "zi", "ci", "si", "yi",
    "wu", "yu", "ye", "yue", "yuan", "yin", "yun", "ying"
]

# 声调映射 - 韵母到带声调版本
TONE_MAP = {
    # 单韵母
    'a': ['ā', 'á', 'ǎ', 'à'],
    'o': ['ō', 'ó', 'ǒ', 'ò'],
    'e': ['ē', 'é', 'ě', 'è'],
    'i': ['ī', 'í', 'ǐ', 'ì'],
    'u': ['ū', 'ú', 'ǔ', 'ù'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ'],
}

def get_tone_pinyin(base_pinyin, tone):
    """获取带声调的拼音"""
    # 找到需要加声调的韵母
    vowels = 'aoeiuü'

    # 特殊处理：如果以 i 结尾且前面有元音，声调加在前面的元音上
    if base_pinyin.endswith('i') and len(base_pinyin) > 1:
        # 检查前面是否有元音
        for v in vowels:
            if v in base_pinyin[:-1]:
                # 声调加在前面的元音上
                idx = base_pinyin.rfind(v)
                toned_vowel = TONE_MAP[v][tone - 1]
                return base_pinyin[:idx] + toned_vowel + base_pinyin[idx+1:]

    # 特殊处理：如果以 u 结尾且前面有元音，声调加在前面的元音上
    if base_pinyin.endswith('u') and len(base_pinyin) > 1:
        for v in vowels:
            if v in base_pinyin[:-1]:
                idx = base_pinyin.rfind(v)
                toned_vowel = TONE_MAP[v][tone - 1]
                return base_pinyin[:idx] + toned_vowel + base_pinyin[idx+1:]

    # 默认：找到第一个元音并加声调
    for v in vowels:
        if v in base_pinyin:
            idx = base_pinyin.index(v)
            toned_vowel = TONE_MAP[v][tone - 1]
            return base_pinyin[:idx] + toned_vowel + base_pinyin[idx+1:]

    return base_pinyin

def download_file(url, output_path):
    """下载文件"""
    try:
        # URL编码
        encoded_url = urllib.parse.quote(url, safe=':/')
        urllib.request.urlretrieve(encoded_url, output_path)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("开始下载带声调的整体认读音节...")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    success = 0
    failed = 0

    for pinyin in WHOLE_SYLLABLES:
        for tone in range(1, 5):
            # 获取带声调的拼音
            toned_pinyin = get_tone_pinyin(pinyin, tone)

            # 构建URL和输出路径
            url = f"{BASE_URL}/{toned_pinyin}.mp3"
            output_path = os.path.join(OUTPUT_DIR, f"{pinyin}{tone}.mp3")

            print(f"  {pinyin}{tone} ({toned_pinyin})...", end=" ", flush=True)

            if download_file(url, output_path):
                # 检查文件大小
                size = os.path.getsize(output_path)
                if size > 1000:
                    print(f"OK ({size} bytes)")
                    success += 1
                else:
                    print(f"FAILED (too small: {size} bytes)")
                    os.remove(output_path)
                    failed += 1
            else:
                print("FAILED")
                failed += 1

    print(f"\n完成！成功: {success}, 失败: {failed}")
    print(f"输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
