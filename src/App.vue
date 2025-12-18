<script setup>
  import { computed, onMounted } from 'vue'
  import { supabase } from './supabase'
  import TopToolbar from './components/TopToolbar.vue'
  import ToastContainer from './components/ToastContainer.vue' 
  import { useRoute } from 'vue-router'
  const route = useRoute()

  const showTopBar = computed(() => {
    return route.path !== '/'
  })

  onMounted(() => {
    // Escuta mudanças de autenticação globais
    supabase.auth.onAuthStateChange((event, session) => {
      // Isso ajuda a debugar se o login caiu ou se o link mágico funcionou
      if (event === 'SIGNED_IN') {
        console.log("✅ [App.vue] Sessão ativa detectada.")
      } else if (event === 'SIGNED_OUT') {
        console.log("👋 [App.vue] Sessão encerrada.")
      }
    })
  })
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