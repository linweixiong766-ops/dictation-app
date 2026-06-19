#!/usr/bin/env node
/**
 * Generate a small sample of pinyin audio files for testing.
 *
 * Usage:
 *   node scripts/generate-sample-audio.js
 *
 * Output: public/audio/pinyin/ (sample files only)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, '..', 'public', 'audio', 'pinyin');

// Sample pinyin to generate (one per category)
const SAMPLE_PINYIN = {
  initials: { b: '玻', m: '摸', h: '喝' },
  'finals/single': { a: '啊', i: '衣' },
  'finals/compound': { ai: '哎', ou: '欧' },
  'finals/front-nasal': { an: '安', in: '因' },
  'finals/back-nasal': { ang: '昂', ing: '英' },
  'whole-syllables': { zhi: '知', yu: '鱼' },
  'triple-pinyin': { jia: '家', hua: '花' }
};

// Tone marks mapping
const TONE_MARKS = {
  a: ['ā', 'á', 'ǎ', 'à'],
  o: ['ō', 'ó', 'ǒ', 'ò'],
  e: ['ē', 'é', 'ě', 'è'],
  i: ['ī', 'í', 'ǐ', 'ì'],
  u: ['ū', 'ú', 'ǔ', 'ù'],
  'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ']
};

function getTonedPinyin(basePinyin, tone) {
  if (tone === 0) return basePinyin;

  for (const vowel of ['a', 'o', 'e', 'ü']) {
    if (basePinyin.includes(vowel)) {
      const idx = basePinyin.indexOf(vowel);
      return basePinyin.slice(0, idx) + TONE_MARKS[vowel][tone - 1] + basePinyin.slice(idx + 1);
    }
  }

  if (basePinyin.includes('iu')) {
    const idx = basePinyin.indexOf('u');
    return basePinyin.slice(0, idx) + TONE_MARKS.u[tone - 1] + basePinyin.slice(idx + 1);
  }

  if (basePinyin.includes('i')) {
    const idx = basePinyin.indexOf('i');
    return basePinyin.slice(0, idx) + TONE_MARKS.i[tone - 1] + basePinyin.slice(idx + 1);
  }

  if (basePinyin.includes('u')) {
    const idx = basePinyin.indexOf('u');
    return basePinyin.slice(0, idx) + TONE_MARKS.u[tone - 1] + basePinyin.slice(idx + 1);
  }

  return basePinyin;
}

function generateAudio(text, outputPath) {
  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  if (fs.existsSync(outputPath)) {
    console.log(`  [跳过] ${outputPath}`);
    return true;
  }

  try {
    execSync(`npx edge-tts --voice "zh-CN-XiaoxiaoNeural" --text "${text}" --write-media "${outputPath}"`, {
      stdio: 'pipe',
      timeout: 30000
    });
    console.log(`  [生成] ${outputPath} (${text})`);
    return true;
  } catch (e) {
    console.error(`  [失败] ${outputPath}: ${e.message}`);
    return false;
  }
}

function main() {
  console.log('生成样本音频文件...\n');

  let total = 0;
  let generated = 0;

  for (const [category, pinyins] of Object.entries(SAMPLE_PINYIN)) {
    console.log(`\n${category}:`);

    for (const [basePinyin, chineseChar] of Object.entries(pinyins)) {
      if (category === 'initials') {
        total++;
        const outputPath = path.join(OUTPUT_DIR, category, `${basePinyin}.mp3`);
        if (generateAudio(chineseChar, outputPath)) {
          generated++;
        }
      } else {
        // Generate first tone only for sample
        total++;
        const toned = getTonedPinyin(basePinyin, 1);
        const outputPath = path.join(OUTPUT_DIR, category, `${basePinyin}1.mp3`);
        if (generateAudio(toned, outputPath)) {
          generated++;
        }
      }
    }
  }

  console.log(`\n完成! 共 ${total} 个文件, 成功 ${generated} 个`);
  console.log('\n现在可以运行 npm run dev 并访问 http://localhost:5178 测试音频效果');
}

main();
