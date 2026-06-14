<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWordStore } from '../stores/wordStore'

const { t, locale } = useI18n()
const wordStore = useWordStore()

const selectedLang = ref(locale.value)
const selectedListIndex = ref(-1)
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

onMounted(() => {
  wordStore.loadCustomLists()
})

function switchLanguage(lang) {
  selectedLang.value = lang
  selectedListIndex.value = -1
}

function selectList(index) {
  selectedListIndex.value = index
}

function getSelectedList() {
  const customLists = wordStore.customLists.filter(l => l.language === selectedLang.value)
  return customLists[selectedListIndex.value]
}

function openAddModal() {
  newWord.value = { word: '', meaning: '', phonetic: '', pinyin: '' }
  showAddModal.value = true
}

function openEditModal(wordIndex) {
  const list = getSelectedList()
  if (!list) return

  editingWordIndex.value = wordIndex
  newWord.value = { ...list.words[wordIndex] }
  showEditModal.value = true
}

function openAddListModal() {
  newListName.value = ''
  showAddListModal.value = true
}

function addWord() {
  const list = getSelectedList()
  if (!list) return

  wordStore.addWordToList(selectedListIndex.value, { ...newWord.value })
  showAddModal.value = false
}

function updateWord() {
  const list = getSelectedList()
  if (!list) return

  wordStore.updateWordInList(selectedListIndex.value, editingWordIndex.value, { ...newWord.value })
  showEditModal.value = false
}

function deleteWord(wordIndex) {
  if (confirm(t('manage.confirmDelete'))) {
    wordStore.deleteWordFromList(selectedListIndex.value, wordIndex)
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

function deleteList(index) {
  if (confirm(t('manage.confirmDelete'))) {
    wordStore.deleteCustomList(index)
    if (selectedListIndex.value === index) {
      selectedListIndex.value = -1
    } else if (selectedListIndex.value > index) {
      selectedListIndex.value--
    }
  }
}

function exportList() {
  const list = getSelectedList()
  if (!list) return

  const dataStr = JSON.stringify(list, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)

  const exportFileDefaultName = `${list.name}.json`

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
            v-for="(list, index) in wordStore.customLists.filter(l => l.language === selectedLang)"
            :key="index"
            class="list-card"
            :class="{ active: selectedListIndex === index }"
            @click="selectList(index)"
          >
            <div class="list-card-title">{{ list.name }}</div>
            <div class="list-card-info">{{ list.words.length }} {{ t('practice.total') }}</div>
            <button class="btn btn-danger btn-sm" @click.stop="deleteList(index)">
              {{ t('common.delete') }}
            </button>
          </div>

          <div class="list-card add-card" @click="openAddListModal">
            <div class="list-card-title">+ {{ t('manage.addNewList') }}</div>
          </div>
        </div>
      </div>

      <!-- Word Management -->
      <div v-if="selectedListIndex >= 0" class="card">
        <div class="manage-header">
          <h2 class="card-title">{{ getSelectedList()?.name }}</h2>
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

        <table v-if="getSelectedList()?.words.length" class="word-table">
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
            <tr v-for="(word, wordIndex) in getSelectedList()?.words" :key="wordIndex">
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

        <div v-else class="card">
          <p>{{ t('manage.noWords') }}</p>
        </div>
      </div>
    </div>

    <!-- Add Word Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal">
        <h3 class="modal-title">{{ t('manage.addWord') }}</h3>
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
          <button class="btn btn-outline" @click="showAddModal = false">{{ t('manage.cancel') }}</button>
          <button class="btn btn-primary" @click="addWord">{{ t('manage.save') }}</button>
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
          <input v-model="newListName" class="input" />
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
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.list-card {
  position: relative;
}

.list-card.active {
  border-color: var(--primary-color);
  background: rgba(74, 144, 226, 0.05);
}

.list-card .btn-danger {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
}

.add-card {
  border: 2px dashed var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100px;
  color: var(--text-light);
}

.add-card:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
