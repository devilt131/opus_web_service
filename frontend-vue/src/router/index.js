import { createRouter, createWebHistory } from 'vue-router'
import Analyze from '../views/Analyze.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import Settings from '../views/Settings.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'analyze', component: Analyze, meta: { requiresAuth: true } },
    { path: '/login', name: 'login', component: Login, meta: { requiresAuth: false } },
    { path: '/register', name: 'register', component: Register, meta: { requiresAuth: false } },
    { path: '/profile', name: 'profile', component: Profile, meta: { requiresAuth: true } },
    { path: '/settings', name: 'settings', component: Settings, meta: { requiresAuth: true } }
  ]
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
