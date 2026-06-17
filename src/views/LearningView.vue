<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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

const currentList = ref(null)
const practiceWords = ref([])
const currentIndex = ref(0)
const isPlaying = ref(false)
const autoPlayTimer = ref(null)
const playInterval = ref(3000) // 3秒间隔
const showPhonetic = ref(true)
const showMeaning = ref(true)
const loopCount = ref(1) // 循环次数 (1-10, 或 0 表示无限循环)
const currentLoop = ref(0) // 当前循环次数
const completed = ref(false) // 是否完成所有循环

const currentWord = computed(() => {
  if (!practiceWords.value.length) return null
  return practiceWords.value[currentIndex.value]
})

const progress = computed(() => {
  if (!practiceWords.value.length) return 0
  return ((currentIndex.value + 1) / practiceWords.value.length) * 100
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
  stopAutoPlay()
})

function playCurrentWord() {
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

function startAutoPlay() {
  if (!practiceWords.value.length) return

  isPlaying.value = true
  completed.value = false
  currentLoop.value = 1
  playCurrentWord()

  autoPlayTimer.value = setInterval(() => {
    // Move to next word
    if (currentIndex.value < practiceWords.value.length - 1) {
      currentIndex.value++
    } else {
      // Completed one loop
      if (loopCount.value === 0) {
        // Infinite loop - restart
        currentIndex.value = 0
      } else if (currentLoop.value < loopCount.value) {
        // More loops to go
        currentLoop.value++
        currentIndex.value = 0
      } else {
        // All loops completed
        stopAutoPlay()
        completed.value = true
        return
      }
    }

    // Play the word
    setTimeout(() => {
      playCurrentWord()
    }, 500)
  }, playInterval.value)
}

function stopAutoPlay() {
  isPlaying.value = false
  if (autoPlayTimer.value) {
    clearInterval(autoPlayTimer.value)
    autoPlayTimer.value = null
  }
  // Stop speech
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel()
  }
}

function togglePlay() {
  if (isPlaying.value) {
    stopAutoPlay()
  } else {
    startAutoPlay()
  }
}

function previousWord() {
  stopAutoPlay()
  if (currentIndex.value > 0) {
    currentIndex.value--
  } else {
    currentIndex.value = practiceWords.value.length - 1
  }
}

function nextWord() {
  stopAutoPlay()
  if (currentIndex.value < practiceWords.value.length - 1) {
    currentIndex.value++
  } else {
    currentIndex.value = 0
  }
}

function restartLearning() {
  currentIndex.value = 0
  currentLoop.value = 0
  completed.value = false
  isPlaying.value = false
  stopAutoPlay()
}

function finishLearning() {
  stopAutoPlay()
  completed.value = true
}

function getWordIndices() {
  // Get the original indices of the practice words in the word list
  const list = wordStore.getListById(props.lang, props.listId)
  if (!list) return ''
  return practiceWords.value.map(w => list.words.findIndex(wl => wl.word === w.word)).join(',')
}

function goToPractice() {
  const wordIndices = getWordIndices()
  router.push(`/practice/${props.lang}/${props.listId}?words=${wordIndices}`)
}

function goToGroupPractice() {
  const wordIndices = getWordIndices()
  router.push(`/group/${props.lang}/${props.listId}?words=${wordIndices}`)
}

function goToGame() {
  const wordIndices = getWordIndices()
  router.push(`/game/${props.lang}/${props.listId}?words=${wordIndices}`)
}

