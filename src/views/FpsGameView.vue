<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useWordStore } from '../stores/wordStore'
import { speakEnglish, speakChinese, isSpeechSupported } from '../utils/audio'
import { playPinyinAudio, playBlendAudio, playCorrectSound, playWrongSound, playClickSound, playCompleteSound, stopCurrentPlayingAudio } from '../utils/audioResourceManager'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const wordStore = useWordStore()

const props = defineProps({
  lang: String,
  listId: String
})

// Game state
const practiceWords = ref([])
const currentWordIndex = ref(0)
const currentWord = ref(null)
const gameStarted = ref(false)
const gameCompleted = ref(false)
const startTime = ref(null)
const elapsedTime = ref(0)
const timerInterval = ref(null)
const wordTimes = ref([])
const totalHits = ref(0)
const totalMisses = ref(0)
const gameArea = ref(null)

// 用于取消当前音频播放
let currentAudioController = null

// Check if current word is pinyin (韵母需要声调)
const isPinyinMode = computed(() => {
  return props.lang === 'zh' && currentWord.value && currentWord.value.unit
})

// Check if current word is a vowel (韵母)
const isVowel = computed(() => {
  if (!currentWord.value) return false
  return currentWord.value.meaning && (
    currentWord.value.meaning.includes('韵母') ||
    currentWord.value.meaning.includes('整体认读')
  )
})

// Get a random toned version for vowels
function getRandomTone(wordData) {
  if (!wordData || !wordData.pinyin) return wordData.word
  const tones = wordData.pinyin.split(' ')
  return tones[Math.floor(Math.random() * tones.length)] || wordData.word
}

// Difficulty settings
const showSettings = ref(false)
const difficulty = ref({
  nextLetter: 30,      // % chance to spawn the next needed letter
  wordLetters: 30,     // % chance to spawn other letters from the word
  decoyLetters: 40     // % chance to spawn decoy letters (not in word)
})
const audioLoopInterval = ref(5) // 音频循环间隔（秒）

// Current word state
const nextLetterIndex = ref(0) // Index of the next letter needed
const activeTargets = ref([])
const popEffects = ref([])
const spawnTimer = ref(null)
const targetIdCounter = ref(0)
const wordStartTime = ref(null) // Track time per word
const wordMisses = ref(0) // Track misses per word

// 组件是否挂载
const isMounted = ref(true)

// 枪械后坐力效果
const isRecoiling = ref(false)

// 鼠标位置追踪
const mouseX = ref(0)
const mouseY = ref(0)

// 计算大炮旋转角度
const gunRotation = computed(() => {
  if (!gameArea.value) return 0

  const rect = gameArea.value.getBoundingClientRect()
  const gameWidth = rect.width
  const gameHeight = rect.height

  // 大炮的位置（底部中间）
  const cannonX = gameWidth / 2
  const cannonY = gameHeight - 60

  // 计算鼠标相对于大炮的位置
  const dx = mouseX.value - cannonX
  const dy = mouseY.value - cannonY

  // 计算角度（弧度转角度）
  // 大炮默认朝上（-90°），所以需要调整
  const angle = Math.atan2(dx, -dy) * (180 / Math.PI)

  // 限制角度范围（-75° 到 75°）
  return Math.max(-75, Math.min(75, angle))
})

// Computed: the next letter we need to click
const nextNeededLetter = computed(() => {
  if (!currentWord.value) return null
  const word = currentWord.value.word
  if (nextLetterIndex.value >= word.length) return null
  // For pinyin mode, return lowercase
  if (isPinyinMode.value) {
    return word[nextLetterIndex.value]
  }
  return word[nextLetterIndex.value].toUpperCase()
})

// Computed: display word showing progress
const displayWord = computed(() => {
  if (!currentWord.value) return ''
  const word = currentWord.value.word

  // For pinyin mode, don't show the answer - only show underscores
  if (isPinyinMode.value) {
    let display = ''
    for (let i = 0; i < word.length; i++) {
      if (i < nextLetterIndex.value) {
        display += word[i] // Already collected
      } else {
        display += '_' // Not yet collected
      }
    }
    return display
  }

  // For English mode, show progress
  let display = ''
  for (let i = 0; i < word.length; i++) {
    if (i < nextLetterIndex.value) {
      display += word[i] // Already collected
    } else {
      display += '_' // Not yet collected
    }
  }
  return display
})

// Check if word is complete
const isWordComplete = computed(() => {
  if (!currentWord.value) return false
  const word = currentWord.value.word.toUpperCase()
  return nextLetterIndex.value >= word.length
})

// Colors for bubbles
const colors = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
  '#22c55e', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6',
  '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
]

