/**
 * TTS (Text-to-Speech) utility using Web Speech API
 */

let synth = window.speechSynthesis;

// Pinyin to Chinese character pronunciation mapping
const pinyinToChinese = {
  // 声母 (Initials) - 23个
  'b': '玻', 'p': '坡', 'm': '摸', 'f': '佛',
  'd': '得', 't': '特', 'n': '讷', 'l': '勒',
  'g': '哥', 'k': '科', 'h': '喝',
  'j': '基', 'q': '欺', 'x': '希',
  'zh': '知', 'ch': '吃', 'sh': '诗', 'r': '日',
  'z': '资', 'c': '雌', 's': '思',
  'y': '衣', 'w': '乌',

  // 单韵母 (Single finals) - 6个
  'a': '啊', 'o': '哦', 'e': '鹅', 'i': '衣', 'u': '乌', 'ü': '鱼',

  // 复韵母 (Compound finals) - 9个
  'ai': '哎', 'ei': '诶', 'ui': '威', 'ao': '熬', 'ou': '欧',
  'iu': '优', 'ie': '耶', 'üe': '约', 'er': '儿',

  // 前鼻韵母 (Front nasal finals) - 5个
  'an': '安', 'en': '恩', 'in': '因', 'un': '温', 'ün': '云',

  // 后鼻韵母 (Back nasal finals) - 4个
  'ang': '昂', 'eng': '鞥', 'ing': '英', 'ong': '翁',

  // 整体认读音节 (Whole syllables) - 16个
  'zhi': '知', 'chi': '吃', 'shi': '诗', 'ri': '日',
  'zi': '资', 'ci': '雌', 'si': '思',
  'yi': '衣', 'wu': '乌', 'yu': '鱼',
  'ye': '耶', 'yue': '约', 'yuan': '元',
  'yin': '因', 'yun': '云', 'ying': '英',

  // 三拼音节 (Triple pinyin syllables) - 常用的
  'jia': '家', 'qia': '恰', 'xia': '虾',
  'jiao': '交', 'qiao': '敲', 'xiao': '消',
  'jian': '间', 'qian': '千', 'xian': '先',
  'jiang': '江', 'qiang': '枪', 'xiang': '香',
  'jiong': '窘', 'qiong': '穷', 'xiong': '兄',
  'gua': '瓜', 'kua': '夸', 'hua': '花',
  'guo': '国', 'kuo': '阔', 'huo': '火',
  'guai': '乖', 'kuai': '快', 'huai': '怀',
  'guan': '关', 'kuan': '宽', 'huan': '欢',
  'guang': '光', 'kuang': '狂', 'huang': '黄',
  'juan': '卷', 'quan': '全', 'xuan': '宣',
  'zhua': '抓', 'chua': '欻', 'shua': '刷',
  'zhuo': '桌', 'chuo': '戳', 'shuo': '说', 'ruo': '弱',
  'zhuai': '拽', 'chuai': '揣', 'shuai': '摔',
  'zhuan': '专', 'chuan': '穿', 'shuan': '栓', 'ruan': '软',
  'zhuang': '装', 'chuang': '窗', 'shuang': '双',
  'diao': '刁', 'tiao': '挑', 'niao': '鸟', 'liao': '聊',
  'dian': '颠', 'tian': '天', 'nian': '年', 'lian': '连',
  'liang': '良', 'niang': '娘',
  'duo': '多', 'tuo': '拖', 'nuo': '挪', 'luo': '罗',
  'duan': '端', 'tuan': '团', 'nuan': '暖', 'luan': '乱',
  'zuo': '做', 'cuo': '错', 'suo': '所',
  'zuan': '钻', 'cuan': '窜', 'suan': '算',
  'nüan': '暖', 'lüan': '乱'
};

/**
 * Speak a word using TTS
 * @param {string} text - The word to speak
 * @param {string} lang - Language code (e.g., 'en-US', 'zh-CN')
 * @param {number} rate - Speech rate (0.1 to 10, default 0.8)
 * @returns {Promise<void>}
 */
export function speak(text, lang = 'en-US', rate = 0.8) {
  return new Promise((resolve, reject) => {
    if (!synth) {
      reject(new Error('Speech synthesis not supported'));
      return;
    }

    // Cancel any ongoing speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = rate;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onend = () => resolve();
    utterance.onerror = (event) => reject(event.error);

    synth.speak(utterance);
  });
}

/**
 * Speak a word in English
 * @param {string} word - The English word
 * @param {number} rate - Speech rate
 */
export function speakEnglish(word, rate = 0.8) {
  return speak(word, 'en-US', rate);
}

/**
 * Speak a word in Chinese
 * @param {string} word - The Chinese word
 * @param {number} rate - Speech rate
 */
export function speakChinese(word, rate = 0.8) {
  return speak(word, 'zh-CN', rate);
}

/**
 * Speak pinyin using Chinese pronunciation
 * @param {string} pinyin - The pinyin to speak (e.g., 'b', 'ai', 'ang')
 * @param {number} rate - Speech rate
 */
export function speakPinyin(pinyin, rate = 0.6) {
  // Convert to lowercase for lookup
  const normalizedPinyin = pinyin.toLowerCase().replace(/[āáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜ]/g, (match) => {
    // Remove tone marks for lookup
    const toneMap = {
      'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
      'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
      'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
      'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
      'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
      'ǖ': 'ü', 'ǘ': 'ü', 'ǚ': 'ü', 'ǜ': 'ü'
    };
    return toneMap[match] || match;
  });

  // Look up the Chinese character for this pinyin
  const chineseChar = pinyinToChinese[normalizedPinyin];

  if (chineseChar) {
    // Speak the Chinese character
    return speak(chineseChar, 'zh-CN', rate);
  } else {
    // Fallback: speak the pinyin directly
    return speak(pinyin, 'zh-CN', rate);
  }
}

/**
 * Check if speech synthesis is supported
 * @returns {boolean}
 */
export function isSpeechSupported() {
  return 'speechSynthesis' in window;
}

/**
 * Get available voices for a language
 * @param {string} lang - Language code
 * @returns {SpeechSynthesisVoice[]}
 */
export function getVoices(lang) {
  return synth.getVoices().filter(voice => voice.lang.startsWith(lang));
}
