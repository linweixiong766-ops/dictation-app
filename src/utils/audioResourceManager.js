/**
 * Audio Resource Manager for Pinyin Learning
 *
 * Manages pinyin audio file loading, caching, and playback.
 * Falls back to Web Speech API (TTS) when audio files are unavailable.
 *
 * Directory convention:
 *   public/audio/pinyin/{category}/{pinyin}{tone}.mp3
 *   public/audio/sfx/{effect}.mp3
 */

import { speakPinyin, speakChinese } from './audio.js'

// ============================================================
//  Category registry: maps pinyin to its subdirectory
// ============================================================
const CATEGORIES = {
  initials: [
    'b','p','m','f','d','t','n','l',
    'g','k','h','j','q','x',
    'zh','ch','sh','r','z','c','s','y','w'
  ],
  'finals/single':    ['a','o','e','i','u','v'],
  'finals/compound':  ['ai','ei','ui','ao','ou','iu','ie','ve','ue','er'],
  'finals/front-nasal': ['an','en','in','un','vn'],
  'finals/back-nasal':  ['ang','eng','ing','ong'],
  'whole-syllables':  [
    'zhi','chi','shi','ri','zi','ci','si',
    'yi','wu','yu','ye','yue','yuan','yin','yun','ying'
  ],
  'triple-pinyin': [
    'jia','qia','xia','jiao','qiao','xiao',
    'jian','qian','xian','jiang','qiang','xiang',
    'jiong','qiong','xiong',
    'diao','tiao','niao','liao',
    'dian','tian','nian','lian','liang','niang',
    'gua','kua','hua','zhua','chua','shua',
    'guo','kuo','huo','zhuo','chuo','shuo','ruo',
    'zuo','cuo','suo','duo','tuo','nuo','luo',
    'guai','kuai','huai','zhuai','chuai','shuai',
    'guan','kuan','huan','zhuan','chuan','shuan','ruan',
    'zuan','cuan','suan','duan','tuan','nuan','luan',
    'guang','kuang','huang','zhuang','chuang','shuang',
    'juan','quan','xuan','nuan','luan'
  ]
}

// Build a reverse lookup: pinyin -> category path
const pinyinCategoryMap = new Map()
for (const [category, pinyins] of Object.entries(CATEGORIES)) {
  for (const p of pinyins) {
    pinyinCategoryMap.set(p, category)
  }
}

// ============================================================
//  Audio cache
// ============================================================
const audioCache = new Map()

// ============================================================
//  Core helpers
// ============================================================

/**
 * Strip tone marks from a pinyin string and return the base letters.
 * Also returns the detected tone number (1-4) or 0 for neutral.
 */
export function parseTone(pinyinWithTone) {
  const toneMap = {
    'ā':'a','á':'a','ǎ':'a','à':'a',
    'ō':'o','ó':'o','ǒ':'o','ò':'o',
    'ē':'e','é':'e','ě':'e','è':'e',
    'ī':'i','í':'i','ǐ':'i','ì':'i',
    'ū':'u','ú':'u','ǔ':'u','ù':'u',
    'ǖ':'v','ǘ':'v','ǚ':'v','ǜ':'v'
  }
  const toneNumberMap = {
    'ā':1,'á':2,'ǎ':3,'à':4,
    'ō':1,'ó':2,'ǒ':3,'ò':4,
    'ē':1,'é':2,'ě':3,'è':4,
    'ī':1,'í':2,'ǐ':3,'ì':4,
    'ū':1,'ú':2,'ǔ':3,'ù':4,
    'ǖ':1,'ǘ':2,'ǚ':3,'ǜ':4
  }

  let base = ''
  let tone = 0
  for (const ch of pinyinWithTone) {
    if (toneMap[ch]) {
      base += toneMap[ch]
      tone = toneNumberMap[ch]
    } else {
      base += ch
    }
  }
  // 将 ü 替换为 v（用于文件名）
  base = base.replace(/ü/g, 'v')
  // j, q, x 后面的 u 实际上是 ü，需要转换为 v
  if (/^[jqx]u[eo]/.test(base)) {
    base = base.replace(/^([jqx])u/, '$1v')
  }
  return { base: base.toLowerCase(), tone }
}