const formattedTime = computed(() => {
  const seconds = elapsedTime.value
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

const totalScore = computed(() => {
  if (wordTimes.value.length === 0) return 0

  let score = 0

  for (const word of wordTimes.value) {
    const letterCount = word.letterCount || word.word.length
    const time = word.time || 1
    const misses = word.misses || 0

    // Base score for completing the word: 100 per letter
    let wordScore = letterCount * 100

    // Time bonus: faster = more points (max 50 bonus per letter if under 3 seconds)
    const timePerLetter = time / letterCount
    if (timePerLetter < 3) {
      wordScore += (3 - timePerLetter) * 50 * letterCount
    }

    // Miss penalty: -30 per miss
    wordScore -= misses * 30

    // Efficiency bonus: if hits close to letter count
    // (we don't track per-word hits, so use misses as proxy)
    if (misses === 0) {
      wordScore += letterCount * 50 // Perfect bonus
    }

    score += Math.max(0, wordScore)
  }

  // Normalize to 0-100 range
  const maxPossible = wordTimes.value.reduce((s, w) => s + w.letterCount * 200, 0)
  return Math.round((score / maxPossible) * 100)
})

// Difficulty presets
const difficultyPresets = {
  easy: { nextLetter: 45, wordLetters: 30, decoyLetters: 25 },
  normal: { nextLetter: 30, wordLetters: 30, decoyLetters: 40 },
  hard: { nextLetter: 20, wordLetters: 25, decoyLetters: 55 }
}

function setDifficultyPreset(preset) {
  if (difficultyPresets[preset]) {
    difficulty.value = { ...difficultyPresets[preset] }
  }
}

function updateDifficulty() {
  // Normalize to 100%
  const total = difficulty.value.nextLetter + difficulty.value.wordLetters + difficulty.value.decoyLetters
  if (total > 0) {
    difficulty.value.nextLetter = Math.round((difficulty.value.nextLetter / total) * 100)
    difficulty.value.wordLetters = Math.round((difficulty.value.wordLetters / total) * 100)
    difficulty.value.decoyLetters = 100 - difficulty.value.nextLetter - difficulty.value.wordLetters
  }
}

const rank = computed(() => {
  const score = totalScore.value
  if (score >= 90) return { grade: 'S', color: '#ffd700', label: 'Perfect!' }
  if (score >= 75) return { grade: 'A', color: '#10b981', label: 'Excellent!' }
  if (score >= 60) return { grade: 'B', color: '#3b82f6', label: 'Good!' }
  if (score >= 40) return { grade: 'C', color: '#f59e0b', label: 'Not Bad' }
  return { grade: 'D', color: '#ef4444', label: 'Keep Trying' }
})

// Audio context for sound effects
let audioCtx = null

function initAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
  }
}

function playPopSound() {
  // Try to use local audio file first, fallback to Web Audio API
  playClickSound().catch(() => {
    initAudio()
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.frequency.setValueAtTime(600, audioCtx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(200, audioCtx.currentTime + 0.15)
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15)
    osc.start(audioCtx.currentTime)
    osc.stop(audioCtx.currentTime + 0.15)
  })
}

function playMissSound() {
  // Try to use local audio file first, fallback to Web Audio API
  playWrongSound().catch(() => {
    initAudio()
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.type = 'sawtooth'
    osc.frequency.setValueAtTime(150, audioCtx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(80, audioCtx.currentTime + 0.2)
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.2)
    osc.start(audioCtx.currentTime)
    osc.stop(audioCtx.currentTime + 0.2)
  })
}

function playSuccessSound() {
  // Try to use local audio file first, fallback to Web Audio API
  playCompleteSound().catch(() => {
    initAudio()
    const notes = [523, 659, 784]
    notes.forEach((freq, i) => {
      const osc = audioCtx.createOscillator()
      const gain = audioCtx.createGain()
      osc.connect(gain)
      gain.connect(audioCtx.destination)
      osc.frequency.setValueAtTime(freq, audioCtx.currentTime + i * 0.1)
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime + i * 0.1)
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + i * 0.1 + 0.3)
      osc.start(audioCtx.currentTime + i * 0.1)
      osc.stop(audioCtx.currentTime + i * 0.1 + 0.3)
    })
  })
}

onMounted(async () => {
  await wordStore.loadWordLists(props.lang)
  wordStore.loadCustomLists()
  const list = wordStore.getListById(props.lang, props.listId)

  if (!list) {
    router.push('/')
    return
  }

  const wordsQuery = route.query.words
  if (wordsQuery) {
    const indices = wordsQuery.split(',').map(Number).filter(i =>
      !isNaN(i) && i >= 0 && i < list.words.length
    )
    practiceWords.value = indices.map(i => list.words[i])
  }

  if (practiceWords.value.length === 0) {
    practiceWords.value = [...list.words]
  }
})

onUnmounted(() => {
  isMounted.value = false
  stopTimers()
})

