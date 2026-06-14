<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useWordStore } from '../stores/wordStore'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const wordStore = useWordStore()

const props = defineProps({
  lang: String,
  listId: String
})

const currentList = ref(null)
const selectedWords = ref([])
const searchQuery = ref('')
const selectAll = ref(false)

const filteredWords = computed(() => {
  if (!currentList.value) return []
  if (!searchQuery.value.trim()) return currentList.value.words
  const query = searchQuery.value.trim().toLowerCase()
  return currentList.value.words.filter(w =>
    w.word.toLowerCase().includes(query) ||
    w.meaning.toLowerCase().includes(query)
  )
})

const selectedCount = computed(() => selectedWords.value.length)

const isIndeterminate = computed(() => {
  if (!currentList.value) return false
  return selectedWords.value.length > 0 && selectedWords.value.length < currentList.value.words.length
})

onMounted(async () => {
  await wordStore.loadWordLists(props.lang)
  wordStore.loadCustomLists()
  currentList.value = wordStore.getListById(props.lang, props.listId)

  if (!currentList.value) {
    router.push('/')
    return
  }

  // 默认全选
  selectedWords.value = currentList.value.words.map((w, i) => i)
})

function toggleWord(index) {
  const pos = selectedWords.value.indexOf(index)
  if (pos === -1) {
    selectedWords.value.push(index)
  } else {
    selectedWords.value.splice(pos, 1)
  }
  selectAll.value = selectedWords.value.length === currentList.value.words.length
}

function toggleSelectAll() {
  if (selectAll.value) {
    selectedWords.value = []
    selectAll.value = false
  } else {
    selectedWords.value = currentList.value.words.map((_, i) => i)
    selectAll.value = true
  }
}

function startPractice() {
  if (selectedWords.value.length === 0) return

  // 将选中的单词索引传递给练习页面
  const wordIndices = selectedWords.value.join(',')
  router.push(`/practice/${props.lang}/${props.listId}?words=${wordIndices}`)
}

function startGroupPractice() {
  if (selectedWords.value.length === 0) return

  // 将选中的单词索引传递给多人听写页面
  const wordIndices = selectedWords.value.join(',')
  router.push(`/group/${props.lang}/${props.listId}?words=${wordIndices}`)
}

function startGame() {
  if (selectedWords.value.length === 0) return

  // 将选中的单词索引传递给游戏页面
  const wordIndices = selectedWords.value.join(',')
  router.push(`/game/${props.lang}/${props.listId}?words=${wordIndices}`)
}
</script>

<template>
  <div class="word-select-view" v-if="currentList">
    <div class="select-header">
      <div class="header-left">
        <button class="btn btn-outline btn-sm" @click="router.push('/')">
          ← {{ t('practice.backToList') }}
        </button>
        <h1>{{ currentList.name }}</h1>
      </div>
      <div class="header-stats">
        <span class="selected-badge">
          {{ t('practice.selected') }}: {{ selectedCount }} / {{ currentList.words.length }}
        </span>
      </div>
    </div>

    <!-- 搜索和全选 -->
    <div class="toolbar">
      <div class="search-box">
        <input
          v-model="searchQuery"
          class="input"
          :placeholder="t('practice.searchWords')"
        />
      </div>
      <div class="toolbar-actions">
        <label class="select-all-label">
          <input
            type="checkbox"
            :checked="selectAll"
            :indeterminate="isIndeterminate"
            @change="toggleSelectAll"
          />
          {{ t('practice.selectAll') }}
        </label>
        <button
          class="btn btn-primary"
          :disabled="selectedCount === 0"
          @click="startPractice"
        >
          {{ t('practice.singlePractice') }} ({{ selectedCount }})
        </button>
        <button
          class="btn btn-secondary"
          :disabled="selectedCount === 0"
          @click="startGroupPractice"
        >
          {{ t('practice.groupPractice') }} ({{ selectedCount }})
        </button>
        <button
          class="btn btn-game"
          :disabled="selectedCount === 0"
          @click="startGame"
        >
          🎯 {{ t('practice.playGame') }} ({{ selectedCount }})
        </button>
      </div>
    </div>

    <!-- 单词列表 -->
    <div class="word-grid">
      <div
        v-for="(word, idx) in filteredWords"
        :key="word.word"
        class="word-item"
        :class="{ 'selected': selectedWords.includes(currentList.words.indexOf(word)) }"
        @click="toggleWord(currentList.words.indexOf(word))"
      >
        <div class="word-checkbox">
          <input
            type="checkbox"
            :checked="selectedWords.includes(currentList.words.indexOf(word))"
            @click.stop
            @change="toggleWord(currentList.words.indexOf(word))"
          />
        </div>
        <div class="word-content">
          <div class="word-text">{{ word.word }}</div>
          <div class="word-meaning">{{ word.meaning }}</div>
          <div v-if="word.phonetic || word.pinyin" class="word-phonetic">
            {{ word.phonetic || word.pinyin }}
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-bar">
      <div class="selected-info">
        {{ t('practice.selectedWords') }}: <strong>{{ selectedCount }}</strong>
      </div>
      <div class="bottom-actions">
        <button
          class="btn btn-primary btn-lg"
          :disabled="selectedCount === 0"
          @click="startPractice"
        >
          {{ t('practice.singlePractice') }} →
        </button>
        <button
          class="btn btn-secondary btn-lg"
          :disabled="selectedCount === 0"
          @click="startGroupPractice"
        >
          {{ t('practice.groupPractice') }} →
        </button>
        <button
          class="btn btn-game btn-lg"
          :disabled="selectedCount === 0"
          @click="startGame"
        >
          🎯 {{ t('practice.playGame') }} →
        </button>
      </div>
    </div>
  </div>

  <div v-else class="card">
    <p>{{ t('common.loading') }}</p>
  </div>
</template>

<style scoped>
.word-select-view {
  max-width: 900px;
  margin: 0 auto;
  padding-bottom: 80px;
}

.select-header {
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

.selected-badge {
  background: var(--primary);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-weight: 500;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 200px;
}

.search-box .input {
  width: 100%;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.select-all-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 500;
}

.word-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}

.word-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition);
}

.word-item:hover {
  border-color: var(--primary-light);
  background: rgba(99, 102, 241, 0.05);
}

.word-item.selected {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
}

.word-checkbox {
  padding-top: 2px;
}

.word-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.word-content {
  flex: 1;
}

.word-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--gray-800);
}

.word-meaning {
  font-size: 0.9rem;
  color: var(--gray-600);
  margin-top: 0.25rem;
}

.word-phonetic {
  font-size: 0.8rem;
  color: var(--gray-500);
  margin-top: 0.25rem;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.selected-info {
  font-size: 1.1rem;
  color: var(--gray-700);
}

.bottom-actions {
  display: flex;
  gap: 1rem;
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

.btn-game:active {
  transform: translateY(0);
}

@media (max-width: 640px) {
  .word-grid {
    grid-template-columns: 1fr;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-actions {
    justify-content: space-between;
  }
}
</style>
