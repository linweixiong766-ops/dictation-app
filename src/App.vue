<script setup>
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t, locale } = useI18n()
const router = useRouter()

function switchLocale(lang) {
  locale.value = lang
  localStorage.setItem('locale', lang)
}
</script>

<template>
  <div class="app-container">
    <nav class="navbar">
      <div class="nav-content">
        <router-link to="/" class="nav-brand">{{ t('app.title') }}</router-link>
        <ul class="nav-links">
          <li><router-link to="/">{{ t('nav.home') }}</router-link></li>
          <li><router-link to="/manage">{{ t('nav.manage') }}</router-link></li>
        </ul>
        <div class="nav-right">
          <div class="lang-switch">
            <button
              class="lang-btn"
              :class="{ active: locale === 'zh' }"
              @click="switchLocale('zh')"
            >
              中文
            </button>
            <button
              class="lang-btn"
              :class="{ active: locale === 'en' }"
              @click="switchLocale('en')"
            >
              EN
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
@import './assets/styles/main.css';
</style>