function stopTimers() {
  if (timerInterval.value) clearInterval(timerInterval.value)
  if (spawnTimer.value) clearInterval(spawnTimer.value)
  timerInterval.value = null
  spawnTimer.value = null
  // 停止音频循环
  loopGeneration++
  // 停止当前音频播放
  stopCurrentPlayingAudio()
}

function shuffleArray(array) {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

function startGame() {
  initAudio()

  // Shuffle words before starting
  practiceWords.value = shuffleArray(practiceWords.value)

  gameStarted.value = true
  gameCompleted.value = false
  currentWordIndex.value = 0
  totalHits.value = 0
  totalMisses.value = 0
  wordTimes.value = []
  startTime.value = Date.now()
  elapsedTime.value = 0

  timerInterval.value = setInterval(() => {
    elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)

  loadWord()
}

function restartGame() {
  gameStarted.value = false
  gameCompleted.value = false
  currentWordIndex.value = 0
  elapsedTime.value = 0
  wordTimes.value = []
  totalHits.value = 0
  totalMisses.value = 0
  activeTargets.value = []
  popEffects.value = []
  nextLetterIndex.value = 0
}

function loadWord() {
  currentWord.value = practiceWords.value[currentWordIndex.value]
  nextLetterIndex.value = 0
  activeTargets.value = []
  popEffects.value = []
  wordStartTime.value = Date.now()
  wordMisses.value = 0

  setTimeout(() => {
    // startAudioLoop 内部会播放音频，不需要单独调用 playWordAudio
    startContinuousSpawning()
    startAudioLoop()
  }, 300)
}

let loopGeneration = 0 // 用于区分新旧循环

function startAudioLoop() {
  // 停止旧循环和正在播放的音频
  loopGeneration++
  const myGeneration = loopGeneration
  stopCurrentPlayingAudio()

  // 使用递归方式，等音频播放完成后再开始计时
  async function playNext() {
    // 检查是否是当前循环（防止旧循环继续运行）
    if (loopGeneration !== myGeneration) return
    if (!isMounted.value || isWordComplete.value || !gameStarted.value) return

    // 播放音频并等待完成
    await playWordAudio(true)

    // 再次检查是否是当前循环
    if (loopGeneration !== myGeneration) return
    if (!isMounted.value || isWordComplete.value || !gameStarted.value) return

    // 等待间隔时间
    await new Promise(r => setTimeout(r, audioLoopInterval.value * 1000))

    // 继续播放下一个
    playNext()
  }

  // 开始播放
  playNext()
}

function startContinuousSpawning() {
  // Stop any existing spawn timer
  if (spawnTimer.value) {
    clearInterval(spawnTimer.value)
  }

  // Initial burst of targets
  for (let i = 0; i < 8; i++) {
    setTimeout(() => spawnOneTarget(), i * 200)
  }

  // Continue spawning at regular intervals
  spawnTimer.value = setInterval(() => {
    // Keep 10-15 targets on screen
    if (activeTargets.value.length < 12 && gameStarted.value) {
      spawnOneTarget()
    }
  }, 600) // New target every 600ms
}

function spawnOneTarget() {
  if (!currentWord.value || !gameStarted.value) return

  const word = currentWord.value.word
  const letters = word.split('')

  // For pinyin mode, use lowercase; for English, use uppercase
  const displayLetters = isPinyinMode.value ? letters : letters.map(l => l.toUpperCase())
  const areaWidth = gameArea.value?.offsetWidth || 800
  const areaHeight = gameArea.value?.offsetHeight || 500
  const padding = 60

  // Get the next letter we need
  const nextLetter = nextNeededLetter.value

  // Use difficulty settings for distribution
  const rand = Math.random() * 100
  const nextThreshold = difficulty.value.nextLetter
  const wordThreshold = nextThreshold + difficulty.value.wordLetters

  let letterData

  if (rand < nextThreshold && nextLetter) {
    // Spawn the exact next letter needed
    letterData = { letter: nextLetter, isCorrect: true }
  } else if (rand < wordThreshold) {
    // Spawn a letter from the word, but NOT the next one needed
    const otherLetters = displayLetters.filter((l, i) => i !== nextLetterIndex.value)
    if (otherLetters.length > 0) {
      const letter = otherLetters[Math.floor(Math.random() * otherLetters.length)]
      letterData = { letter, isCorrect: false }
    } else {
      // Fallback to decoy
      if (isPinyinMode.value) {
        // Chinese pinyin decoys
        const pinyinDecoys = ['b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x',
          'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w', 'a', 'o', 'e', 'i', 'u', 'ü',
          'ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 'üe', 'er', 'an', 'en', 'in', 'un', 'ün',
          'ang', 'eng', 'ing', 'ong']
        let decoyLetter
        do {
          decoyLetter = pinyinDecoys[Math.floor(Math.random() * pinyinDecoys.length)]
        } while (displayLetters.includes(decoyLetter))
        letterData = { letter: decoyLetter, isCorrect: false }
      } else {
        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        let decoyLetter
        do {
          decoyLetter = alphabet[Math.floor(Math.random() * 26)]
        } while (displayLetters.includes(decoyLetter))
        letterData = { letter: decoyLetter, isCorrect: false }
      }
    }
  } else {
    // Spawn a decoy (letter NOT in the word)
    if (isPinyinMode.value) {
      // Chinese pinyin decoys
      const pinyinDecoys = ['b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x',
        'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w', 'a', 'o', 'e', 'i', 'u', 'ü',
        'ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 'üe', 'er', 'an', 'en', 'in', 'un', 'ün',
        'ang', 'eng', 'ing', 'ong']
      let decoyLetter
      do {
        decoyLetter = pinyinDecoys[Math.floor(Math.random() * pinyinDecoys.length)]
      } while (displayLetters.includes(decoyLetter))
      letterData = { letter: decoyLetter, isCorrect: false }
    } else {
      const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
      let decoyLetter
      do {
        decoyLetter = alphabet[Math.floor(Math.random() * 26)]
      } while (displayLetters.includes(decoyLetter))
      letterData = { letter: decoyLetter, isCorrect: false }
    }
  }

  // Adjust size for pinyin (longer text needs bigger bubbles)
  const isLongLetter = letterData.letter.length > 2
  const size = isLongLetter ? (70 + Math.random() * 20) : (45 + Math.random() * 35)
  const color = colors[Math.floor(Math.random() * colors.length)]

  // Find non-overlapping position
  let x, y
  let attempts = 0
  const minDistance = size + 15 // Minimum distance between bubbles

  do {
    x = padding + Math.random() * (areaWidth - padding * 2 - size)
    y = padding + Math.random() * (areaHeight - padding * 2 - size)
    attempts++

    // Check distance from all existing targets
    const overlaps = activeTargets.value.some(target => {
      const dx = (x + size / 2) - (target.x + target.size / 2)
      const dy = (y + size / 2) - (target.y + target.size / 2)
      const distance = Math.sqrt(dx * dx + dy * dy)
      return distance < minDistance
    })

    if (!overlaps) break
  } while (attempts < 30) // Max 30 attempts to find position

  const target = {
    id: targetIdCounter.value++,
    letter: letterData.letter,
    isCorrect: letterData.isCorrect,
    x,
    y,
    size,
    color,
    opacity: 0,
    scale: 0,
    lifetime: 5000 + Math.random() * 5000, // Live 5-10 seconds
    born: Date.now()
  }

  activeTargets.value.push(target)

  // Animate in
  requestAnimationFrame(() => {
    const t = activeTargets.value.find(tt => tt.id === target.id)
    if (t) {
      t.opacity = 1
      t.scale = 1
    }
  })

  // Auto remove after lifetime
  setTimeout(() => {
    removeTarget(target.id)
  }, target.lifetime)
}

function removeTarget(id) {
  const index = activeTargets.value.findIndex(t => t.id === id)
  if (index !== -1) {
    activeTargets.value.splice(index, 1)
  }
}

function handleGameAreaClick(event) {
  if (!gameStarted.value) return

  // 触发后坐力效果（不影响音频）
  triggerRecoil()

  const rect = gameArea.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // Check if hit any target
  let hitTarget = null
  for (const target of activeTargets.value) {
    const centerX = target.x + target.size / 2
    const centerY = target.y + target.size / 2
    const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2))
    if (distance < target.size / 2 + 5) {
      hitTarget = target
      break
    }
  }

  if (hitTarget) {
    handleHit(hitTarget)
  } else {
    handleMiss(x, y)
  }

  // 注意：这里不调用 stopCurrentAudio()，让音频循环继续播放
}

