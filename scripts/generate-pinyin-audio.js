#!/usr/bin/env node
/**
 * Generate pinyin audio files using edge-tts (via npx).
 *
 * Usage:
 *   node scripts/generate-pinyin-audio.js
 *
 * Output: public/audio/pinyin/**/*.mp3
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, '..', 'public', 'audio', 'pinyin');

// ============================================================
//  Pinyin definitions
// ============================================================

const PINYIN_MAP = {
  // 声母 (23个)
  initials: {
    b: '玻', p: '坡', m: '摸', f: '佛',
    d: '得', t: '特', n: '讷', l: '勒',
    g: '哥', k: '科', h: '喝',
    j: '基', q: '欺', x: '希',
    zh: '知', ch: '吃', sh: '诗', r: '日',
    z: '资', c: '雌', s: '思',
    y: '衣', w: '乌'
  },

  // 单韵母 (6个)
  'finals/single': {
    a: '啊', o: '哦', e: '鹅', i: '衣', u: '乌', 'ü': '鱼'
  },

  // 复韵母 (9个)
  'finals/compound': {
    ai: '哎', ei: '诶', ui: '威', ao: '熬', ou: '欧',
    iu: '优', ie: '耶', 'üe': '约', er: '儿'
  },

  // 前鼻韵母 (5个)
  'finals/front-nasal': {
    an: '安', en: '恩', in: '因', un: '温', 'ün': '云'
  },

  // 后鼻韵母 (4个)
  'finals/back-nasal': {
    ang: '昂', eng: '鞥', ing: '英', ong: '翁'
  },

  // 整体认读音节 (16个)
  'whole-syllables': {
    zhi: '知', chi: '吃', shi: '诗', ri: '日',
    zi: '资', ci: '雌', si: '思',
    yi: '衣', wu: '乌', yu: '鱼',
    ye: '耶', yue: '约', yuan: '元',
    yin: '因', yun: '云', ying: '英'
  },

  // 三拼音节 (常用)
  'triple-pinyin': {
    jia: '家', qia: '恰', xia: '虾',
    jiao: '交', qiao: '敲', xiao: '消',
    jian: '间', qian: '千', xian: '先',
    jiang: '江', qiang: '枪', xiang: '香',
    jiong: '窘', qiong: '穷', xiong: '兄',
    gua: '瓜', kua: '夸', hua: '花',
    guo: '国', kuo: '阔', huo: '火',
    guai: '乖', kuai: '快', huai: '怀',
    guan: '关', kuan: '宽', huan: '欢',
    guang: '光', kuang: '狂', huang: '黄',
    juan: '卷', quan: '全', xuan: '宣',
    zhua: '抓', shua: '刷',
    zhuo: '桌', chuo: '戳', shuo: '说', ruo: '弱',
    zhuai: '拽', shuai: '摔',
    zhuan: '专', chuan: '穿', shuan: '栓', ruan: '软',
    zhuang: '装', chuang: '窗', shuang: '双',
    diao: '刁', tiao: '挑', niao: '鸟', liao: '聊',
    dian: '颠', tian: '天', nian: '年', lian: '连',
    liang: '良', niang: '娘',
    duo: '多', tuo: '拖', nuo: '挪', luo: '罗',
    duan: '端', tuan: '团', nuan: '暖', luan: '乱',
    zuo: '做', cuo: '错', suo: '所',
    zuan: '钻', cuan: '窜', suan: '算'
  }
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

  // Find the main vowel to add tone mark
  for (const vowel of ['a', 'o', 'e', 'ü']) {
    if (basePinyin.includes(vowel)) {
      const idx = basePinyin.indexOf(vowel);
      return basePinyin.slice(0, idx) + TONE_MARKS[vowel][tone - 1] + basePinyin.slice(idx + 1);
    }
  }

  // Special case for 'iu'
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
    return true; // Skip existing
  }

  try {
    // Use edge-tts via npx
    execSync(`npx edge-tts --voice "zh-CN-XiaoxiaoNeural" --text "${text}" --write-media "${outputPath}"`, {
      stdio: 'pipe',
      timeout: 30000
    });
    return true;
  } catch (e) {
    console.error(`Failed: ${outputPath}`, e.message);
    return false;
  }
}

function main() {
  let total = 0;
  let generated = 0;
  let failed = 0;

  for (const [category, pinyins] of Object.entries(PINYIN_MAP)) {
    const categoryDir = path.join(OUTPUT_DIR, category);

    for (const [basePinyin, chineseChar] of Object.entries(pinyins)) {
      if (category === 'initials') {
        // 声母不带声调
        total++;
        const outputPath = path.join(categoryDir, `${basePinyin}.mp3`);

        if (generateAudio(chineseChar, outputPath)) {
          if (fs.existsSync(outputPath)) {
            console.log(`  [生成] ${outputPath} (${chineseChar})`);
            generated++;
          } else {
            console.log(`  [跳过] ${outputPath}`);
            generated++;
          }
        } else {
          failed++;
        }
      } else {
        // 韵母和音节生成4个声调
        for (let tone = 1; tone <= 5; tone++) {
          total++;
          const toned = getTonedPinyin(basePinyin, tone);
          const filename = `${basePinyin}${tone}.mp3`;
          const outputPath = path.join(categoryDir, filename);

          if (generateAudio(toned, outputPath)) {
            if (fs.existsSync(outputPath)) {
              console.log(`  [生成] ${outputPath} (${toned})`);
              generated++;
            } else {
              console.log(`  [跳过] ${outputPath}`);
              generated++;
            }
          } else {
            failed++;
          }
        }
      }
    }
  }

  console.log(`\n完成! 共 ${total} 个文件, 成功 ${generated} 个, 失败 ${failed} 个`);
}

main();
