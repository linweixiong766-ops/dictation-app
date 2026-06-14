<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWordStore } from '../stores/wordStore'

const { t, locale } = useI18n()
const wordStore = useWordStore()

const selectedLang = ref(locale.value)
const selectedListName = ref('')
const showAddModal = ref(false)
const showEditModal = ref(false)
const showAddListModal = ref(false)
const editingWordIndex = ref(-1)

const newListName = ref('')
const newWord = ref({
  word: '',
  meaning: '',
  phonetic: '',
  pinyin: ''
})

const phoneticField = computed({
  get() {
    return selectedLang.value === 'en' ? newWord.value.phonetic : newWord.value.pinyin
  },
  set(value) {
    if (selectedLang.value === 'en') {
      newWord.value.phonetic = value
    } else {
      newWord.value.pinyin = value
    }
  }
})

// Get filtered lists for current language
const filteredLists = computed(() => {
  return wordStore.customLists.filter(l => l.language === selectedLang.value)
})

// Get the selected list object
const selectedList = computed(() => {
  if (!selectedListName.value) return null
  return wordStore.customLists.find(
    l => l.language === selectedLang.value && l.name === selectedListName.value
  )
})

// Get the real index of selected list in the unfiltered store array
const realListIndex = computed(() => {
  if (!selectedList.value) return -1
  return wordStore.customLists.indexOf(selectedList.value)
})

onMounted(() => {
  wordStore.loadCustomLists()
})

function switchLanguage(lang) {
  selectedLang.value = lang
  selectedListName.value = ''
}

function selectList(listName) {
  selectedListName.value = listName
}

function openAddModal() {
  newWord.value = { word: '', meaning: '', phonetic: '', pinyin: '' }
  showAddModal.value = true
}

function openEditModal(wordIndex) {
  if (!selectedList.value) return

  editingWordIndex.value = wordIndex
  newWord.value = { ...selectedList.value.words[wordIndex] }
  showEditModal.value = true
}

function openAddListModal() {
  newListName.value = ''
  showAddListModal.value = true
}

function addWord() {
  if (!selectedList.value || realListIndex.value < 0) return

  wordStore.addWordToList(realListIndex.value, { ...newWord.value })
  showAddModal.value = false
}

function updateWord() {
  if (!selectedList.value || realListIndex.value < 0) return

  wordStore.updateWordInList(realListIndex.value, editingWordIndex.value, { ...newWord.value })
  showEditModal.value = false
}

function deleteWord(wordIndex) {
  if (confirm(t('manage.confirmDelete')) && realListIndex.value >= 0) {
    wordStore.deleteWordFromList(realListIndex.value, wordIndex)
  }
}

function addList() {
  const newList = {
    name: newListName.value,
    language: selectedLang.value,
    category: newListName.value.toLowerCase().replace(/\s+/g, '-'),
    words: []
  }
  wordStore.addCustomList(newList)
  showAddListModal.value = false
}

function deleteList(listName) {
  if (confirm(t('manage.confirmDelete'))) {
    const index = wordStore.customLists.findIndex(
      l => l.language === selectedLang.value && l.name === listName
    )
    if (index >= 0) {
      wordStore.deleteCustomList(index)
      if (selectedListName.value === listName) {
        selectedListName.value = ''
      }
    }
  }
}

function exportList() {
  if (!selectedList.value) return

  const dataStr = JSON.stringify(selectedList.value, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)

  const exportFileDefaultName = `${selectedList.value.name}.json`

  const linkElement = document.createElement('a')
  linkElement.setAttribute('href', dataUri)
  linkElement.setAttribute('download', exportFileDefaultName)
  linkElement.click()
}

function importList(event) {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const imported = JSON.parse(e.target.result)
      if (imported.name && imported.words && Array.isArray(imported.words)) {
        imported.language = selectedLang.value
        wordStore.addCustomList(imported)
      } else {
        alert(t('common.error'))
      }
    } catch (err) {
      alert(t('common.error'))
    }
  }
  reader.readAsText(file)
  event.target.value = ''
}
</script>

