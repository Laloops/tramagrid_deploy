<script setup>
  import { computed, onMounted, watch, ref } from 'vue' 
  import { supabase } from './supabase'
  import TopToolbar from './components/TopToolbar.vue'
  import ToastContainer from './components/ToastContainer.vue' 
  import { useRoute, useRouter } from 'vue-router'
  import { API_BASE, restoreSession, sessionId } from './api'; 

  const route = useRoute()
  const router = useRouter()
  
  // Variável para controlar o carregamento inicial (impede erro de sessão fantasma)
  const isAppReady = ref(false); 

  const showTopBar = computed(() => route.path !== '/')

  async function trackVisit() {
    const visitedKey = `tramagrid_visited_${new Date().toISOString().slice(0,10)}`;
    if (sessionStorage.getItem(visitedKey)) return;
    try {
      await fetch(`${API_BASE}/api/track/visit`, { method: 'POST' });
      sessionStorage.setItem(visitedKey, 'true'); 
    } catch(e) { console.warn("Analytics offline."); }
  }

  onMounted(async () => {
    // 1. Verifica a sessão ANTES de mostrar o site (Crucial para evitar erros 404)
    const sessionRestored = await restoreSession();
    
    // Agora que sabemos se a sessão é válida (ou foi limpa), podemos liberar o site
    isAppReady.value = true; 

    if (sessionRestored && route.path === '/') {
        router.push('/editor');
    }

    trackVisit();

    supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') console.log("✅ Sessão iniciada");
      if (event === 'SIGNED_OUT') console.log("👋 Sessão encerrada");
    })
  })

  watch(route, () => {
     // trackVisit(); 
  });
</script>
  
<template>
  <div class="app-layout">
    <template v-if="isAppReady">
      <TopToolbar v-if="showTopBar" />
      <router-view />
    </template>
    
    <div v-else class="loading-screen">
      <div class="spinner"></div>
      <p>A carregar o teu TramaGrid...</p>
    </div>

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

/* Estilo do Loading */
.loading-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #888;
  gap: 1rem;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #333;
  border-top-color: #42b983;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>