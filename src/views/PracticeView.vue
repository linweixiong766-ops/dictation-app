<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useWordStore } from '../stores/wordStore'
import { speakEnglish, speakChinese, isSpeechSupported } from '../utils/audio'
import { playPinyinAudio, playBlendAudio, stopCurrentPlayingAudio } from '../utils/audioResourceManager'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const wordStore = useWordStore()

const props = defineProps({
  lang: String,
  listId: String
})

const currentList = ref(null)
const selectedIndices = ref([])
const practiceWords = ref([])
const currentIndex = ref(0)
const userInput = ref('')
const showResult = ref(false)
const isCorrect = ref(false)
const showAnswerFlag = ref(false)
const showMeaningFlag = ref(false)
const score = ref(0)
const completed = ref(false)
const answers = ref([])

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

const accuracy = computed(() => {
  if (answers.value.length === 0) return 0
  const correct = answers.value.filter(a => a.correct).length
  return Math.round((correct / answers.value.length) * 100)
})

onMounted(async () => {
  await loadList()
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
    selectedIndices.value = wordsQuery.split(',').map(Number).filter(i =>
      !isNaN(i) && i >= 0 && i < currentList.value.words.length
    )
  }

  // 如果没有选中单词或索引无效，使用全部单词
  if (selectedIndices.value.length === 0) {
    practiceWords.value = [...currentList.value.words]
  } else {
    practiceWords.value = selectedIndices.value.map(i => currentList.value.words[i])
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

async function playAudio() {
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
      if (currentWord.value.blendParts && currentWord.value.blendParts.length > 1) {
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

function checkAnswer() {
  if (!currentWord.value || !userInput.value.trim()) return

  showResult.value = true
  const userAnswer = userInput.value.trim().toLowerCase()
  const correctAnswer = currentWord.value.word.toLowerCase()
  isCorrect.value = userAnswer === correctAnswer

  if (isCorrect.value) {
    score.value++
  }

  answers.value.push({
    word: currentWord.value.word,
    userAnswer: userInput.value.trim(),
    correct: isCorrect.value
  })
}

function nextWord() {
  stopCurrentAudio()
  if (currentIndex.value < practiceWords.value.length - 1) {
    currentIndex.value++
    userInput.value = ''
    showResult.value = false
    showAnswerFlag.value = false
    showMeaningFlag.value = false
  } else {
    completed.value = true
  }
}

function previousWord() {
  stopCurrentAudio()
  if (currentIndex.value > 0) {
    currentIndex.value--
    userInput.value = ''
    showResult.value = false
    showAnswerFlag.value = false
    showMeaningFlag.value = false
  }
}

function toggleAnswer() {
  showAnswerFlag.value = !showAnswerFlag.value
}

function toggleMeaning() {
  showMeaningFlag.value = !showMeaningFlag.value
}

function tryAgain() {
  currentIndex.value = 0
  userInput.value = ''
  showResult.value = false
  showAnswerFlag.value = false
  showMeaningFlag.value = false
  score.value = 0
  completed.value = false
  answers.value = []
}

function handleKeydown(event) {
  if (event.key === 'Enter') {
    if (!showResult.value) {
      checkAnswer()
    } else {
      nextWord()
    }
  }
}

function goBackToSelection() {
  // 返回到选择页面，保留之前的选择状态
  router.push(`/select/${props.lang}/${props.listId}`)
}
</script>

<template>
  <div class="practice-view" v-if="currentList">
    <div class="practice-header">
      <h1>{{ t('practice.title') }}</h1>
      <div class="header-actions">
        <button class="btn btn-outline btn-sm" @click="goBackToSelection">
          📋 返回选择
        </button>
        <button class="btn btn-outline btn-sm" @click="router.push('/')">
          {{ t('practice.backToList') }}
        </button>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progress + '%' }"></div>
    </div>

    <!-- Completed Screen -->
    <div v-if="completed" class="card score-card">
      <h2>{{ t('practice.complete') }}</h2>
      <div class="score-number">{{ score }}/{{ practiceWords.length }}</div>
      <div class="score-label">{{ t('practice.accuracy') }}: {{ accuracy }}%</div>
      <div class="actions">
        <button class="btn btn-primary btn-lg" @click="tryAgain">
          {{ t('practice.tryAgain') }}
        </button>
        <button class="btn btn-outline btn-lg" @click="router.push('/')">
          {{ t('practice.backToList') }}
        </button>
      </div>
    </div>

    <!-- Practice Area -->
    <div v-else>
      <div class="word-display">
        <div class="word-number">
          {{ t('practice.wordOf', { current: currentIndex + 1, total: practiceWords.length }) }}
        </div>

        <!-- Play Button -->
        <button class="btn btn-primary btn-play" @click="playAudio" :disabled="!isSpeechSupported()">
          🔊
        </button>

        <!-- Chinese mode: show pinyin as hint -->
        <div v-if="lang === 'zh' && showMeaningFlag && currentWord && currentWord.pinyin" class="word-phonetic">
          {{ currentWord.pinyin }}
        </div>

        <!-- English mode: show meaning as hint -->
        <div v-if="lang === 'en' && showMeaningFlag && currentWord" class="word-meaning">
          {{ currentWord.meaning }}
        </div>

        <!-- Answer: show phonetic/pinyin -->
        <div v-if="showAnswerFlag && currentWord" class="word-phonetic">
          {{ currentWord.phonetic || currentWord.pinyin }}
        </div>

        <!-- Answer -->
        <div v-if="showAnswerFlag && currentWord" class="word-meaning" style="font-size: 1.5rem; font-weight: bold;">
          {{ currentWord.word }}
        </div>
      </div>

      <!-- Input Area -->
      <div class="input-area">
        <input
          v-model="userInput"
          class="input input-large"
          :placeholder="t('practice.inputPlaceholder')"
          @keydown="handleKeydown"
          :disabled="showResult"
          autofocus
        />
      </div>

      <!-- Result Message -->
      <div v-if="showResult" class="result-message" :class="isCorrect ? 'result-correct' : 'result-incorrect'">
        {{ isCorrect ? t('practice.correct') : t('practice.incorrect') }}
        <span v-if="!isCorrect && currentWord">
          ({{ currentWord.word }})
        </span>
      </div>

      <!-- Action Buttons -->
      <div class="actions">
        <button
          v-if="!showResult"
          class="btn btn-primary btn-lg"
          @click="checkAnswer"
          :disabled="!userInput.trim()"
        >
          {{ t('practice.check') }}
        </button>

        <template v-else>
          <button class="btn btn-primary btn-lg" @click="nextWord">
            {{ currentIndex < practiceWords.length - 1 ? t('practice.next') : t('practice.complete') }}
          </button>
        </template>

        <button class="btn btn-outline" @click="toggleMeaning">
          {{ showMeaningFlag ? t('practice.hideMeaning') : t('practice.showMeaning') }}
        </button>

        <button class="btn btn-outline" @click="toggleAnswer">
          {{ showAnswerFlag ? t('practice.hideAnswer') : t('practice.showAnswer') }}
        </button>
      </div>
    </div>
  </div>

  <div v-else class="card">
    <p>{{ t('common.loading') }}</p>
  </div>
</template>

<style scoped>
.practice-view {
  max-width: 600px;
  margin: 0 auto;
}

.practice-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
}

.practice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.word-display {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border-radius: var(--radius-lg);
  padding: 2rem;
  margin-bottom: 2rem;
}

.btn-play {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
  }
  50% {
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.6);
  }
}

.btn-play:hover {
  animation: none;
}

.input-area .input-large {
  font-size: 1.5rem;
  letter-spacing: 2px;
}

.score-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.score-card .actions .btn {
  min-width: 140px;
}
</style>
