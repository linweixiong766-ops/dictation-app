# 拼音音频资源生成指南

## 方案一：使用 edge-tts（推荐）

### 安装

```bash
# Python 版本
pip install edge-tts

# 或者使用 Node.js 版本（无需额外安装）
```

### 生成音频

```bash
# Python 版本
python scripts/generate-pinyin-audio.py

# Node.js 版本
npm run generate-audio
```

### 输出目录

```
public/audio/pinyin/
├── initials/           # 声母 (23个)
│   ├── b.mp3
│   ├── p.mp3
│   └── ...
├── finals/
│   ├── single/         # 单韵母 (24个)
│   │   ├── a1.mp3
│   │   ├── a2.mp3
│   │   └── ...
│   ├── compound/       # 复韵母 (36个)
│   ├── front-nasal/    # 前鼻韵母 (20个)
│   └── back-nasal/     # 后鼻韵母 (16个)
├── whole-syllables/    # 整体认读音节 (64个)
└── triple-pinyin/      # 三拼音节 (216个)
```

## 方案二：手动下载

如果无法使用 edge-tts，可以从以下资源下载：

1. **pinyin-dot-mp3** - npm 包
   ```bash
   npm install pinyin-dot-mp3
   ```

2. **Anki 拼音牌组** - 社区共享的发音牌组

3. **在线 TTS 服务**：
   - Google Cloud TTS
   - Azure Speech
   - 百度语音合成

## 音频文件命名规则

```
{基础拼音}{声调}.mp3

示例：
  b.mp3          - 声母 b（无声调）
  a1.mp3         - ā（第一声）
  a2.mp3         - á（第二声）
  a3.mp3         - ǎ（第三声）
  a4.mp3         - à（第四声）
  zhi3.mp3       - zhǐ（第三声）
  jiang4.mp3     - jiàng（第四声）
```

## 测试音频

生成后，访问 http://localhost:5178 测试拼音发音效果。

## 故障排除

### edge-tts 安装失败

```bash
# 使用国内镜像
pip install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 生成速度慢

edge-tts 需要网络连接到 Microsoft 服务器。如果网络较慢，可以：
1. 使用代理
2. 分批生成（修改脚本跳过已存在的文件）

### 音频文件太大

如果音频文件太大，可以使用 ffmpeg 压缩：
```bash
# 批量压缩
for f in public/audio/pinyin/**/*.mp3; do
  ffmpeg -i "$f" -b:a 64k "${f%.mp3}_compressed.mp3"
done
```