<template>
  <div class="manage-view">
    <div class="manage-header">
      <h1>{{ t('manage.title') }}</h1>
      <div class="lang-switch">
        <button
          class="btn"
          :class="selectedLang === 'zh' ? 'btn-primary' : 'btn-outline'"
          @click="switchLanguage('zh')"
        >
          {{ t('language.zh') }}
        </button>
        <button
          class="btn"
          :class="selectedLang === 'en' ? 'btn-primary' : 'btn-outline'"
          @click="switchLanguage('en')"
        >
          {{ t('language.en') }}
        </button>
      </div>
    </div>

    <div class="manage-content">
      <!-- List Selection -->
      <div class="card">
        <h2 class="card-title">{{ t('home.selectList') }}</h2>
        <div class="list-grid">
          <div
            v-for="list in filteredLists"
            :key="list.name"
            class="list-card"
            :class="{ active: selectedListName === list.name }"
            @click="selectList(list.name)"
          >
            <div class="list-card-title">{{ list.name }}</div>
            <div class="list-card-info">{{ list.words.length }} {{ t('practice.total') }}</div>
            <button class="btn btn-danger btn-sm" @click.stop="deleteList(list.name)">
              {{ t('common.delete') }}
            </button>
          </div>

          <div class="list-card add-card" @click="openAddListModal">
            <div class="list-card-title">+ {{ t('manage.addNewList') }}</div>
          </div>
        </div>
      </div>

      <!-- Word Management -->
      <div v-if="selectedList" class="card">
        <div class="manage-header">
          <h2 class="card-title">{{ selectedList.name }}</h2>
          <div class="actions">
            <button class="btn btn-primary" @click="openAddModal">
              {{ t('manage.addWord') }}
            </button>
            <button class="btn btn-outline" @click="exportList">
              {{ t('manage.exportList') }}
            </button>
            <label class="btn btn-outline">
              {{ t('manage.importList') }}
              <input type="file" accept=".json" @change="importList" style="display: none;">
            </label>
          </div>
        </div>

        <table v-if="selectedList.words.length" class="word-table">
          <thead>
            <tr>
              <th>{{ t('manage.word') }}</th>
              <th>{{ t('manage.meaning') }}</th>
              <th>{{ selectedLang === 'en' ? t('manage.phonetic') : t('manage.pinyin') }}</th>
              <th>{{ t('common.edit') }}</th>
              <th>{{ t('common.delete') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(word, wordIndex) in selectedList.words" :key="wordIndex">
              <td>{{ word.word }}</td>
              <td>{{ word.meaning }}</td>
              <td>{{ word.phonetic || word.pinyin }}</td>
              <td>
                <button class="btn btn-outline btn-sm" @click="openEditModal(wordIndex)">
                  {{ t('common.edit') }}
                </button>
              </td>
              <td>
                <button class="btn btn-danger btn-sm" @click="deleteWord(wordIndex)">
                  {{ t('common.delete') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="empty-state">
          <div class="empty-state-icon">📝</div>
          <p>{{ t('manage.noWords') }}</p>
        </div>
      </div>

      <div v-else-if="filteredLists.length > 0" class="card">
        <div class="empty-state">
          <div class="empty-state-icon">👆</div>
          <p>{{ t('home.selectList') }}</p>
        </div>
      </div>
    </div>

    <!-- Add Word Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal">
        <h3 class="modal-title">{{ t('manage.addWord') }}</h3>
        <div class="input-group">
          <label>{{ t('manage.word') }}</label>
          <input v-model="newWord.word" class="input" :placeholder="selectedLang === 'en' ? 'apple' : '苹果'" />
        </div>
        <div class="input-group">
          <label>{{ t('manage.meaning') }}</label>
          <input v-model="newWord.meaning" class="input" :placeholder="selectedLang === 'en' ? '苹果' : 'apple'" />
        </div>
        <div class="input-group">
          <label>{{ selectedLang === 'en' ? t('manage.phonetic') : t('manage.pinyin') }}</label>
          <input v-model="phoneticField" class="input" :placeholder="selectedLang === 'en' ? '/ˈæp.əl/' : 'píng guǒ'" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showAddModal = false">{{ t('manage.cancel') }}</button>
          <button class="btn btn-primary" @click="addWord" :disabled="!newWord.word.trim()">{{ t('manage.save') }}</button>
        </div>
      </div>
    </div>

    <!-- Edit Word Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal">
        <h3 class="modal-title">{{ t('manage.editWord') }}</h3>
        <div class="input-group">
          <label>{{ t('manage.word') }}</label>
          <input v-model="newWord.word" class="input" />
        </div>
        <div class="input-group">
          <label>{{ t('manage.meaning') }}</label>
          <input v-model="newWord.meaning" class="input" />
        </div>
        <div class="input-group">
          <label>{{ selectedLang === 'en' ? t('manage.phonetic') : t('manage.pinyin') }}</label>
          <input v-model="phoneticField" class="input" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showEditModal = false">{{ t('manage.cancel') }}</button>
          <button class="btn btn-primary" @click="updateWord">{{ t('manage.save') }}</button>
        </div>
      </div>
    </div>

    <!-- Add List Modal -->
    <div v-if="showAddListModal" class="modal-overlay" @click.self="showAddListModal = false">
      <div class="modal">
        <h3 class="modal-title">{{ t('manage.addNewList') }}</h3>
        <div class="input-group">
          <label>{{ t('manage.listName') }}</label>
          <input v-model="newListName" class="input" :placeholder="selectedLang === 'en' ? 'My Word List' : '我的词库'" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showAddListModal = false">{{ t('manage.cancel') }}</button>
          <button class="btn btn-primary" @click="addList" :disabled="!newListName.trim()">{{ t('manage.save') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.manage-view {
  max-width: 1000px;
  margin: 0 auto;
}

.manage-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.list-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.list-card {
  position: relative;
}

.list-card.active {
  border-color: var(--primary);
  background: var(--primary-light);
}

.list-card .btn-danger {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  opacity: 0;
  transition: var(--transition);
}

.list-card:hover .btn-danger {
  opacity: 1;
}

.add-card {
  border: 2px dashed var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.5);
}

.add-card:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
