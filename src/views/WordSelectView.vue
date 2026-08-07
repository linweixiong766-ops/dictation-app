<script setup>
import { ref, computed, onMounted, watch, nextTick, onUnmounted } from 'vue'
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
const showUnitDropdown = ref(false) // 控制单元下拉框显示
const expandedGroups = ref([]) // 控制分组展开/折叠
const lastClickedUnit = ref(null) // 记录最后点击的单元

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

  // 添加点击外部关闭下拉框的监听
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(event) {
  const dropdown = document.querySelector('.unit-dropdown-wrapper')
  if (dropdown && !dropdown.contains(event.target)) {
    showUnitDropdown.value = false
  }
}

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
  // 记录最后点击的单元，用于排序
  lastClickedUnit.value = unit
  // 延迟更新选择状态，避免频繁重渲染
  nextTick(() => onUnitChange())
}

// 排序后的单元列表：最后点击的排在最前面
const sortedUnits = computed(() => {
  if (!lastClickedUnit.value) return availableUnits.value
  return [...availableUnits.value].sort((a, b) => {
    if (a === lastClickedUnit.value) return -1
    if (b === lastClickedUnit.value) return 1
    return 0
  })
})

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
        <div class="unit-dropdown-wrapper">
          <button
            class="btn unit-dropdown-btn"
            :class="{ 'active': showUnitDropdown, 'has-selection': selectedUnits.length > 0 }"
            @click="showUnitDropdown = !showUnitDropdown"
          >
            📚 选择单元
            <span v-if="selectedUnits.length > 0" class="unit-badge">{{ selectedUnits.length }}</span>
            <span class="dropdown-arrow">{{ showUnitDropdown ? '▲' : '▼' }}</span>
          </button>
          <div v-if="showUnitDropdown" class="unit-dropdown">
            <div class="unit-dropdown-header">
              <button class="btn btn-sm btn-outline" @click="selectAllUnits">全选</button>
              <button class="btn btn-sm btn-outline" @click="clearAllUnits">清除</button>
              <button class="btn btn-sm btn-outline" @click="showUnitDropdown = false">关闭</button>
            </div>
            <div class="unit-dropdown-list">
              <div
                v-for="unit in sortedUnits"
                :key="unit"
                class="unit-dropdown-item"
                :class="{ 'selected': selectedUnits.includes(unit) }"
                @click="toggleUnit(unit)"
              >
                <div class="unit-checkbox" :class="{ 'checked': selectedUnits.includes(unit) }">
                  <span v-if="selectedUnits.includes(unit)">✓</span>
                </div>
                <span class="unit-dropdown-name">{{ unit }}</span>
                <span class="unit-dropdown-count">{{ wordsByUnit[unit]?.length || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
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

.unit-dropdown-wrapper {
  position: relative;
}

.unit-dropdown-btn {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: 50px;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
  display: flex;
  align-items: center;
  gap: 0.6rem;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
}

.unit-dropdown-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
  background: linear-gradient(135deg, #9b6ff7, #8b4ff8);
}

.unit-dropdown-btn.active {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
  transform: translateY(0);
}

.unit-dropdown-btn.has-selection {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.unit-dropdown-btn.has-selection:hover {
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
  background: linear-gradient(135deg, #14d696, #06b57a);
}

.unit-badge {
  background: rgba(255, 255, 255, 0.25);
  padding: 0.2rem 0.5rem;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 700;
  min-width: 20px;
  text-align: center;
}

.dropdown-arrow {
  font-size: 0.7rem;
  margin-left: 0.15rem;
  opacity: 0.8;
}

.unit-dropdown {
  position: absolute;
  top: calc(100% + 0.75rem);
  left: 0;
  min-width: 300px;
  background: white;
  border: none;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.08);
  z-index: 1000;
  animation: dropdownSlide 0.25s ease-out;
  overflow: hidden;
}

@keyframes dropdownSlide {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.unit-dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  background: linear-gradient(135deg, #f9fafb, #f3f4f6);
}

.unit-dropdown-header .btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
  border-radius: 8px;
}

.unit-dropdown-list {
  max-height: 320px;
  overflow-y: auto;
  padding: 0.5rem;
}

.unit-dropdown-list::-webkit-scrollbar {
  width: 6px;
}

.unit-dropdown-list::-webkit-scrollbar-track {
  background: transparent;
}

.unit-dropdown-list::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.unit-dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 0.8rem;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.2s ease;
  margin: 2px 0;
}

.unit-dropdown-item:hover {
  background: #f3f4f6;
}

.unit-dropdown-item.selected {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(139, 92, 246, 0.12));
}

.unit-checkbox {
  width: 22px;
  height: 22px;
  border: 2px solid #d1d5db;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.unit-checkbox.checked {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border-color: #7c3aed;
  color: white;
  font-size: 14px;
  font-weight: bold;
}

.unit-dropdown-name {
  flex: 1;
  font-weight: 500;
  color: #374151;
  font-size: 0.95rem;
}

.unit-dropdown-count {
  font-size: 0.8rem;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.2rem 0.6rem;
  border-radius: 8px;
  font-weight: 500;
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
