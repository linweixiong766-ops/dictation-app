<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useWordStore } from '../stores/wordStore'
import { speakEnglish, speakChinese, isSpeechSupported } from '../utils/audio'

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
const letterTargets = ref([])
const spelledWord = ref('')
const gameStarted = ref(false)
const gameCompleted = ref(false)
const isCorrect = ref(null)
const startTime = ref(null)
const endTime = ref(null)
const elapsedTime = ref(0)
const timerInterval = ref(null)
const wordTimes = ref([])
const correctCount = ref(0)
const wrongCount = ref(0)
const gameArea = ref(null)
const crosshairX = ref(0)
const crosshairY = ref(0)
const showMuzzleFlash = ref(false)
const hitEffects = ref([])

// Audio
const hitSound = null
const missSound = null

const formattedTime = computed(() => {
  const seconds = elapsedTime.value
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

const totalScore = computed(() => {
  if (wordTimes.value.length === 0) return 0
  const totalTime = wordTimes.value.reduce((sum, w) => sum + w.time, 0)
  const accuracy = correctCount.value / (correctCount.value + wrongCount.value) || 0
  return Math.round((10000 / totalTime) * accuracy * 100)
})

const rank = computed(() => {
  const score = totalScore.value
  if (score >= 90) return { grade: 'S', color: '#ffd700', label: 'Perfect!' }
  if (score >= 75) return { grade: 'A', color: '#10b981', label: 'Excellent!' }
  if (score >= 60) return { grade: 'B', color: '#3b82f6', label: 'Good!' }
  if (score >= 40) return { grade: 'C', color: '#f59e0b', label: 'Not Bad' }
  return { grade: 'D', color: '#ef4444', label: 'Keep Trying' }
})

onMounted(async () => {
  await wordStore.loadWordLists(props.lang)
  wordStore.loadCustomLists()
  const list = wordStore.getListById(props.lang, props.listId)

  if (!list) {
    router.push('/')
    return
  }

  // Get selected words from URL
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
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
  }
})

function startGame() {
  gameStarted.value = true
  gameCompleted.value = false
  currentWordIndex.value = 0
  correctCount.value = 0
  wrongCount.value = 0
  wordTimes.value = []
  startTime.value = Date.now()
  elapsedTime.value = 0

  // Start timer
  timerInterval.value = setInterval(() => {
    elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)

  loadWord()
}

function loadWord() {
  currentWord.value = practiceWords.value[currentWordIndex.value]
  spelledWord.value = ''
  isCorrect.value = null
  generateTargets()

  // Play word audio
  setTimeout(() => {
    playWordAudio()
  }, 500)
}

function generateTargets() {
  if (!currentWord.value) return

  const word = currentWord.value.word.toUpperCase()
  const letters = word.split('')
  const targets = []
  const padding = 60

  // Get game area dimensions
  const areaWidth = gameArea.value?.offsetWidth || 800
  const areaHeight = gameArea.value?.offsetHeight || 500

  // Generate random positions for each letter
  const positions = []
  for (let i = 0; i < letters.length; i++) {
    let pos
    let attempts = 0
    do {
      pos = {
        x: padding + Math.random() * (areaWidth - padding * 2),
        y: padding + Math.random() * (areaHeight - padding * 2)
      }
      attempts++
    } while (attempts < 50 && positions.some(p =>
      Math.abs(p.x - pos.x) < 60 && Math.abs(p.y - pos.y) < 60
    ))
    positions.push(pos)

    targets.push({
      id: i,
      letter: letters[i],
      x: pos.x,
      y: pos.y,
      hit: false,
      scale: 1,
      rotation: Math.random() * 30 - 15,
      animationDelay: i * 0.1
    })
  }

  // Add some decoy letters
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const decoyCount = Math.min(5, Math.max(3, Math.floor(letters.length * 0.5)))
  for (let i = 0; i < decoyCount; i++) {
    let decoyLetter
    do {
      decoyLetter = alphabet[Math.floor(Math.random() * 26)]
    } while (letters.includes(decoyLetter))

    let pos
    let attempts = 0
    do {
      pos = {
        x: padding + Math.random() * (areaWidth - padding * 2),
        y: padding + Math.random() * (areaHeight - padding * 2)
      }
      attempts++
    } while (attempts < 50 && positions.some(p =>
      Math.abs(p.x - pos.x) < 60 && Math.abs(p.y - pos.y) < 60
    ))
    positions.push(pos)

    targets.push({
      id: `decoy-${i}`,
      letter: decoyLetter,
      x: pos.x,
      y: pos.y,
      hit: false,
      isDecoy: true,
      scale: 1,
      rotation: Math.random() * 30 - 15,
      animationDelay: (letters.length + i) * 0.1
    })
  }

  letterTargets.value = targets
}

function playWordAudio() {
  if (!currentWord.value) return
  try {
    if (props.lang === 'en') {
      speakEnglish(currentWord.value.word)
    } else {
      speakChinese(currentWord.value.word)
    }
  } catch (err) {
    console.error('Speech error:', err)
  }
}

function handleGameAreaClick(event) {
  if (!gameStarted.value || isCorrect.value !== null) return

  const rect = gameArea.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // Update crosshair position
  crosshairX.value = x
  crosshairY.value = y

  // Show muzzle flash
  showMuzzleFlash.value = true
  setTimeout(() => {
    showMuzzleFlash.value = false
  }, 100)

  // Check if hit any target
  let hitTarget = null
  for (const target of letterTargets.value) {
    if (target.hit) continue
    const distance = Math.sqrt(
      Math.pow(x - target.x, 2) + Math.pow(y - target.y, 2)
    )
    if (distance < 35) {
      hitTarget = target
      break
    }
  }

  if (hitTarget) {
    handleHit(hitTarget)
  } else {
    handleMiss(x, y)
  }
}

function handleHit(target) {
  target.hit = true
  target.scale = 0

  // Add hit effect
  hitEffects.value.push({
    id: Date.now(),
    x: target.x,
    y: target.y,
    type: 'hit'
  })

  setTimeout(() => {
    hitEffects.value = hitEffects.value.filter(e => e.id !== Date.now())
  }, 500)

  if (target.isDecoy) {
    // Hit a decoy - wrong!
    wrongCount.value++
    spelledWord.value = ''
    // Reset all targets
    setTimeout(() => {
      generateTargets()
      playWordAudio()
    }, 500)
  } else {
    // Correct letter
    spelledWord.value += target.letter

    // Check if word is complete
    const targetWord = currentWord.value.word.toUpperCase()
    if (spelledWord.value === targetWord) {
      // Word complete!
      isCorrect.value = true
      correctCount.value++
      const wordTime = Math.floor((Date.now() - startTime.value) / 1000) - wordTimes.value.reduce((s, w) => s + w.time, 0)
      wordTimes.value.push({
        word: currentWord.value.word,
        time: wordTime
      })
    }
  }
}

function handleMiss(x, y) {
  // Add miss effect
  hitEffects.value.push({
    id: Date.now(),
    x,
    y,
    type: 'miss'
  })

  setTimeout(() => {
    hitEffects.value = hitEffects.value.filter(e => e.id !== Date.now())
  }, 300)
}

function confirmWord() {
  if (isCorrect.value !== true) return

  if (currentWordIndex.value < practiceWords.value.length - 1) {
    // Next word
    currentWordIndex.value++
    loadWord()
  } else {
    // Game complete
    endTime.value = Date.now()
    elapsedTime.value = Math.floor((endTime.value - startTime.value) / 1000)
    gameCompleted.value = true
    if (timerInterval.value) {
      clearInterval(timerInterval.value)
    }
  }
}

function retryWord() {
  wrongCount.value++
  spelledWord.value = ''
  isCorrect.value = null
  generateTargets()
  playWordAudio()
}

function handleKeydown(event) {
  if (event.key === 'Enter' && isCorrect.value === true) {
    confirmWord()
  } else if (event.key === 'r' || event.key === 'R') {
    if (isCorrect.value === false) {
      retryWord()
    }
  } else if (event.key === ' ') {
    event.preventDefault()
    playWordAudio()
  }
}

function restartGame() {
  gameStarted.value = false
  gameCompleted.value = false
  currentWordIndex.value = 0
  elapsedTime.value = 0
  wordTimes.value = []
  correctCount.value = 0
  wrongCount.value = 0
}

// Listen for keyboard events
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
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
        <button class="btn btn-primary btn-xl" @click="startGame">
          {{ t('game.start') }} 🚀
        </button>
        <button class="btn btn-outline" @click="router.push('/')">
          {{ t('practice.backToList') }}
        </button>
      </div>
    </div>

    <!-- Game Screen -->
    <div v-else-if="gameStarted && !gameCompleted" class="game-screen">
      <!-- Game Header -->
      <div class="game-header">
        <div class="header-left">
          <span class="word-progress">
            {{ t('practice.wordOf', { current: currentWordIndex + 1, total: practiceWords.length }) }}
          </span>
          <span class="timer">⏱️ {{ formattedTime }}</span>
        </div>
        <div class="header-center">
          <div class="spelled-word">
            <span v-for="(letter, index) in spelledWord" :key="index" class="letter">
              {{ letter }}
            </span>
            <span class="cursor">|</span>
          </div>
        </div>
        <div class="header-right">
          <button class="btn btn-sm btn-outline" @click="playWordAudio">
            🔊 {{ t('game.replay') }}
          </button>
        </div>
      </div>

      <!-- Game Area -->
      <div
        ref="gameArea"
        class="game-area"
        @click="handleGameAreaClick"
      >
        <!-- Crosshair -->
        <div
          class="crosshair"
          :style="{ left: crosshairX + 'px', top: crosshairY + 'px' }"
        >
          +
        </div>

        <!-- Muzzle Flash -->
        <div v-if="showMuzzleFlash" class="muzzle-flash">💥</div>

        <!-- Letter Targets -->
        <div
          v-for="target in letterTargets"
          :key="target.id"
          class="letter-target"
          :class="{
            'hit': target.hit,
            'decoy': target.isDecoy,
            'hidden': target.hit
          }"
          :style="{
            left: target.x + 'px',
            top: target.y + 'px',
            transform: `rotate(${target.rotation}deg) scale(${target.scale})`,
            animationDelay: target.animationDelay + 's'
          }"
        >
          {{ target.letter }}
        </div>

        <!-- Hit Effects -->
        <div
          v-for="effect in hitEffects"
          :key="effect.id"
          class="hit-effect"
          :class="effect.type"
          :style="{ left: effect.x + 'px', top: effect.y + 'px' }"
        >
          {{ effect.type === 'hit' ? '💥' : '💨' }}
        </div>

        <!-- Word Meaning -->
        <div class="word-hint" v-if="currentWord">
          {{ currentWord.meaning }}
        </div>
      </div>

      <!-- Word Complete Overlay -->
      <div v-if="isCorrect === true" class="word-complete-overlay">
        <div class="word-complete-content">
          <h2>✅ {{ t('game.correct') }}</h2>
          <div class="completed-word">{{ currentWord.word }}</div>
          <p>{{ currentWord.meaning }}</p>
          <button class="btn btn-primary btn-lg" @click="confirmWord">
            {{ currentWordIndex < practiceWords.length - 1 ? t('game.nextWord') : t('game.finish') }} →
          </button>
        </div>
      </div>

      <!-- Wrong Answer Overlay -->
      <div v-if="isCorrect === false" class="wrong-overlay">
        <div class="wrong-content">
          <h2>❌ {{ t('game.wrong') }}</h2>
          <p>{{ t('game.tryAgain') }}</p>
          <button class="btn btn-primary btn-lg" @click="retryWord">
            {{ t('game.retry') }} 🔄
          </button>
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
            <div class="stat-value">{{ correctCount }}</div>
            <div class="stat-label">{{ t('game.correctWords') }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ wrongCount }}</div>
            <div class="stat-label">{{ t('game.wrongAttempts') }}</div>
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
              <span class="result-time">{{ result.time }}s</span>
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
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.start-content {
  text-align: center;
  color: white;
  max-width: 500px;
}