function handleKeydown(event) {
  switch (event.key) {
    case ' ':
      event.preventDefault()
      togglePlay()
      break
    case 'ArrowLeft':
      previousWord()
      break
    case 'ArrowRight':
      nextWord()
      break
    case 'p':
      playCurrentWord()
      break
  }
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
  <div class="learning-view" v-if="practiceWords.length">
    <div class="learning-header">
      <div class="header-left">
        <button class="btn btn-outline btn-sm" @click="router.push('/')">
          ← {{ t('practice.backToList') }}
        </button>
        <h1>{{ t('learning.title') }}</h1>
      </div>
      <div class="header-right">
        <span class="word-count">
          {{ currentIndex + 1 }} / {{ practiceWords.length }}
        </span>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progress + '%' }"></div>
    </div>

    <!-- Settings -->
    <div class="settings-card card">
      <div class="settings-row">
        <div class="setting-item">
          <label>{{ t('learning.interval') }}</label>
          <select v-model="playInterval" class="input-select" :disabled="isPlaying">
            <option :value="2000">2 {{ t('practice.seconds') }}</option>
            <option :value="3000">3 {{ t('practice.seconds') }}</option>
            <option :value="5000">5 {{ t('practice.seconds') }}</option>
            <option :value="8000">8 {{ t('practice.seconds') }}</option>
          </select>
        </div>
        <div class="setting-item">
          <label>{{ t('learning.loopCount') }}</label>
          <select v-model="loopCount" class="input-select" :disabled="isPlaying">
            <option :value="1">1 {{ t('learning.times') }}</option>
            <option :value="2">2 {{ t('learning.times') }}</option>
            <option :value="3">3 {{ t('learning.times') }}</option>
            <option :value="5">5 {{ t('learning.times') }}</option>
            <option :value="0">{{ t('learning.infinite') }}</option>
          </select>
        </div>
        <!-- Loop progress -->
        <div class="setting-item" v-if="isPlaying && loopCount > 0">
          <span class="loop-progress">
            {{ t('learning.loopProgress') }}: {{ currentLoop }} / {{ loopCount }}
          </span>
        </div>
        <!-- Chinese mode: show pinyin toggle -->
        <div class="setting-item" v-if="lang === 'zh'">
          <label class="checkbox-label">
            <input type="checkbox" v-model="showPhonetic">
            {{ t('learning.showPinyin') }}
          </label>
        </div>
        <!-- English mode: show phonetic toggle -->
        <div class="setting-item" v-if="lang === 'en'">
          <label class="checkbox-label">
            <input type="checkbox" v-model="showPhonetic">
            {{ t('learning.showPhonetic') }}
          </label>
        </div>
        <!-- English mode: show meaning toggle -->
        <div class="setting-item" v-if="lang === 'en'">
          <label class="checkbox-label">
            <input type="checkbox" v-model="showMeaning">
            {{ t('learning.showMeaning') }}
          </label>
        </div>
      </div>
    </div>

    <!-- Word Display - Chinese Mode -->
    <div v-if="lang === 'zh'" class="word-display-card card">
      <!-- Chinese Word -->
      <div class="word-main" v-if="currentWord">
        <div class="word-text">{{ currentWord.word }}</div>
      </div>

      <!-- Pinyin -->
      <div v-if="showPhonetic && currentWord && currentWord.pinyin" class="phonetic-display">
        {{ currentWord.pinyin }}
      </div>

      <!-- Play Button -->
      <button class="btn btn-play" @click="playCurrentWord" :disabled="!isSpeechSupported()">
        🔊 {{ t('learning.playAudio') }}
      </button>
    </div>

    <!-- Word Display - English Mode -->
    <div v-else class="word-display-card card">
      <!-- English Word -->
      <div class="word-main" v-if="currentWord">
        <div class="word-text">{{ currentWord.word }}</div>
      </div>

      <!-- Phonetic -->
      <div v-if="showPhonetic && currentWord && currentWord.phonetic" class="phonetic-display">
        {{ currentWord.phonetic }}
      </div>

      <!-- Chinese Meaning -->
      <div v-if="showMeaning && currentWord" class="meaning-display">
        {{ currentWord.meaning }}
      </div>

      <!-- Play Button -->
      <button class="btn btn-play" @click="playCurrentWord" :disabled="!isSpeechSupported()">
        🔊 {{ t('learning.playAudio') }}
      </button>
    </div>

    <!-- Controls -->
    <div class="controls-card card">
      <div class="controls-main">
        <button class="btn btn-control" @click="previousWord" :title="t('practice.previous') + ' (←)'">
          ⏮ {{ t('practice.previous') }}
        </button>

        <button
          class="btn btn-play-control"
          :class="{ 'playing': isPlaying }"
          @click="togglePlay"
        >
          {{ isPlaying ? '⏸ ' + t('practice.pause') : '▶ ' + t('learning.autoPlay') }}
        </button>

        <button class="btn btn-control" @click="nextWord" :title="t('practice.next') + ' (→)'">
          {{ t('practice.next') }} ⏭
        </button>

        <button class="btn btn-complete" @click="finishLearning">
          ✅ {{ t('learning.finishLearning') }}
        </button>
      </div>

      <div class="shortcuts-hint">
        <p>{{ t('practice.shortcuts') }}: <kbd>Space</kbd> {{ t('learning.autoPlay') }} | <kbd>←</kbd> {{ t('practice.previous') }} | <kbd>→</kbd> {{ t('practice.next') }} | <kbd>P</kbd> {{ t('learning.playAudio') }}</p>
      </div>
    </div>

    <!-- Completed Screen -->
    <div v-if="completed" class="completed-card card">
      <h2>🎉 {{ t('learning.completed') }}</h2>
      <p>{{ t('learning.completedMessage') }}</p>
      <div class="completed-actions">
        <button class="btn btn-learn" @click="restartLearning">
          🔄 {{ t('learning.restart') }}
        </button>
        <button class="btn btn-primary" @click="goToPractice">
          ✏️ {{ t('practice.singlePractice') }}
        </button>
        <button class="btn btn-secondary" @click="goToGroupPractice">
          👥 {{ t('practice.groupPractice') }}
        </button>
        <button class="btn btn-game" @click="goToGame">
          🎯 {{ t('practice.playGame') }}
        </button>
      </div>
    </div>
  </div>

  <div v-else class="card">
    <p>{{ t('common.loading') }}</p>
  </div>
