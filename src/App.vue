<script setup>
  import { computed, onMounted, watch } from 'vue'
  import { supabase } from './supabase'
  import TopToolbar from './components/TopToolbar.vue'
  import ToastContainer from './components/ToastContainer.vue' 
  import { useRoute, useRouter } from 'vue-router'
  import { API_BASE, restoreSession, sessionId } from './api'; // Importe o restoreSession

  const route = useRoute()
  const router = useRouter()

  const showTopBar = computed(() => route.path !== '/')

  // Função com "debounce" simples de sessão para não contar F5 como nova visita
  async function trackVisit() {
    // Se já visitou nesta sessão do navegador, não conta de novo (opcional)
    const visitedKey = `tramagrid_visited_${new Date().toISOString().slice(0,10)}`;
    if (sessionStorage.getItem(visitedKey)) return;

    try {
      await fetch(`${API_BASE}/api/track/visit`, { method: 'POST' });
      sessionStorage.setItem(visitedKey, 'true'); // Marca que já visitou hoje
    } catch(e) {
      console.warn("Analytics offline.");
    }
  }

  onMounted(async () => {
    // 1. Tenta restaurar projeto anterior (Prioridade Alta)
    const sessionRestored = await restoreSession();
    
    // Se estava na Home e recuperou sessão, joga pro Editor
    if (sessionRestored && route.path === '/') {
        router.push('/editor');
    }

    // 2. Rastreia visita
    trackVisit();

    // 3. Monitora Auth
    supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') console.log("✅ Sessão iniciada");
      if (event === 'SIGNED_OUT') console.log("👋 Sessão encerrada");
    })
  })

  // Se quiser contar pageviews (cada troca de página), mantenha o watch.
  // Se quiser apenas visitantes únicos, remova este watch.
  watch(route, () => {
     // trackVisit(); // Descomente se quiser contar cada clique no menu
  });
</script>
  
<template>
  <div class="app-layout">
    <TopToolbar v-if="showTopBar" />
    <router-view />
    <ToastContainer /> 
  </div>
</template>
  
<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: #121212;
}
</style>