/**
 * Build the file path for a given pinyin.
 */
export function getAudioPath(pinyin, tone) {
  const parsed = parseTone(pinyin)
  const base = parsed.base
  const t = tone ?? parsed.tone

  const category = pinyinCategoryMap.get(base)

  // 如果不在分类表中，直接使用 all-pinyin 目录
  if (!category) {
    return `audio/pinyin/all-pinyin/${pinyin}.mp3`
  }

  // Initials have no tone suffix
  if (category === 'initials') {
    return `audio/pinyin/initials/${base}.mp3`
  }

  // 对于不带声调的拼音，使用对应的目录
  if (t === 0) {
    // 不带声调的拼音
    if (category === 'finals/single') {
      return `audio/pinyin/finals/single/${base}.mp3`
    } else if (category === 'finals/compound') {
      return `audio/pinyin/finals/compound/${base}.mp3`
    } else if (category === 'finals/front-nasal') {
      return `audio/pinyin/finals/front-nasal/${base}.mp3`
    } else if (category === 'finals/back-nasal') {
      return `audio/pinyin/finals/back-nasal/${base}.mp3`
    } else if (category === 'whole-syllables') {
      return `audio/pinyin/whole-syllables/${base}.mp3`
    } else if (category === 'triple-pinyin') {
      return `audio/pinyin/triple-pinyin/${base}.mp3`
    }
  }

  // 带声调的拼音
  // 首先尝试 all-pinyin 目录（带声调符号的文件名）
  const allPinyinPath = `audio/pinyin/all-pinyin/${pinyin}.mp3`

  // 如果 all-pinyin 目录中没有，尝试使用数字后缀的格式
  if (category === 'finals/single') {
    return `audio/pinyin/finals/single/${base}${t}.mp3`
  } else if (category === 'finals/compound') {
    return `audio/pinyin/finals/compound/${base}${t}.mp3`
  } else if (category === 'finals/front-nasal') {
    return `audio/pinyin/finals/front-nasal/${base}${t}.mp3`
  } else if (category === 'finals/back-nasal') {
    return `audio/pinyin/finals/back-nasal/${base}${t}.mp3`
  } else if (category === 'whole-syllables') {
    return `audio/pinyin/whole-syllables/${base}${t}.mp3`
  } else if (category === 'triple-pinyin') {
    return `audio/pinyin/triple-pinyin/${base}${t}.mp3`
  }

  // 默认使用 all-pinyin 目录
  return allPinyinPath
}

// ============================================================
//  Playback engine
// ============================================================

// 当前正在播放的音频对象
let currentPlayingAudio = null

/**
 * 停止当前正在播放的音频
 */
export function stopCurrentPlayingAudio() {
  if (currentPlayingAudio) {
    currentPlayingAudio.pause()
    currentPlayingAudio.currentTime = 0
    currentPlayingAudio = null
  }
}

function playAudioFile(src) {
  return new Promise((resolve, reject) => {
    // 先停止之前的音频
    stopCurrentPlayingAudio()

    // 创建新的 Audio 对象
    const audio = new Audio(src)
    currentPlayingAudio = audio

    audio.onended = () => {
      if (currentPlayingAudio === audio) {
        currentPlayingAudio = null
      }
      resolve()
    }
    audio.onerror = (e) => {
      if (currentPlayingAudio === audio) {
        currentPlayingAudio = null
      }
      reject(e)
    }
    audio.play().catch(reject)
  })
}

/**
 * Play a pinyin audio resource.
 * Priority: 1. Local audio file  2. TTS fallback
 */
export async function playPinyinAudio(pinyin, options = {}) {
  const { tone, rate = 0.6, forceTts = false } = options

  if (!forceTts) {
    const path = getAudioPath(pinyin, tone)
    if (path) {
      try {
        await playAudioFile(`/${path}`)
        return
      } catch {
        // File not found -> fall through to TTS
      }
    }
  }

  // TTS fallback
  await speakPinyin(pinyin, rate)
}