.start-content h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  text-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
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
  position: relative;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  z-index: 10;
}

.header-left {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.word-progress {
  font-size: 1.1rem;
  font-weight: 600;
}

.timer {
  font-size: 1.2rem;
  font-family: monospace;
  color: #f59e0b;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.spelled-word {
  display: flex;
  gap: 0.5rem;
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: 4px;
}

.spelled-word .letter {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  animation: popIn 0.3s ease-out;
}

@keyframes popIn {
  from { transform: scale(0); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.cursor {
  animation: blink 1s infinite;
  color: #6366f1;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.game-area {
  flex: 1;
  position: relative;
  background:
    radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
    linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 100%);
  cursor: crosshair;
  overflow: hidden;
}

.crosshair {
  position: absolute;
  font-size: 2rem;
  color: rgba(255, 255, 255, 0.8);
  pointer-events: none;
  transform: translate(-50%, -50%);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
  z-index: 100;
}

.muzzle-flash {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 3rem;
  z-index: 100;
  animation: flash 0.1s ease-out;
}

@keyframes flash {
  from { opacity: 1; transform: translateX(-50%) scale(1.5); }
  to { opacity: 0; transform: translateX(-50%) scale(1); }
}

.letter-target {
  position: absolute;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 800;
  color: white;
  background: radial-gradient(circle, #ef4444 0%, #dc2626 50%, #b91c1c 100%);
  border-radius: 50%;
  cursor: pointer;
  transform-origin: center;
  animation: floatIn 0.5s ease-out forwards;
  box-shadow:
    0 0 20px rgba(239, 68, 68, 0.5),
    0 0 40px rgba(239, 68, 68, 0.3),
    inset 0 -4px 8px rgba(0, 0, 0, 0.3);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  user-select: none;
}

.letter-target.decoy {
  background: radial-gradient(circle, #6b7280 0%, #4b5563 50%, #374151 100%);
  box-shadow:
    0 0 15px rgba(107, 114, 128, 0.4),
    0 0 30px rgba(107, 114, 128, 0.2),
    inset 0 -4px 8px rgba(0, 0, 0, 0.3);
}

.letter-target.hit {
  animation: hit 0.3s ease-out forwards;
}

.letter-target.hidden {
  display: none;
}

@keyframes floatIn {
  from {
    opacity: 0;
    transform: scale(0) rotate(180deg);
  }
  to {
    opacity: 1;
    transform: scale(1) rotate(var(--rotation, 0deg));
  }
}

@keyframes hit {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.5);
    opacity: 0.5;
  }
  100% {
    transform: scale(0);
    opacity: 0;
  }
}

.letter-target:hover {
  transform: scale(1.1);
  box-shadow:
    0 0 30px rgba(239, 68, 68, 0.7),
    0 0 60px rgba(239, 68, 68, 0.4),
    inset 0 -4px 8px rgba(0, 0, 0, 0.3);
}

.hit-effect {
  position: absolute;
  font-size: 2rem;
  pointer-events: none;
  transform: translate(-50%, -50%);
  animation: effectFade 0.5s ease-out forwards;
}

.hit-effect.hit {
  color: #10b981;
}

.hit-effect.miss {
  color: #6b7280;
}

@keyframes effectFade {
  from {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.5);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.5);
  }
}

