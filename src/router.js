import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import EditorView from './views/EditorView.vue'
import LoginView from './views/LoginView.vue'
import BuyCreditsView from './views/BuyCreditsView.vue'
import DashboardView from './views/DashboardView.vue'

import { supabase } from './supabase'
import { sessionId } from './api.js' // Importa o sessionId global

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { 
    path: '/editor', 
    name: 'editor', 
    component: EditorView,
    meta: { requiresAuth: true, requiresSession: true } // Protegida
  },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/buy-credits', name: 'buy-credits', component: BuyCreditsView, meta: { requiresAuth: true } },
  { 
    path: '/dashboard', 
    name: 'dashboard', 
    component: DashboardView, 
    meta: { requiresAuth: true } 
  },
  { path: '/:pathMatch(.*)*', redirect: '/' } // Catch-all
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// =================================================================================
// NAVIGATION GUARDS (sofisticados e funcionais)
// =================================================================================
router.beforeEach(async (to, from, next) => {
  // 1. Busca o usuário atual (cacheado pelo Supabase)
  const { data: { user } } = await supabase.auth.getUser()

  const isAuthenticated = !!user
  const hasSession = !!sessionId.value

  // 2. Rotas que exigem autenticação
  if (to.meta.requiresAuth && !isAuthenticated) {
    // Salva a rota que queria acessar pra redirecionar após login
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  // 3. /editor exige sessão ativa
  if (to.name === 'editor' && to.meta.requiresSession && !hasSession) {
    return next({ name: 'home' })
  }

  // 4. Se logado e tentar acessar login → vai pro dashboard
  if (to.name === 'login' && isAuthenticated) {
    return next({ name: 'dashboard' })
  }

  // 5. Se logado e acessar home → pode ir pro dashboard (opcional)
  if (to.name === 'home' && isAuthenticated) {
  return next({ name: 'dashboard' })
  }

  // 6. Tudo ok → prossegue
  next()
})

export default router