// 触发大炮后坐力效果
function triggerRecoil() {
  isRecoiling.value = true
  setTimeout(() => {
    isRecoiling.value = false
  }, 200)
}

function handleHit(target) {
  // Play pop sound
  playPopSound()

  // Add pop effect
  popEffects.value.push({
    id: Date.now() + Math.random(),
    x: target.x + target.size / 2,
    y: target.y + target.size / 2,
    color: target.color,
    size: target.size
  })

  // Remove effect after animation
  setTimeout(() => {
    popEffects.value.shift()
  }, 600)

  // Remove target
  removeTarget(target.id)
  totalHits.value++

  // Check if this is the correct NEXT letter in order
  const word = currentWord.value.word
  const expectedLetter = word[nextLetterIndex.value]

  // For pinyin mode, compare lowercase; for English, compare uppercase
  const hitLetter = isPinyinMode.value ? target.letter : target.letter.toUpperCase()
  const expected = isPinyinMode.value ? expectedLetter : expectedLetter.toUpperCase()

  if (hitLetter === expected) {
    // Correct next letter! Move to next position
    nextLetterIndex.value++

    // Check if word is now complete
    if (isWordComplete.value) {
      wordComplete()
    }
  } else {
    // Wrong letter or wrong order - miss!
    totalMisses.value++
    wordMisses.value++
    playMissSound()
    flashArea('rgba(239, 68, 68, 0.2)')
  }
}

