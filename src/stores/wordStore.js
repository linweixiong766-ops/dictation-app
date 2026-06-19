import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useWordStore = defineStore('word', () => {
  // State
  const wordLists = ref([])
  const customLists = ref([])
  const currentList = ref(null)
  const currentLanguage = ref('en')
  const isLoading = ref(false)
  const error = ref(null)

  // 选择状态存储
  const selectedWordIndices = ref([])
  const selectedListId = ref(null)
  const selectedLang = ref(null)

  // All available word list files
  const wordListFiles = {
    en: [
      'grade3-fall.json',
      'grade3-spring.json',
      'grade4-fall.json',
      'grade4-spring.json',
      'grade5-fall.json',
      'grade5-spring.json',
      'grade6-fall.json',
      'grade6-spring.json'
    ],
    zh: [
      'grade3.json',
      'grade4.json',
      'pinyin-preschool.json',
      'pinyin-reading.json'
    ]
  }

  // Load word lists from JSON files
  async function loadWordLists(lang) {
    isLoading.value = true
    error.value = null
    try {
      const files = wordListFiles[lang] || []
      const lists = []

      // Load all files in parallel
      const promises = files.map(async (file) => {
        try {
          const response = await fetch(`/data/${lang}/${file}`)
          if (response.ok) {
            const data = await response.json()
            return data
          }
        } catch (err) {
          console.warn(`Failed to load ${file}:`, err)
        }
        return null
      })

      const results = await Promise.all(promises)
      results.forEach(data => {
        if (data) lists.push(data)
      })

      wordLists.value = lists
    } catch (err) {
      error.value = err.message
      console.error('Failed to load word lists:', err)
    } finally {
      isLoading.value = false
    }
  }

  // Load custom lists from localStorage
  function loadCustomLists() {
    try {
      const saved = localStorage.getItem('customWordLists')
      if (saved) {
        customLists.value = JSON.parse(saved)
      }
    } catch (err) {
      console.error('Failed to load custom lists:', err)
    }
  }

  // Save custom lists to localStorage
  function saveCustomLists() {
    try {
      localStorage.setItem('customWordLists', JSON.stringify(customLists.value))
    } catch (err) {
      console.error('Failed to save custom lists:', err)
    }
  }

  // Add a new custom list
  function addCustomList(list) {
    customLists.value.push(list)
    saveCustomLists()
  }

  // Update a custom list
  function updateCustomList(index, list) {
    customLists.value[index] = list
    saveCustomLists()
  }

  // Delete a custom list
  function deleteCustomList(index) {
    customLists.value.splice(index, 1)
    saveCustomLists()
  }

  // Add word to a custom list
  function addWordToList(listIndex, word) {
    if (customLists.value[listIndex]) {
      customLists.value[listIndex].words.push(word)
      saveCustomLists()
    }
  }

  // Update word in a custom list
  function updateWordInList(listIndex, wordIndex, word) {
    if (customLists.value[listIndex]?.words[wordIndex]) {
      customLists.value[listIndex].words[wordIndex] = word
      saveCustomLists()
    }
  }

  // Delete word from a custom list
  function deleteWordFromList(listIndex, wordIndex) {
    if (customLists.value[listIndex]) {
      customLists.value[listIndex].words.splice(wordIndex, 1)
      saveCustomLists()
    }
  }

  // Get all available lists for current language
  const availableLists = computed(() => {
    const langLists = wordLists.value.filter(l => l.language === currentLanguage.value)
    const customLangLists = customLists.value.filter(l => l.language === currentLanguage.value)
    return [...langLists, ...customLangLists]
  })

  // Get list by ID
  function getListById(lang, listId) {
    const allLists = [...wordLists.value, ...customLists.value]
    return allLists.find(l => l.language === lang && l.category === listId)
  }

  // 保存选择状态
  function saveSelection(lang, listId, indices) {
    selectedLang.value = lang
    selectedListId.value = listId
    selectedWordIndices.value = [...indices]
    // 同时保存到 localStorage 以便刷新后恢复
    try {
      localStorage.setItem('lastSelection', JSON.stringify({
        lang,
        listId,
        indices,
        timestamp: Date.now()
      }))
    } catch (err) {
      console.error('Failed to save selection:', err)
    }
  }

  // 恢复选择状态
  function restoreSelection() {
    // 首先从内存中恢复
    if (selectedLang.value && selectedListId.value && selectedWordIndices.value.length > 0) {
      return {
        lang: selectedLang.value,
        listId: selectedListId.value,
        indices: selectedWordIndices.value
      }
    }
    // 然后从 localStorage 恢复
    try {
      const saved = localStorage.getItem('lastSelection')
      if (saved) {
        const data = JSON.parse(saved)
        // 检查是否在 24 小时内
        if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
          selectedLang.value = data.lang
          selectedListId.value = data.listId
          selectedWordIndices.value = data.indices
          return data
        }
      }
    } catch (err) {
      console.error('Failed to restore selection:', err)
    }
    return null
  }

  // 清除选择状态
  function clearSelection() {
    selectedLang.value = null
    selectedListId.value = null
    selectedWordIndices.value = []
    try {
      localStorage.removeItem('lastSelection')
    } catch (err) {
      console.error('Failed to clear selection:', err)
    }
  }

  return {
    wordLists,
    customLists,
    currentList,
    currentLanguage,
    isLoading,
    error,
    availableLists,
    selectedWordIndices,
    selectedListId,
    selectedLang,
    loadWordLists,
    loadCustomLists,
    saveCustomLists,
    addCustomList,
    updateCustomList,
    deleteCustomList,
    addWordToList,
    updateWordInList,
    deleteWordFromList,
    getListById,
    saveSelection,
    restoreSelection,
    clearSelection
  }
})
