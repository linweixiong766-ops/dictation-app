import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue')
  },
  {
    path: '/practice/:lang/:listId',
    name: 'Practice',
    component: () => import('../views/PracticeView.vue'),
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