// ============================================================
//  Sound effects
// ============================================================
const SFX_BASE = '/audio/sfx/'

export async function playSoundEffect(name) {
  const src = `${SFX_BASE}${name}.mp3`
  try {
    // 音效使用独立的 Audio 对象，不中断当前播放
    const audio = new Audio(src)
    audio.onended = () => {}
    audio.onerror = () => {}
    await audio.play()
  } catch {
    // SFX missing -> silently ignore
  }
}

export function playCorrectSound()   { return playSoundEffect('correct') }
export function playWrongSound()     { return playSoundEffect('wrong') }
export function playClickSound()     { return playSoundEffect('click') }
export function playCompleteSound()  { return playSoundEffect('complete') }

// ============================================================
//  Batch / playlist helpers
// ============================================================

export async function playPinyinSequence(pinyins, options = {}) {
  const { interval = 800, onPlay, signal } = options

  for (let i = 0; i < pinyins.length; i++) {
    if (signal?.aborted) break
    onPlay?.(i, pinyins[i])
    await playPinyinAudio(pinyins[i])
    if (i < pinyins.length - 1) {
      await new Promise(r => setTimeout(r, interval))
    }
  }
}

/**
 * Play blend mode audio: parts played sequentially with no TTS fallback
 * @param {string[]} parts - e.g., ["b", "ái", "bái"] or ["b", "i", "àn", "biàn"]
 * @param {object} options - { signal }
 */
export async function playBlendAudio(parts, options = {}) {
  const { signal } = options

  if (!parts || parts.length === 0) return
  if (signal?.aborted) return

  for (let i = 0; i < parts.length; i++) {
    if (signal?.aborted) return

    const part = parts[i]
    const isLast = i === parts.length - 1

    // 最后一个部分（拼读结果）前加延迟
    if (isLast && parts.length > 1) {
      await new Promise(r => setTimeout(r, 400))
      if (signal?.aborted) return
    }

    // 播放音频文件
    const path = getAudioPath(part)
    if (path) {
      try {
        await playAudioFile(`/${path}`)
      } catch (err) {
        if (err.name === 'AbortError') return
        console.warn(`Audio file not found for: ${part}`)
      }
    } else {
      console.warn(`No audio path for: ${part}`)
    }

    // 每个部分之间的间隔（最后一个不加）
    if (!isLast) {
      await new Promise(r => setTimeout(r, 150))
    }
  }
}

export async function playAllTones(basePinyin) {
  for (let t = 1; t <= 4; t++) {
    await playPinyinAudio(basePinyin, { tone: t })
    if (t < 4) await new Promise(r => setTimeout(r, 600))
  }
}

// ============================================================
//  Preloading
// ============================================================

export async function preloadAudio(pinyins) {
  const loaded = []
  const failed = []

  const tasks = pinyins.map(async (p) => {
    const path = getAudioPath(p)
    if (!path) { failed.push(p); return }
    try {
      const audio = new Audio(`/${path}`)
      await new Promise((resolve, reject) => {
        audio.oncanplaythrough = resolve
        audio.onerror = reject
        audio.load()
      })
      audioCache.set(`/${path}`, audio)
      loaded.push(p)
    } catch {
      failed.push(p)
    }
  })

  await Promise.allSettled(tasks)
  return { loaded, failed }
}

export function hasLocalAudio(pinyin) {
  const path = getAudioPath(pinyin)
  if (!path) return false
  return audioCache.has(`/${path}`)
}

// ============================================================
//  Utility: list all required audio paths
// ============================================================

export function enumerateAllAudioPaths() {
  const result = []
  for (const [category, pinyins] of Object.entries(CATEGORIES)) {
    if (category === 'initials') {
      for (const p of pinyins) {
        result.push({ category, pinyin: p, path: `audio/pinyin/initials/${p}.mp3` })
      }
    } else {
      for (const p of pinyins) {
        for (let t = 1; t <= 4; t++) {
          result.push({
            category,
            pinyin: `${p}${t}`,
            path: `audio/pinyin/${category}/${p}${t}.mp3`
          })
        }
      }
    }
  }
  return result
}
