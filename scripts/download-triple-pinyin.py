#!/usr/bin/env python3
"""
下载三拼音节音频
从 https://img.zdic.net/audio/zd/py/ 下载
"""

import os
import urllib.request
import urllib.parse

# 基础URL
BASE_URL = "https://img.zdic.net/audio/zd/py"

# 输出目录
OUTPUT_DIR = "public/audio/pinyin/triple-pinyin"

# 三拼音节定义
TRIPLE_PINYIN = {
    # 介母i系列
    "ia": ["jia", "qia", "xia"],
    "iao": ["jiao", "qiao", "xiao", "diao", "tiao", "niao", "liao"],
    "ian": ["jian", "qian", "xian", "dian", "tian", "nian", "lian"],
    "iang": ["jiang", "qiang", "xiang", "liang", "niang"],
    "iong": ["jiong", "qiong", "xiong"],

    # 介母u系列
    "ua": ["gua", "kua", "hua", "zhua", "chua", "shua"],
    "uo": ["guo", "kuo", "huo", "zhuo", "chuo", "shuo", "ruo", "zuo", "cuo", "suo", "duo", "tuo", "nuo", "luo"],
    "uai": ["guai", "kuai", "huai", "zhuai", "chuai", "shuai"],
    "uan": ["guan", "kuan", "huan", "zhuan", "chuan", "shuan", "ruan", "zuan", "cuan", "suan", "duan", "tuan", "nuan", "luan"],
    "uang": ["guang", "kuang", "huang", "zhuang", "chuang", "shuang"],

    # 介母ü系列
    "üan": ["juan", "quan", "xuan", "yuan", "nüan", "lüan"],
}

# 声调映射 - 韵母到带声调版本
TONE_MAP = {
    'a': ['ā', 'á', 'ǎ', 'à'],
    'o': ['ō', 'ó', 'ǒ', 'ò'],
    'e': ['ē', 'é', 'ě', 'è'],
    'i': ['ī', 'í', 'ǐ', 'ì'],
    'u': ['ū', 'ú', 'ǔ', 'ù'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ'],
}

def get_tone_pinyin(base_pinyin, tone):
    """获取带声调的拼音"""
    # 特殊处理：j, q, x, y 后面的 ü 写成 u
    if base_pinyin[0] in 'jqxy' and 'u' in base_pinyin[1:]:
        # 将 u 替换为 ü 来添加声调
        pinyin_chars = list(base_pinyin)
        for idx in range(len(pinyin_chars) - 1, 0, -1):
            if pinyin_chars[idx] == 'u':
                pinyin_chars[idx] = 'ü'
                break
        base_pinyin = ''.join(pinyin_chars)

    # 找到最后一个元音并加声调
    vowels = 'aeiouü'

    # 优先在 a, o, e 上加声调
    for v in ['a', 'o', 'e']:
        if v in base_pinyin:
            idx = base_pinyin.rfind(v)
            toned_vowel = TONE_MAP[v][tone - 1]
            return base_pinyin[:idx] + toned_vowel + base_pinyin[idx+1:]

    # 如果没有 a, o, e，在 i, u, ü 上加声调
    for v in ['i', 'u', 'ü']:
        if v in base_pinyin:
            idx = base_pinyin.rfind(v)
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
        return False

def main():
    print("开始下载三拼音节音频...")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    success = 0
    failed = 0
    skipped = 0
    total = 0

    for group, pinyins in TRIPLE_PINYIN.items():
        print(f"\n【{group}】")
        for pinyin in pinyins:
            for tone in range(1, 5):
                total += 1
                # 获取带声调的拼音
                toned_pinyin = get_tone_pinyin(pinyin, tone)

                # 构建输出路径
                filename = f"{pinyin}{tone}.mp3"
                output_path = os.path.join(OUTPUT_DIR, filename)

                # 检查文件是否已存在
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    skipped += 1
                    continue

                # 构建URL
                url = f"{BASE_URL}/{toned_pinyin}.mp3"

                print(f"  {filename} ({toned_pinyin})...", end=" ", flush=True)

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

    print(f"\n{'='*50}")
    print(f"下载完成！")
    print(f"总计: {total}, 成功: {success}, 失败: {failed}, 跳过: {skipped}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
