#!/bin/bash
# 从 zdic.net 下载拼音音频文件

BASE_URL="https://zdic.net/ts/fulu/rtpy/pysd"
OUTPUT_DIR="public/audio/pinyin"

# 声母 (23个) - 没有声调
INITIALS="b p m f d t n l g k h j q x zh ch sh r z c s y w"

# 单韵母 (6个)
SINGLE_FINALS="a o e i u v"

# 复韵母 (9个)
COMPOUND_FINALS="ai ei ui ao ou iu ie ve er"

# 前鼻韵母 (5个)
FRONT_NASAL="an en in un vn"

# 后鼻韵母 (4个)
BACK_NASAL="ang eng ing ong"

# 整体认读音节 (16个)
WHOLE_SYLLABLES="zhi chi shi ri zi ci si yi wu yu ye yue yuan yin yun ying"

echo "=== 开始下载拼音音频 ==="
echo ""

# 1. 下载声母
echo "【下载声母】"
for p in $INITIALS; do
  url="${BASE_URL}/${p}.mp3"
  output="${OUTPUT_DIR}/initials/${p}.mp3"
  echo -n "  ${p}... "
  curl -s -o "$output" "$url"
  if [ -f "$output" ] && [ -s "$output" ]; then
    echo "OK"
  else
    echo "FAILED"
    rm -f "$output"
  fi
done
echo ""

# 2. 下载单韵母 (4个声调)
echo "【下载单韵母】"
for p in $SINGLE_FINALS; do
  for tone in 1 2 3 4; do
    url="${BASE_URL}/${p}${tone}.mp3"
    output="${OUTPUT_DIR}/finals/single/${p}${tone}.mp3"
    echo -n "  ${p}${tone}... "
    curl -s -o "$output" "$url"
    if [ -f "$output" ] && [ -s "$output" ]; then
      echo "OK"
    else
      echo "FAILED"
      rm -f "$output"
    fi
  done
done
echo ""

# 3. 下载复韵母 (4个声调)
echo "【下载复韵母】"
for p in $COMPOUND_FINALS; do
  for tone in 1 2 3 4; do
    url="${BASE_URL}/${p}${tone}.mp3"
    output="${OUTPUT_DIR}/finals/compound/${p}${tone}.mp3"
    echo -n "  ${p}${tone}... "
    curl -s -o "$output" "$url"
    if [ -f "$output" ] && [ -s "$output" ]; then
      echo "OK"
    else
      echo "FAILED"
      rm -f "$output"
    fi
  done
done
echo ""

# 4. 下载前鼻韵母 (4个声调)
echo "【下载前鼻韵母】"
for p in $FRONT_NASAL; do
  for tone in 1 2 3 4; do
    url="${BASE_URL}/${p}${tone}.mp3"
    output="${OUTPUT_DIR}/finals/front-nasal/${p}${tone}.mp3"
    echo -n "  ${p}${tone}... "
    curl -s -o "$output" "$url"
    if [ -f "$output" ] && [ -s "$output" ]; then
      echo "OK"
    else
      echo "FAILED"
      rm -f "$output"
    fi
  done
done
echo ""

# 5. 下载后鼻韵母 (4个声调)
echo "【下载后鼻韵母】"
for p in $BACK_NASAL; do
  for tone in 1 2 3 4; do
    url="${BASE_URL}/${p}${tone}.mp3"
    output="${OUTPUT_DIR}/finals/back-nasal/${p}${tone}.mp3"
    echo -n "  ${p}${tone}... "
    curl -s -o "$output" "$url"
    if [ -f "$output" ] && [ -s "$output" ]; then
      echo "OK"
    else
      echo "FAILED"
      rm -f "$output"
    fi
  done
done
echo ""

# 6. 下载整体认读音节 (4个声调)
echo "【下载整体认读音节】"
for p in $WHOLE_SYLLABLES; do
  for tone in 1 2 3 4; do
    url="${BASE_URL}/${p}${tone}.mp3"
    output="${OUTPUT_DIR}/whole-syllables/${p}${tone}.mp3"
    echo -n "  ${p}${tone}... "
    curl -s -o "$output" "$url"
    if [ -f "$output" ] && [ -s "$output" ]; then
      echo "OK"
    else
      echo "FAILED"
      rm -f "$output"
    fi
  done
done
echo ""

echo "=== 下载完成 ==="
echo ""
echo "统计："
echo "  声母: $(ls -1 ${OUTPUT_DIR}/initials/*.mp3 2>/dev/null | wc -l) 文件"
echo "  单韵母: $(ls -1 ${OUTPUT_DIR}/finals/single/*.mp3 2>/dev/null | wc -l) 文件"
echo "  复韵母: $(ls -1 ${OUTPUT_DIR}/finals/compound/*.mp3 2>/dev/null | wc -l) 文件"
echo "  前鼻韵母: $(ls -1 ${OUTPUT_DIR}/finals/front-nasal/*.mp3 2>/dev/null | wc -l) 文件"
echo "  后鼻韵母: $(ls -1 ${OUTPUT_DIR}/finals/back-nasal/*.mp3 2>/dev/null | wc -l) 文件"
echo "  整体认读: $(ls -1 ${OUTPUT_DIR}/whole-syllables/*.mp3 2>/dev/null | wc -l) 文件"
echo ""
total=$(find ${OUTPUT_DIR} -name "*.mp3" | wc -l)
echo "总计: ${total} 文件"
