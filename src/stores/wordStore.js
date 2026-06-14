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

  // Load word lists from JSON files
  async function loadWordLists(lang) {
    isLoading.value = true
    error.value = null
    try {
      const response = await fetch(`/data/${lang}/grade3.json`)
      const response2 = await fetch(`/data/${lang}/grade4.json`)
      const lists = []

      if (response.ok) {
        const data = await response.json()
        lists.push(data)
      }
      if (response2.ok) {
        const data2 = await response2.json()
        lists.push(data2)
      }

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

  return {
    wordLists,
    customLists,
    currentList,
    currentLanguage,
    isLoading,
    error,
    availableLists,
    loadWordLists,
    loadCustomLists,
    saveCustomLists,
    addCustomList,
    updateCustomList,
    deleteCustomList,
    addWordToList,
    updateWordInList,
    deleteWordFromList,
    getListById
  }
})
