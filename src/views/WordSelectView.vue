<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
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
const selectedUnits = ref([]) // 改为多选
const showUnitPanel = ref(false) // 控制单元选择面板显示
const expandedGroups = ref([]) // 控制分组展开/折叠

// Get available units from word list
const availableUnits = computed(() => {
  if (!currentList.value) return []
  const units = new Set()
  currentList.value.words.forEach(w => {
    if (w.unit) units.add(w.unit)
  })
  return Array.from(units)
})

const hasUnits = computed(() => availableUnits.value.length > 0)

// 按单元分组的单词（支持搜索过滤）
const wordsByUnit = computed(() => {
  if (!currentList.value) return {}
  const groups = {}
  const query = searchQuery.value.trim().toLowerCase()

  currentList.value.words.forEach((w, index) => {
    // 搜索过滤（支持搜索单词、释义、拼音）
    if (query &&
        !w.word.toLowerCase().includes(query) &&
        !w.meaning.toLowerCase().includes(query) &&
        !(w.pinyin && w.pinyin.toLowerCase().includes(query))) {
      return
    }

    const unit = w.unit || '未分类'
    if (!groups[unit]) groups[unit] = []
    groups[unit].push({ ...w, originalIndex: index })
  })
  return groups
})

const filteredWords = computed(() => {
  if (!currentList.value) return []
  let words = currentList.value.words

  // Filter by selected units
  if (selectedUnits.value.length > 0) {
    words = words.filter(w => selectedUnits.value.includes(w.unit))
  }

  // Filter by search query（支持搜索单词、释义、拼音）
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.trim().toLowerCase()
    words = words.filter(w =>
      w.word.toLowerCase().includes(query) ||
      w.meaning.toLowerCase().includes(query) ||
      (w.pinyin && w.pinyin.toLowerCase().includes(query))
    )
  }

  return words
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

  // 尝试恢复之前的选择状态
  const lastSelection = wordStore.restoreSelection()
  if (lastSelection && lastSelection.lang === props.lang && lastSelection.listId === props.listId) {
    // 恢复之前的选择
    selectedWords.value = lastSelection.indices.filter(i => i < currentList.value.words.length)
  } else {
    // 默认全选
    selectedWords.value = currentList.value.words.map((w, i) => i)
  }
  // 默认展开所有单元
  expandedGroups.value = [...availableUnits.value]
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
    // Select all filtered words (get their original indices)
    selectedWords.value = filteredWords.value.map(w =>
      currentList.value.words.indexOf(w)
    )
    selectAll.value = true
  }
}

function onUnitChange() {
  // 不重置选择状态，让用户手动管理
  // 只更新全选状态
  const visibleWords = filteredWords.value
  const visibleIndices = visibleWords.map(w => currentList.value.words.indexOf(w))
  const allSelected = visibleIndices.every(i => selectedWords.value.includes(i))
  selectAll.value = allSelected
}

function toggleUnit(unit) {
  const index = selectedUnits.value.indexOf(unit)
  if (index === -1) {
    selectedUnits.value.push(unit)
    // 展开选中的单元
    if (!expandedGroups.value.includes(unit)) {
      expandedGroups.value.push(unit)
    }
  } else {
    selectedUnits.value.splice(index, 1)
  }
  // 延迟更新选择状态，避免频繁重渲染
  nextTick(() => onUnitChange())
}

function selectAllUnits() {
  selectedUnits.value = [...availableUnits.value]
  // 展开所有单元
  expandedGroups.value = [...availableUnits.value]
  nextTick(() => onUnitChange())
}

function clearAllUnits() {
  selectedUnits.value = []
  nextTick(() => onUnitChange())
}

function toggleGroup(unit) {
  const index = expandedGroups.value.indexOf(unit)
  if (index === -1) {
    expandedGroups.value.push(unit)
  } else {
    expandedGroups.value.splice(index, 1)
  }
}

function startPractice() {
  if (selectedWords.value.length === 0) return

  // 保存选择状态
  wordStore.saveSelection(props.lang, props.listId, selectedWords.value)

  // 将选中的单词索引传递给练习页面
  const wordIndices = selectedWords.value.join(',')
  router.push(`/practice/${props.lang}/${props.listId}?words=${wordIndices}`)
}

function startGroupPractice() {
  if (selectedWords.value.length === 0) return

  // 保存选择状态
  wordStore.saveSelection(props.lang, props.listId, selectedWords.value)

  // 将选中的单词索引传递给多人听写页面
  const wordIndices = selectedWords.value.join(',')
  router.push(`/group/${props.lang}/${props.listId}?words=${wordIndices}`)
}

function startGame() {
  if (selectedWords.value.length === 0) return

  // 保存选择状态
  wordStore.saveSelection(props.lang, props.listId, selectedWords.value)

  // 将选中的单词索引传递给游戏页面
  const wordIndices = selectedWords.value.join(',')
  router.push(`/game/${props.lang}/${props.listId}?words=${wordIndices}`)
}