function flashArea(color) {
  const gameAreaEl = gameArea.value
  if (gameAreaEl) {
    gameAreaEl.style.background = color
    setTimeout(() => {
      gameAreaEl.style.background = ''
    }, 200)
  }
}

function handleMiss(x, y) {
  totalMisses.value++
  wordMisses.value++
  playMissSound()

  // Miss effect
  popEffects.value.push({
    id: Date.now() + Math.random(),
    x, y,
    color: '#6b7280',
    size: 20,
    isMiss: true
  })

  setTimeout(() => {
    popEffects.value.shift()
  }, 400)
}

function wordComplete() {
  // Stop spawning and audio loop
  if (spawnTimer.value) {
    clearInterval(spawnTimer.value)
    spawnTimer.value = null
  }
  // 停止音频循环
  loopGeneration++
  stopCurrentPlayingAudio()

  // Play success sound
  playSuccessSound()

  // Record time and misses for this word
  const wordTime = Math.floor((Date.now() - wordStartTime.value) / 1000)
  wordTimes.value.push({
    word: currentWord.value.word,
    time: wordTime,
    misses: wordMisses.value,
    letterCount: currentWord.value.word.length
  })

  // Clear remaining targets
  activeTargets.value = []

  // Auto advance after delay
  setTimeout(() => {
    if (currentWordIndex.value < practiceWords.value.length - 1) {
      currentWordIndex.value++
      loadWord()
    } else {
      gameFinish()
    }
  }, 1500)
}

function gameFinish() {
  elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000)
  gameCompleted.value = true
  gameStarted.value = false
  stopTimers()
}

// 停止当前音频播放
function stopCurrentAudio() {
  if (currentAudioController) {
    currentAudioController.abort()
    currentAudioController = null
  }
  // 同时停止正在播放的音频对象
  stopCurrentPlayingAudio()
}

async function playWordAudio(isFromLoop = false) {
  if (!currentWord.value) return

  // 只有非循环调用时才停止之前的音频
  if (!isFromLoop) {
    stopCurrentAudio()
  }

  // 创建新的 abort controller
  const controller = new AbortController()
  currentAudioController = controller

  try {
    if (props.lang === 'en') {
      await speakEnglish(currentWord.value.word)
    } else if (isPinyinMode.value) {
      // 检查是否有blendParts（拼读模式或整体认读）
      if (currentWord.value.blendParts && currentWord.value.blendParts.length >= 1) {
        // 拼读模式：按顺序播放各个部分
        await playBlendAudio(currentWord.value.blendParts, { signal: controller.signal })
      } else {
        // 普通拼音模式
        const pinyinText = isVowel.value ? getRandomTone(currentWord.value) : currentWord.value.word
        await playPinyinAudio(pinyinText)
      }
    } else {
      await speakChinese(currentWord.value.word)
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      console.error('Speech error:', err)
    }
  } finally {
    if (currentAudioController === controller) {
      currentAudioController = null
    }
  }
}

function handleKeydown(event) {
  if (event.key === ' ') {
    event.preventDefault()
    playWordAudio()
  }
}

function goBackToSelection() {
  // 返回到选择页面，保留之前的选择状态
  router.push(`/select/${props.lang}/${props.listId}`)
}

// 追踪鼠标位置
function handleMouseMove(event) {
  if (!gameArea.value) return
  const rect = gameArea.value.getBoundingClientRect()
  mouseX.value = event.clientX - rect.left
  mouseY.value = event.clientY - rect.top
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('mousemove', handleMouseMove)
})
</script>

