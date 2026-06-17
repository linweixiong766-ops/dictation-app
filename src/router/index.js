import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue')
  },
  {
    path: '/select/:lang/:listId',
    name: 'WordSelect',
    component: () => import('../views/WordSelectView.vue'),
    props: true
  },
  {
    path: '/learn/:lang/:listId',
    name: 'Learning',
    component: () => import('../views/LearningView.vue'),
    props: true
  },
  {
    path: '/practice/:lang/:listId',
    name: 'Practice',
    component: () => import('../views/PracticeView.vue'),
    props: true
  },
  {
    path: '/group/:lang/:listId',
    name: 'GroupPractice',
    component: () => import('../views/GroupPracticeView.vue'),
    props: true
  },
  {
    path: '/game/:lang/:listId',
    name: 'FpsGame',
    component: () => import('../views/FpsGameView.vue'),
    props: true
  },
  {
    path: '/manage',
    name: 'Manage',
    component: () => import('../views/ManageView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