function startLearning() {
  if (selectedWords.value.length === 0) return

  // 保存选择状态
  wordStore.saveSelection(props.lang, props.listId, selectedWords.value)

  // 将选中的单词索引传递给学习页面
  const wordIndices = selectedWords.value.join(',')
  router.push(`/learn/${props.lang}/${props.listId}?words=${wordIndices}`)
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
      <div class="unit-filter" v-if="hasUnits">
        <button class="btn btn-outline btn-sm" @click="showUnitPanel = !showUnitPanel">
          📚 选择单元 {{ selectedUnits.length > 0 ? `(${selectedUnits.length})` : '' }}
        </button>
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
          class="btn btn-learn"
          :disabled="selectedCount === 0"
          @click="startLearning"
        >
          📖 {{ t('practice.learningMode') }} ({{ selectedCount }})
        </button>
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

    <!-- 单元选择面板 -->
    <div v-if="showUnitPanel && hasUnits" class="unit-panel">
      <div class="unit-panel-header">
        <h3>选择练习单元</h3>
        <div class="unit-panel-actions">
          <button class="btn btn-sm btn-outline" @click="selectAllUnits">全选</button>
          <button class="btn btn-sm btn-outline" @click="clearAllUnits">清除</button>
          <button class="btn btn-sm" @click="showUnitPanel = false">关闭</button>
        </div>
      </div>
      <div class="unit-grid">
        <div
          v-for="unit in availableUnits"
          :key="unit"
          class="unit-item"
          :class="{ 'selected': selectedUnits.includes(unit) }"
          @click="toggleUnit(unit)"
        >
          <input
            type="checkbox"
            :checked="selectedUnits.includes(unit)"
            @click.stop
          />
          <span class="unit-name">{{ unit }}</span>
          <span class="unit-count">{{ wordsByUnit[unit]?.length || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- 单词列表 - 按单元分组显示 -->
    <div class="word-groups">
      <div
        v-for="(words, unit) in wordsByUnit"
        :key="unit"
        class="word-group"
        v-show="selectedUnits.length === 0 || selectedUnits.includes(unit)"
      >
        <div class="group-header" @click="toggleGroup(unit)">
          <span class="group-title">{{ unit }}</span>
          <span class="group-count">{{ words.length }} 个</span>
          <span class="group-toggle">{{ expandedGroups.includes(unit) ? '▼' : '▶' }}</span>
        </div>
        <div v-show="expandedGroups.includes(unit)" class="group-content">
          <div class="word-grid">
            <div
              v-for="word in words"
              :key="word.originalIndex"
              class="word-item"
              :class="{ 'selected': selectedWords.includes(word.originalIndex) }"
              @click="toggleWord(word.originalIndex)"
            >
              <div class="word-checkbox">
                <input
                  type="checkbox"
                  :checked="selectedWords.includes(word.originalIndex)"
                  @click.stop
                  @change="toggleWord(word.originalIndex)"
                />
              </div>
              <div class="word-content">
                <div class="word-text">{{ word.word }}</div>
                <!-- Chinese mode: only show pinyin -->
                <div v-if="lang === 'zh' && word.pinyin" class="word-phonetic">
                  {{ word.pinyin }}
                </div>
                <!-- English mode: show meaning and phonetic -->
                <div v-if="lang === 'en'" class="word-meaning">{{ word.meaning }}</div>
                <div v-if="lang === 'en' && word.phonetic" class="word-phonetic">
                  {{ word.phonetic }}
                </div>
              </div>
            </div>
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

.unit-filter {
  min-width: 150px;
}

.input-select {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 1rem;
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  transition: var(--transition);
}

.input-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
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

.unit-panel {
  background: white;
  border: 2px solid var(--primary);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

.unit-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.unit-panel-header h3 {
  margin: 0;
  color: var(--gray-800);
}

.unit-panel-actions {
  display: flex;
  gap: 0.5rem;
}

.unit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}

.unit-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--gray-50);
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition);
}

.unit-item:hover {
  border-color: var(--primary-light);
  background: rgba(99, 102, 241, 0.05);
}

.unit-item.selected {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
}

.unit-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.unit-name {
  flex: 1;
  font-weight: 500;
  color: var(--gray-700);
}

.unit-count {
  font-size: 0.85rem;
  color: var(--gray-500);
  background: var(--gray-200);
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
}

.word-groups {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.word-group {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: var(--gray-50);
  cursor: pointer;
  transition: var(--transition);
  user-select: none;
}

.group-header:hover {
  background: var(--gray-100);
}

.group-title {
  flex: 1;
  font-weight: 600;
  color: var(--gray-800);
  font-size: 1.1rem;
}

.group-count {
  font-size: 0.9rem;
  color: var(--gray-500);
}

.group-toggle {
  color: var(--gray-400);
  font-size: 0.8rem;
}

.group-content {
  padding: 1rem;
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

.btn-learn {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  color: white;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.4);
}

.btn-learn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.5);
}

.btn-learn:active {
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