<template>
  <div class="fps-game-view">
    <!-- Start Screen -->
    <div v-if="!gameStarted && !gameCompleted" class="start-screen">
      <div class="start-content">
        <h1>🎯 {{ t('game.title') }}</h1>
        <p>{{ t('game.description') }}</p>
        <div class="word-preview">
          <p>{{ t('game.wordCount') }}: <strong>{{ practiceWords.length }}</strong></p>
        </div>

        <div class="start-actions">
          <button class="btn btn-outline" @click="goBackToSelection">
            📋 返回选择
          </button>
        </div>

        <!-- Difficulty Settings -->
        <div class="settings-section">
          <button class="btn btn-outline btn-sm" @click="showSettings = !showSettings">
            ⚙️ {{ t('game.settings') }} {{ showSettings ? '▲' : '▼' }}
          </button>

          <div v-if="showSettings" class="settings-panel">
            <div class="preset-buttons">
              <button class="btn btn-sm" @click="setDifficultyPreset('easy')">
                {{ t('game.easy') }}
              </button>
              <button class="btn btn-sm" @click="setDifficultyPreset('normal')">
                {{ t('game.normal') }}
              </button>
              <button class="btn btn-sm" @click="setDifficultyPreset('hard')">
                {{ t('game.hard') }}
              </button>
            </div>

            <div class="slider-group">
              <label>{{ t('game.nextLetterChance') }}: {{ difficulty.nextLetter }}%</label>
              <input type="range" v-model.number="difficulty.nextLetter" min="5" max="60" @input="updateDifficulty">
            </div>

            <div class="slider-group">
              <label>{{ t('game.wordLetterChance') }}: {{ difficulty.wordLetters }}%</label>
              <input type="range" v-model.number="difficulty.wordLetters" min="5" max="60" @input="updateDifficulty">
            </div>

            <div class="slider-group">
              <label>{{ t('game.decoyChance') }}: {{ difficulty.decoyLetters }}%</label>
              <input type="range" v-model.number="difficulty.decoyLetters" min="5" max="60" @input="updateDifficulty">
            </div>

            <div class="slider-group">
              <label>语音循环间隔: {{ audioLoopInterval }}秒</label>
              <input type="range" v-model.number="audioLoopInterval" min="2" max="10" step="1">
            </div>
          </div>
        </div>

        <button class="btn btn-primary btn-xl" @click="startGame">
          {{ t('game.start') }} 🚀
        </button>
        <button class="btn btn-outline" @click="router.push('/')">
          {{ t('practice.backToList') }}
        </button>
      </div>
    </div>

    <!-- Game Screen -->
    <div v-else-if="gameStarted" class="game-screen">
      <!-- Game Header -->
      <div class="game-header">
        <div class="header-left">
          <span class="word-progress">
            {{ currentWordIndex + 1 }}/{{ practiceWords.length }}
          </span>
          <span class="timer">⏱️ {{ formattedTime }}</span>
        </div>
        <div class="header-center">
          <div class="spelled-word">
            <span
              v-for="(char, index) in displayWord"
              :key="index"
              class="letter"
              :class="{ 'found': char !== '_', 'empty': char === '_' }"
            >{{ char }}</span>
          </div>
          <div class="word-meaning-hint" v-if="currentWord">
            {{ currentWord.meaning }}
          </div>
        </div>
        <div class="header-right">
          <span class="hits">✅ {{ totalHits }}</span>
          <span class="misses">❌ {{ totalMisses }}</span>
          <button class="btn btn-sm btn-outline" @click="playWordAudio">
            🔊
          </button>
        </div>
      </div>

      <!-- Game Area -->
      <div
        ref="gameArea"
        class="game-area"
        @click="handleGameAreaClick"
      >
        <!-- Targets -->
        <div
          v-for="target in activeTargets"
          :key="target.id"
          class="target-bubble"
          :style="{
            left: target.x + 'px',
            top: target.y + 'px',
            width: target.size + 'px',
            height: target.size + 'px',
            backgroundColor: target.color,
            opacity: target.opacity,
            transform: `scale(${target.scale})`,
            fontSize: target.letter.length > 2 ? (target.size * 0.25) + 'px' : (target.size * 0.45) + 'px'
          }"
        >
          {{ target.letter }}
        </div>

        <!-- Pop Effects -->
        <div
          v-for="effect in popEffects"
          :key="effect.id"
          class="pop-effect"
          :class="{ 'miss': effect.isMiss }"
          :style="{
            left: effect.x + 'px',
            top: effect.y + 'px',
            '--color': effect.color
          }"
        >
          <div class="pop-particle" v-for="i in 8" :key="i" :style="{ '--i': i }"></div>
          <span v-if="effect.isMiss" class="miss-x">✕</span>
        </div>

        <!-- 大炮 -->
        <div
          class="cannon-container"
          :class="{ 'recoil': isRecoiling }"
          :style="{
            transform: `rotate(${gunRotation}deg)`,
            '--rotation': `rotate(${gunRotation}deg)`
          }"
        >
          <div class="cannon-body">
            <div class="cannon-barrel"></div>
            <div class="cannon-base"></div>
            <div class="cannon-wheel left"></div>
            <div class="cannon-wheel right"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Screen -->
    <div v-else-if="gameCompleted" class="results-screen">
      <div class="results-content">
        <h1>🏆 {{ t('game.results') }}</h1>

        <div class="rank-badge" :style="{ borderColor: rank.color }">
          <span class="rank-grade" :style="{ color: rank.color }">{{ rank.grade }}</span>
          <span class="rank-label">{{ rank.label }}</span>
        </div>

        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ formattedTime }}</div>
            <div class="stat-label">{{ t('game.totalTime') }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ totalHits }}</div>
            <div class="stat-label">{{ t('game.totalHits') }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ totalMisses }}</div>
            <div class="stat-label">{{ t('game.totalMisses') }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ totalScore }}</div>
            <div class="stat-label">{{ t('game.score') }}</div>
          </div>
        </div>

        <div class="word-results">
          <h3>{{ t('game.wordDetails') }}</h3>
          <div class="word-result-list">
            <div
              v-for="(result, index) in wordTimes"
              :key="index"
              class="word-result-item"
            >
              <span class="result-index">{{ index + 1 }}.</span>
              <span class="result-word">{{ result.word }}</span>
              <span class="result-detail">{{ result.time }}s | {{ result.misses || 0 }}❌</span>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <button class="btn btn-primary btn-lg" @click="restartGame">
            {{ t('game.playAgain') }} 🔄
          </button>
          <button class="btn btn-outline btn-lg" @click="router.push('/')">
            {{ t('practice.backToList') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fps-game-view {
  width: 100%;
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
}

/* Start Screen */
.start-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
}

.start-content {
  text-align: center;
  color: white;
  max-width: 500px;
}

.start-content h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  text-shadow: 0 0 30px rgba(99, 102, 241, 0.6);
}