</template>

<style scoped>
.learning-view {
  max-width: 800px;
  margin: 0 auto;
}

.learning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left h1 {
  margin: 0;
  font-size: 1.5rem;
}

.word-count {
  background: var(--primary);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-weight: 600;
}

.settings-card {
  margin-bottom: 1.5rem;
}

.settings-row {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  align-items: center;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.setting-item label {
  font-weight: 500;
  color: var(--gray-700);
  white-space: nowrap;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.input-select {
  padding: 0.5rem 1rem;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-md);
  background: white;
  font-size: 1rem;
  cursor: pointer;
  transition: var(--transition);
}

.input-select:focus {
  outline: none;
  border-color: var(--primary);
}

.word-display-card {
  text-align: center;
  padding: 3rem 2rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.word-main {
  margin-bottom: 1.5rem;
}

.word-text {
  font-size: 3.5rem;
  font-weight: 700;
  letter-spacing: 4px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.phonetic-display {
  font-size: 1.5rem;
  opacity: 0.9;
  margin-bottom: 1rem;
  font-style: italic;
}

.meaning-display {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  background: rgba(255, 255, 255, 0.2);
  display: inline-block;
  padding: 0.5rem 2rem;
  border-radius: var(--radius-md);
}

.btn-play {
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-size: 1.1rem;
  padding: 0.75rem 2rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition);
}

.btn-play:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-play:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.controls-card {
  margin-bottom: 1.5rem;
}

.controls-main {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.btn-control {
  min-width: 120px;
  font-size: 1rem;
  padding: 0.75rem 1.5rem;
}

.btn-play-control {
  min-width: 160px;
  font-size: 1.1rem;
  padding: 0.75rem 2rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition);
}

.btn-play-control:hover {
  background: var(--primary-dark);
}

.btn-play-control.playing {
  background: #ef4444;
}

.shortcuts-hint {
  text-align: center;
  color: var(--gray-500);
  font-size: 0.9rem;
}

.shortcuts-hint kbd {
  background: var(--gray-100);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--gray-300);
  font-family: monospace;
  font-size: 0.85rem;
}

.loop-progress {
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-light);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
}

.completed-card {
  text-align: center;
  padding: 3rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  margin-top: 2rem;
}

.completed-card h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.completed-card p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.completed-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.completed-actions .btn {
  min-width: 140px;
}

.btn-learn {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  color: white;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.4);
}

.btn-learn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.5);
}

.btn-game {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
}

.btn-game:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.5);
}

.btn-complete {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.4);
  min-width: 120px;
}

.btn-complete:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
}

.btn-complete:active {
  transform: translateY(0);
}

@media (max-width: 640px) {
  .word-text {
    font-size: 2.5rem;
  }

  .phonetic-display {
    font-size: 1.2rem;
  }

  .meaning-display {
    font-size: 1.4rem;
  }

  .controls-main {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-control,
  .btn-play-control {
    min-width: auto;
  }

  .settings-row {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
