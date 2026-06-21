<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useWordStore } from '../stores/wordStore'
import { speakEnglish, speakChinese, isSpeechSupported } from '../utils/audio'
import { playPinyinAudio, playBlendAudio, stopCurrentPlayingAudio } from '../utils/audioResourceManager'

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
const showAnswer = ref(false)
const autoPlayTimer = ref(null)
const playInterval = ref(3000) // 3秒间隔
const repeatCount = ref(1) // 重复次数
const currentRepeat = ref(0)

// 用于取消当前音频播放
let currentAudioController = null

const currentWord = computed(() => {
  if (!practiceWords.value.length) return null
  return practiceWords.value[currentIndex.value]
})

// Check if current word is pinyin (has unit field)
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

const progress = computed(() => {
  if (!practiceWords.value.length) return 0
  return ((currentIndex.value + 1) / practiceWords.value.length) * 100
})

onMounted(async () => {
  await loadList()
})

onUnmounted(() => {
  stopAutoPlay()
})

async function loadList() {
  await wordStore.loadWordLists(props.lang)
  wordStore.loadCustomLists()
  currentList.value = wordStore.getListById(props.lang, props.listId)

  if (!currentList.value) {
    router.push('/')
    return
  }

  // 解析URL中的选中单词索引
  const wordsQuery = route.query.words
  if (wordsQuery) {
    const indices = wordsQuery.split(',').map(Number).filter(i =>
      !isNaN(i) && i >= 0 && i < currentList.value.words.length
    )
    practiceWords.value = indices.map(i => currentList.value.words[i])
  }

  // 如果没有选中单词，使用全部单词
  if (practiceWords.value.length === 0) {
    practiceWords.value = [...currentList.value.words]
  }
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

async function playCurrentWord() {
  if (!currentWord.value) return

  // 先停止之前的音频
  stopCurrentAudio()

  // 创建新的 abort controller
  const controller = new AbortController()
  currentAudioController = controller

  try {
    if (props.lang === 'en') {
      await speakEnglish(currentWord.value.word)
    } else if (isPinyinMode.value) {
      // 检查是否有blendParts（拼读模式）
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

// 用户点击播放按钮时调用
async function handlePlayButtonClick() {
  // 停止自动播放
  const wasPlaying = isPlaying.value
  if (wasPlaying) {
    isPlaying.value = false
    if (autoPlayTimer.value) {
      clearInterval(autoPlayTimer.value)
      autoPlayTimer.value = null
    }
  }

  // 重置重复计数
  currentRepeat.value = 0

  // 播放当前单词
  await playCurrentWord()

  // 如果之前在自动播放，重新开始
  if (wasPlaying) {
    startAutoPlay()
  }
}

async function startAutoPlay() {
  if (!practiceWords.value.length) return

  isPlaying.value = true
  currentRepeat.value = 0

  // 使用递归方式，等音频播放完成后再开始计时
  async function playNext() {
    if (!isPlaying.value) return

    // 播放当前单词并等待完成
    await playCurrentWord()

    // 如果停止了，直接返回
    if (!isPlaying.value) return

    // 等待间隔时间
    await new Promise(r => setTimeout(r, playInterval.value))

    // 如果停止了，直接返回
    if (!isPlaying.value) return

    currentRepeat.value++

    if (currentRepeat.value >= repeatCount.value) {
      // 移动到下一个单词
      currentRepeat.value = 0
      if (currentIndex.value < practiceWords.value.length - 1) {
        currentIndex.value++
        showAnswer.value = false
      } else {
        // 循环回到开头
        currentIndex.value = 0
        showAnswer.value = false
      }
    }

    // 继续播放下一个
    playNext()
  }

  // 开始播放
  playNext()
}

function stopAutoPlay() {
  isPlaying.value = false
  if (autoPlayTimer.value) {
    clearInterval(autoPlayTimer.value)
    autoPlayTimer.value = null
  }
  // 停止当前音频播放
  stopCurrentAudio()
  // 停止语音
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
    showAnswer.value = false
  } else {
    currentIndex.value = practiceWords.value.length - 1
    showAnswer.value = false
  }
}

function nextWord() {
  stopAutoPlay()
  if (currentIndex.value < practiceWords.value.length - 1) {
    currentIndex.value++
    showAnswer.value = false
  } else {
    currentIndex.value = 0
    showAnswer.value = false
  }
}

function shuffleWords() {
  stopAutoPlay()
  const shuffled = [...practiceWords.value]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  practiceWords.value = shuffled
  currentIndex.value = 0
  showAnswer.value = false
}

function toggleAnswer() {
  showAnswer.value = !showAnswer.value
  // 显示答案时自动暂停播放
  if (showAnswer.value && isPlaying.value) {
    stopAutoPlay()
  }
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
    case 'Enter':
      toggleAnswer()
      break
  }
}

function goBackToSelection() {
  // 返回到选择页面，保留之前的选择状态
  router.push(`/select/${props.lang}/${props.listId}`)
}

// 监听键盘事件
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="group-practice-view" v-if="practiceWords.length">
    <div class="practice-header">
      <div class="header-left">
        <button class="btn btn-outline btn-sm" @click="goBackToSelection">
          📋 返回选择
        </button>
        <button class="btn btn-outline btn-sm" @click="router.push('/')">
          ← {{ t('practice.backToList') }}
        </button>
        <h1>{{ t('practice.groupMode') }}</h1>
      </div>
      <div class="header-right">
        <span class="word-count">
          {{ currentIndex + 1 }} / {{ practiceWords.length }}
        </span>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progress + '%' }"></div>
    </div>

    <!-- 设置区域 -->
    <div class="settings-card card">
      <div class="settings-row">
        <div class="setting-item">
          <label>{{ t('practice.playInterval') }}</label>
          <select v-model="playInterval" class="input-select" :disabled="isPlaying">
            <option :value="2000">2 {{ t('practice.seconds') }}</option>
            <option :value="3000">3 {{ t('practice.seconds') }}</option>
            <option :value="5000">5 {{ t('practice.seconds') }}</option>
            <option :value="8000">8 {{ t('practice.seconds') }}</option>
            <option :value="10000">10 {{ t('practice.seconds') }}</option>
          </select>
        </div>
        <div class="setting-item">
          <label>{{ t('practice.repeatCount') }}</label>
          <select v-model="repeatCount" class="input-select" :disabled="isPlaying">
            <option :value="1">1x</option>
            <option :value="2">2x</option>
            <option :value="3">3x</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 单词显示区域 -->
    <div class="word-display-card card">
      <div class="word-number">
        {{ t('practice.wordOf', { current: currentIndex + 1, total: practiceWords.length }) }}
      </div>

      <!-- 中文模式: 显示拼音 (拼音词库不显示，避免泄露答案) -->
      <div class="word-main" v-if="currentWord && lang === 'zh'">
        <div class="meaning-display" v-if="!isPinyinMode">{{ currentWord.pinyin }}</div>
        <div class="meaning-display pinyin-hint" v-else>🎧 请听读音</div>
      </div>

      <!-- 英文模式: 显示中文释义 -->
      <div class="word-main" v-if="currentWord && lang === 'en'">
        <div class="meaning-display">{{ currentWord.meaning }}</div>
        <div v-if="currentWord.phonetic" class="phonetic-hint">
          {{ currentWord.phonetic }}
        </div>
      </div>

      <!-- 听写提示 (未显示答案时) -->
      <div v-if="!showAnswer" class="dictation-hint">
        {{ t('practice.listenAndWrite') }}
      </div>
    </div>

    <!-- 完整答案表 (模态框) -->
    <div v-if="showAnswer" class="answer-sheet-overlay" @click.self="showAnswer = false">
      <div class="answer-sheet card">
        <div class="answer-sheet-header">
          <h2>{{ t('practice.answerSheet') }}</h2>
          <button class="btn btn-outline btn-sm" @click="showAnswer = false">
            ✕ {{ t('common.close') }}
          </button>
        </div>
        <div class="answer-list">
          <!-- 中文模式答案表 -->
          <div v-if="lang === 'zh'">
            <div
              v-for="(word, index) in practiceWords"
              :key="index"
              class="answer-item"
              :class="{ 'current': index === currentIndex }"
            >
              <span class="answer-number">{{ index + 1 }}.</span>
              <span class="answer-pinyin" v-if="!word.unit">{{ word.pinyin }}</span>
              <span class="answer-word">{{ word.word }}</span>
              <span class="answer-meaning" v-if="word.unit">{{ word.meaning }}</span>
            </div>
          </div>
          <!-- 英文模式答案表 -->
          <div v-else>
            <div
              v-for="(word, index) in practiceWords"
              :key="index"
              class="answer-item"
              :class="{ 'current': index === currentIndex }"
            >
              <span class="answer-number">{{ index + 1 }}.</span>
              <span class="answer-meaning">{{ word.meaning }}</span>
              <span class="answer-word">{{ word.word }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 控制按钮 -->
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
          {{ isPlaying ? '⏸ ' + t('practice.pause') : '▶ ' + t('practice.play') }}
        </button>

        <button class="btn btn-control" @click="nextWord" :title="t('practice.next') + ' (→)'">
          {{ t('practice.next') }} ⏭
        </button>
      </div>

      <div class="controls-secondary">
        <button class="btn btn-outline" @click="shuffleWords">
          🔀 {{ t('practice.shuffle') }}
        </button>

        <button class="btn btn-outline" @click="toggleAnswer">
          {{ showAnswer ? '🙈 ' + t('practice.hideAnswer') : '👀 ' + t('practice.showAnswer') }}
        </button>

        <button class="btn btn-outline" @click="handlePlayButtonClick" :disabled="!isSpeechSupported()">
          🔊 {{ t('practice.playAudio') }}
        </button>
      </div>
    </div>

    <!-- 快捷键提示 -->
    <div class="shortcuts-hint">
      <p>{{ t('practice.shortcuts') }}: <kbd>Space</kbd> {{ t('practice.playPause') }} | <kbd>←</kbd> {{ t('practice.previous') }} | <kbd>→</kbd> {{ t('practice.next') }} | <kbd>Enter</kbd> {{ t('practice.showAnswer') }}</p>
    </div>
  </div>

  <div v-else class="card">
    <p>{{ t('common.loading') }}</p>
  </div>
</template>

<style scoped>
.group-practice-view {
  max-width: 900px;
  width: 85%;
  margin: 0 auto;
}

.practice-header {
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

.word-number {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-bottom: 1rem;
}

.word-main {
  margin: 2rem 0;
}

.meaning-display {
  font-size: 2.5rem;
  font-weight: 700;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
  margin-bottom: 1rem;
}

.phonetic-hint {
  font-size: 1.2rem;
  opacity: 0.85;
  font-style: italic;
}

.pinyin-hint {
  font-size: 2rem;
  opacity: 0.9;
}

.answer-section {
  background: rgba(255, 255, 255, 0.25);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  margin-top: 1.5rem;
  animation: fadeIn 0.3s ease-out;
}

.word-answer {
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: 3px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.dictation-hint {
  margin-top: 1.5rem;
  font-size: 1.1rem;
  opacity: 0.8;
  font-style: italic;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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

.controls-secondary {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
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

/* Answer Sheet Modal */
.answer-sheet-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
  animation: fadeIn 0.3s ease-out;
}

.answer-sheet {
  background: white;
  border-radius: var(--radius-lg);
  max-width: 800px;
  width: 90%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.answer-sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 2px solid var(--border);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.answer-sheet-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.answer-sheet-header .btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.answer-sheet-header .btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.answer-list {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.answer-item {
  display: grid;
  grid-template-columns: 50px 1fr auto;
  gap: 1.5rem;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-md);
  transition: var(--transition);
  align-items: center;
  border-bottom: 1px solid var(--gray-100);
}

.answer-item:last-child {
  border-bottom: none;
}

.answer-item:hover {
  background: var(--primary-light);
}

.answer-item.current {
  background: rgba(99, 102, 241, 0.15);
  border-left: 4px solid var(--primary);
  font-weight: 600;
}

.answer-number {
  font-weight: 800;
  color: var(--primary);
  font-size: 1.25rem;
}

.answer-meaning {
  font-size: 1.25rem;
  color: var(--gray-700);
}

.answer-pinyin {
  font-size: 1.25rem;
  color: var(--primary);
  font-style: italic;
}

.answer-word {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gray-900);
  letter-spacing: 2px;
}

@media (max-width: 640px) {
  .word-text {
    font-size: 2.5rem;
  }

  .controls-main {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-control,
  .btn-play-control {
    min-width: auto;
  }

  .controls-secondary {
    flex-direction: column;
    align-items: stretch;
  }

  .settings-row {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
