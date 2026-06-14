<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useWordStore } from '../stores/wordStore'

const { t, locale } = useI18n()
const router = useRouter()
const wordStore = useWordStore()

const selectedLang = ref(locale.value)

onMounted(async () => {
  await loadLists()
})

async function loadLists() {
  await wordStore.loadWordLists(selectedLang.value)
  wordStore.loadCustomLists()
  wordStore.currentLanguage = selectedLang.value
}

async function switchLanguage(lang) {
  selectedLang.value = lang
  await loadLists()
}

function startPractice(listId) {
  router.push(`/select/${selectedLang.value}/${listId}`)
}
</script>

<template>
  <div class="home-view">
    <div class="hero">
      <h1>{{ t('home.welcome') }}</h1>
      <p>{{ t('home.description') }}</p>
    </div>

    <div class="card home-card">
      <h2 class="card-title">{{ t('home.selectLanguage') }}</h2>
      <div class="lang-switch">
        <button
          class="btn"
          :class="selectedLang === 'zh' ? 'btn-primary' : 'btn-outline'"
          @click="switchLanguage('zh')"
        >
          🇨🇳 {{ t('language.zh') }}
        </button>
        <button
          class="btn"
          :class="selectedLang === 'en' ? 'btn-primary' : 'btn-outline'"
          @click="switchLanguage('en')"
        >
          🇺🇸 {{ t('language.en') }}
        </button>
      </div>
    </div>

    <h2 class="section-title">{{ t('home.selectList') }}</h2>

    <div v-if="wordStore.isLoading" class="card home-card">
      <div class="empty-state">
        <div class="empty-state-icon">⏳</div>
        <p>{{ t('common.loading') }}</p>
      </div>
    </div>

    <div v-else-if="wordStore.error" class="card home-card">
      <div class="empty-state">
        <div class="empty-state-icon">❌</div>
        <p>{{ t('common.error') }}: {{ wordStore.error }}</p>
      </div>
    </div>

    <div v-else class="grid grid-2">
      <div
        v-for="(list, index) in wordStore.availableLists"
        :key="index"
        class="list-card home-list-card"
        @click="startPractice(list.category)"
      >
        <div class="list-card-title">{{ list.name }}</div>
        <div class="list-card-info">
          {{ list.words.length }} {{ t('practice.total') }}
        </div>
        <div class="list-card-action">
          <span class="btn btn-primary btn-sm">{{ t('home.startPractice') }} →</span>
        </div>
      </div>

      <div v-if="wordStore.availableLists.length === 0" class="card home-card">
        <div class="empty-state">
          <div class="empty-state-icon">📭</div>
          <p>{{ t('common.noData') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 800px;
  margin: 0 auto;
}

.lang-switch {
  display: flex;
  gap: 1rem;
}

.list-card-action {
  margin-top: 1rem;
  opacity: 0;
  transform: translateY(10px);
  transition: var(--transition);
}

.list-card:hover .list-card-action {
  opacity: 1;
  transform: translateY(0);
}
</style>