.start-content p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.word-preview {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: var(--radius-md);
  margin-bottom: 2rem;
}

.start-actions {
  margin-bottom: 2rem;
}

.start-actions .btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.start-actions .btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.settings-section {
  margin-bottom: 2rem;
}

.settings-panel {
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  margin-top: 1rem;
  backdrop-filter: blur(10px);
}

.preset-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.preset-buttons .btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.preset-buttons .btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.slider-group {
  margin-bottom: 1rem;
}

.slider-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
  opacity: 0.9;
}

.slider-group input[type="range"] {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  outline: none;
}

.slider-group input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #6366f1;
  cursor: pointer;
}

.slider-group input[type="range"]::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #6366f1;
  cursor: pointer;
  border: none;
}

.btn-xl {
  padding: 1rem 3rem;
  font-size: 1.3rem;
  margin: 0 1rem;
}

/* Game Screen */
.game-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0a0a1a;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  z-index: 10;
}

.header-left,
.header-right {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.word-progress {
  font-size: 1.1rem;
  font-weight: 700;
  color: #6366f1;
}

.timer {
  font-size: 1.1rem;
  font-family: monospace;
  color: #f59e0b;
}

.hits {
  color: #10b981;
}

.misses {
  color: #ef4444;
}

.header-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.spelled-word {
  display: flex;
  gap: 0.25rem;
  font-size: 1.8rem;
  font-weight: 800;
}

.spelled-word .letter {
  padding: 0.3rem 0.7rem;
  border-radius: 6px;
  min-width: 36px;
  text-align: center;
  transition: all 0.2s;
}

.spelled-word .letter.found {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  animation: popIn 0.2s ease-out;
}

.spelled-word .letter.empty {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.5);
  border: 2px dashed rgba(255, 255, 255, 0.3);
}

@keyframes popIn {
  from { transform: scale(0); }
  to { transform: scale(1); }
}

.cursor {
  color: #6366f1;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.word-meaning-hint {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
}

.game-area {
  flex: 1;
  position: relative;
  background:
    radial-gradient(circle at 20% 30%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.05) 0%, transparent 50%),
    #0a0a1a;
  cursor: crosshair;
  overflow: hidden;
  transition: background 0.2s;
  /* 自定义准星 */
  cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><circle cx="16" cy="16" r="12" fill="none" stroke="white" stroke-width="2"/><line x1="16" y1="4" x2="16" y2="12" stroke="white" stroke-width="2"/><line x1="16" y1="20" x2="16" y2="28" stroke="white" stroke-width="2"/><line x1="4" y1="16" x2="12" y2="16" stroke="white" stroke-width="2"/><line x1="20" y1="16" x2="28" y2="16" stroke="white" stroke-width="2"/><circle cx="16" cy="16" r="2" fill="white"/></svg>') 16 16, crosshair;
}

/* 大炮容器 */
.cannon-container {
  position: absolute;
  bottom: 40px;
  left: 50%;
  z-index: 10;
  pointer-events: none;
  transform-origin: center bottom;
}

/* 后坐力动画 - 使用 margin 避免影响旋转 */
.cannon-container.recoil {
  animation: cannon-recoil 0.2s ease-out;
}

@keyframes cannon-recoil {
  0% {
    margin-bottom: 0;
  }
  20% {
    margin-bottom: 20px;
  }
  100% {
    margin-bottom: 0;
  }
}

/* 大炮主体 */
.cannon-body {
  position: relative;
  width: 60px;
  height: 120px;
}

