<script setup>
  import { computed, onMounted, watch } from 'vue'
  import { supabase } from './supabase'
  import TopToolbar from './components/TopToolbar.vue'
  import ToastContainer from './components/ToastContainer.vue' 
  import { useRoute } from 'vue-router'
  import { API_BASE } from './api'; // Importante para chamar o backend

  const route = useRoute()

  const showTopBar = computed(() => {
    return route.path !== '/'
  })

  // Função para registrar visita no banco de dados
  async function trackVisit() {
    try {
      // Chama a rota que criamos no backend para incrementar o contador
      await fetch(`${API_BASE}/api/track/visit`, { method: 'POST' });
    } catch(e) {
      // Falha silenciosa para não atrapalhar a experiência do usuário
      console.warn("Analytics falhou:", e);
    }
  }

  onMounted(() => {
    // 1. Rastreia visita inicial (quando o site carrega)
    trackVisit();

    // 2. Escuta mudanças de autenticação globais
    supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN') {
        console.log("✅ [App.vue] Sessão ativa detectada.")
      } else if (event === 'SIGNED_OUT') {
        console.log("👋 [App.vue] Sessão encerrada.")
      }
    })
  })

  // 3. Rastreia visita a cada mudança de página (navegação interna)
  watch(route, () => {
    trackVisit();
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
  background-color: #121212; /* Fundo base para evitar flashes brancos */
}
</style>