.word-hint {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 1rem 2rem;
  border-radius: var(--radius-lg);
  font-size: 1.2rem;
  backdrop-filter: blur(10px);
}

/* Overlays */
.word-complete-overlay,
.wrong-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease-out;
}

.word-complete-overlay {
  background: rgba(16, 185, 129, 0.9);
}

.wrong-overlay {
  background: rgba(239, 68, 68, 0.9);
}

.word-complete-content,
.wrong-content {
  text-align: center;
  color: white;
  padding: 3rem;
}

.word-complete-content h2,
.wrong-content h2 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.completed-word {
  font-size: 3rem;
  font-weight: 800;
  margin: 1rem 0;
  letter-spacing: 4px;
}

.word-complete-content p,
.wrong-content p {
  font-size: 1.3rem;
  margin-bottom: 2rem;
  opacity: 0.9;
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

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive */
@media (max-width: 768px) {
  .game-header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .header-left {
    gap: 1rem;
  }

  .spelled-word {
    font-size: 1.5rem;
  }

  .spelled-word .letter {
    padding: 0.4rem 0.8rem;
  }

  .letter-target {
    width: 50px;
    height: 50px;
    font-size: 1.5rem;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .results-content {
    padding: 2rem;
  }

  .rank-grade {
    font-size: 3rem;
  }

  .btn-xl {
    padding: 0.875rem 2rem;
    font-size: 1.1rem;
  }
}
</style>