/* 炮管 */
.cannon-barrel {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 30px;
  height: 90px;
  background: linear-gradient(90deg, #2d3748 0%, #4a5568 30%, #718096 50%, #4a5568 70%, #2d3748 100%);
  border-radius: 8px 8px 5px 5px;
  box-shadow:
    inset 0 -5px 10px rgba(0, 0, 0, 0.3),
    0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 炮口 */
.cannon-barrel::before {
  content: '';
  position: absolute;
  top: -5px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 15px;
  background: linear-gradient(180deg, #718096 0%, #4a5568 100%);
  border-radius: 5px 5px 0 0;
  box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.3);
}

/* 炮口内孔 */
.cannon-barrel::after {
  content: '';
  position: absolute;
  top: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px;
  height: 10px;
  background: #1a202c;
  border-radius: 3px 3px 0 0;
}

/* 炮座 */
.cannon-base {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 30px;
  background: linear-gradient(180deg, #8B4513 0%, #654321 100%);
  border-radius: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 炮座装饰 */
.cannon-base::before {
  content: '';
  position: absolute;
  top: 5px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 5px;
  background: #A0522D;
  border-radius: 2px;
}

/* 轮子 */
.cannon-wheel {
  position: absolute;
  bottom: 5px;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #8B4513 0%, #654321 100%);
  border-radius: 50%;
  border: 3px solid #4a3520;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.cannon-wheel.left {
  left: 0;
}

.cannon-wheel.right {
  right: 0;
}

/* 轮子辐条 */
.cannon-wheel::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  background: #4a3520;
  border-radius: 50%;
}

/* Target Bubbles */
.target-bubble {
  position: absolute;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  cursor: crosshair;
  transition: transform 0.15s ease-out, opacity 0.15s;
  box-shadow:
    0 0 15px rgba(255, 255, 255, 0.2),
    inset 0 -3px 6px rgba(0, 0, 0, 0.2),
    inset 0 3px 6px rgba(255, 255, 255, 0.2);
  user-select: none;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(var(--scale, 1)); }
  50% { transform: translateY(-8px) scale(var(--scale, 1)); }
}

.target-bubble:active {
  transform: scale(0.9) !important;
}

/* Pop Effects */
.pop-effect {
  position: absolute;
  pointer-events: none;
  transform: translate(-50%, -50%);
  z-index: 100;
}

.pop-particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--color);
  border-radius: 50%;
  animation: particle 0.5s ease-out forwards;
  transform: rotate(calc(var(--i) * 45deg)) translateX(20px);
}

@keyframes particle {
  0% {
    opacity: 1;
    transform: rotate(calc(var(--i) * 45deg)) translateX(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: rotate(calc(var(--i) * 45deg)) translateX(40px) scale(0);
  }
}

.miss-x {
  position: absolute;
  font-size: 2rem;
  color: #ef4444;
  font-weight: 900;
  transform: translate(-50%, -50%);
  animation: missFade 0.4s ease-out forwards;
}

@keyframes missFade {
  0% { opacity: 1; transform: translate(-50%, -50%) scale(1.5); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
}

/* Results Screen */
.results-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow-y: auto;
  padding: 2rem;
}

.results-content {
  background: white;
  border-radius: var(--radius-xl);
  padding: 3rem;
  max-width: 600px;
  width: 100%;
  text-align: center;
  box-shadow: var(--shadow-xl);
}

.results-content h1 {
  font-size: 2.5rem;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.rank-badge {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 3rem;
  border: 4px solid;
  border-radius: var(--radius-lg);
  margin: 2rem 0;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
}

.rank-grade {
  font-size: 4rem;
  font-weight: 900;
}

.rank-label {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--gray-600);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin: 2rem 0;
}

.stat-item {
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius-md);
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: var(--primary);
}

.stat-label {
  font-size: 0.85rem;
  color: var(--gray-500);
  margin-top: 0.25rem;
}

.word-results {
  margin: 2rem 0;
  text-align: left;
}

.word-results h3 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: var(--gray-700);
}

.word-result-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.word-result-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--gray-100);
}

.word-result-item:last-child {
  border-bottom: none;
}

.result-index {
  width: 30px;
  color: var(--gray-400);
}

.result-word {
  flex: 1;
  font-weight: 600;
}

.result-time {
  color: var(--primary);
  font-weight: 600;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
}

/* Responsive */
@media (max-width: 768px) {
  .game-header {
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
  }

  .header-left,
  .header-right {
    gap: 1rem;
    font-size: 0.9rem;
  }

  .spelled-word {
    font-size: 1.4rem;
  }

  .spelled-word .letter {
    padding: 0.25rem 0.5rem;
    min-width: 28px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .results-content {
    padding: 2rem;
  }

  .btn-xl {
    padding: 0.875rem 2rem;
    font-size: 1.1rem;
  }
}
</style>
