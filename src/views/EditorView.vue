<script setup>
  import { ref, onMounted } from "vue";
  import { useRouter } from "vue-router";
  import ProjectControls from '../components/ProjectControls.vue';
  import ColorPalette from '../components/ColorPalette.vue';
  import GridCanvas from '../components/GridCanvas.vue';
  import { sessionId, getGridImage, getParams, API_BASE } from '../api.js'; 
  import { supabase } from '../supabase';
  import { showToast } from '../toast.js';
  
  const router = useRouter();
  const isLoading = ref(false); 
  const isSaving = ref(false);  
  const isSidebarOpen = ref(true);
  
  // === SALVAR PROJETO ===
  async function handleFinishProject() {
    if (!sessionId.value) return;
  
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      showToast("Faz login para guardar.", "error");
      router.push('/login');
      return;
    }
  
    const nomeProjeto = window.prompt("Nome do Projeto:", "O meu Gráfico");
    if (!nomeProjeto) return;
  
    isSaving.value = true;
    try {
      const base64Img = await getGridImage();
      const params = await getParams();
      
      const res = await fetch(base64Img);
      const blob = await res.blob();
      
      const fileName = `${user.id}/${Date.now()}.png`;
  
      const { error: uploadError } = await supabase.storage
        .from('images') 
        .upload(fileName, blob, { contentType: 'image/png', upsert: true });
  
      if (uploadError) throw uploadError;
  
      const { data: { publicUrl } } = supabase.storage
        .from('images')
        .getPublicUrl(fileName);
  
      const { error: dbError } = await supabase
        .from('projects')
        .insert({
          user_id: user.id,
          name: nomeProjeto,
          image_url: publicUrl,
          settings: params
        });
  
      if (dbError) throw dbError;
      showToast("Projeto guardado!", "success");
  
    } catch (e) {
      console.error(e);
      showToast("Erro ao guardar: " + e.message, "error");
    } finally {
      isSaving.value = false;
    }
  }
  
  // === EXPORTAR PDF ===
  async function exportPDF() {
    if (!sessionId.value) return;
    isLoading.value = true;
    showToast("A gerar preview do PDF...", "info");
    
    try {
      const url = `${API_BASE}/api/export-pdf/${sessionId.value}`;
      window.open(url, '_blank');
      
      showToast("PDF aberto! Escolhe as páginas na opção de imprimir.", "success");
    } catch (err) {
      showToast("Erro ao gerar PDF.", "error");
    } finally {
      isLoading.value = false;
    }
  }
  
  onMounted(() => {
    if (!sessionId.value) router.push('/');
  });
  </script>
  
  <template>
    <div class="editor-layout">
      <!-- Botão hamburguer flutuante quando sidebar fechada -->
      <button v-if="!isSidebarOpen" class="toggle-sidebar-floating" @click="isSidebarOpen = true">☰</button>
      
      <!-- Botões FAB -->
      <button class="fab-finish" @click="handleFinishProject" :disabled="isSaving" title="Salvar Projeto">
        <span v-if="isSaving" class="spinner-small"></span>
        <span v-else class="plus-icon">💾</span>
      </button>
  
      <button class="fab-pdf" @click="exportPDF" :disabled="isLoading" title="Baixar Receita em PDF">
        <span v-if="isLoading" class="spinner-small"></span>
        <span v-else>📄</span>
      </button>
  
      <!-- Sidebar -->
      <aside class="sidebar" :class="{ closed: !isSidebarOpen }">
        <div class="sidebar-header">
          <h2 class="sidebar-title">Ferramentas</h2>
          <button @click="isSidebarOpen = false" class="close-btn">✕</button>
        </div>
        <div class="sidebar-content">
          <ProjectControls />
          <ColorPalette />
        </div>
      </aside>
      
      <main class="canvas-area">
        <GridCanvas />
      </main>
    </div>
  </template>
  
  <style scoped>
  .editor-layout { 
    flex: 1; 
    display: flex; 
    overflow: hidden; 
    position: relative; 
    height: calc(100vh - 60px); /* espaço pro cabeçalho se tiver */
  }
  
  /* Botão hamburguer flutuante */
  .toggle-sidebar-floating { 
    position: absolute; 
    left: 20px; 
    z-index: 1100 !important; /* Deve ser maior que o .side-hud (1000) */
    top: 15px;
    background: #252526; 
    color: #fff; 
    border: 1px solid #444; 
    width: 44px; 
    height: 44px; 
    border-radius: 8px; 
    cursor: pointer; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.4); 
  }
  .toggle-sidebar-floating:hover { 
    background: #333; 
    transform: translateY(-2px); 
    border-color: #e67e22; 
    color: #e67e22; 
  }
  
  /* FABs */
  .fab-finish { 
    position: absolute; 
    bottom: 120px; 
    right: 40px; 
    width: 64px; 
    height: 64px; 
    border-radius: 50%; 
    background: #27ae60; 
    color: white; 
    border: none; 
    cursor: pointer; 
    box-shadow: 0 6px 20px rgba(0,0,0,0.4); 
    z-index: 100; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    transition: all 0.3s; 
  }
  .fab-finish:hover:not(:disabled) { transform: scale(1.1); background: #2ecc71; }
  
  .fab-pdf { 
    position: absolute; 
    bottom: 40px; 
    right: 40px; 
    width: 64px; 
    height: 64px; 
    border-radius: 50%; 
    background: #9b59b6; 
    color: white; 
    border: none; 
    cursor: pointer; 
    box-shadow: 0 6px 20px rgba(0,0,0,0.4); 
    z-index: 100; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    transition: all 0.3s; 
    font-size: 1.8rem;
  }
  .fab-pdf:hover:not(:disabled) { transform: scale(1.1); background: #8e44ad; }
  
  .plus-icon { font-size: 2rem; margin-top: -2px; }
  .spinner-small { 
    width: 24px; 
    height: 24px; 
    border: 3px solid rgba(255,255,255,0.3); 
    border-top-color: white; 
    border-radius: 50%; 
    animation: spin 1s infinite linear; 
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  
  /* Sidebar */
  .sidebar { 
    width: 340px; 
    background: #252526; 
    border-right: 1px solid #333; 
    transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
    display: flex; 
    flex-direction: column; 
    overflow: hidden; 
    z-index: 90; 
    height: 100%; /* ocupa toda a altura disponível */
  }
  .sidebar.closed { 
    width: 0; 
    border: none; 
  }
  
  .sidebar-header { 
    flex-shrink: 0; 
    height: 55px; 
    display: flex; 
    align-items: center; 
    justify-content: space-between; 
    padding: 0 20px; 
    border-bottom: 1px solid #333; 
    background-color: #252526; 
  }
  .sidebar-title { 
    margin: 0; 
    font-size: 0.95rem; 
    color: #ddd; 
    font-weight: 600; 
    text-transform: uppercase; 
    letter-spacing: 1px; 
  }
  .close-btn { 
    background: transparent; 
    border: none; 
    color: #aaa; 
    cursor: pointer; 
    font-size: 1.1rem; 
    width: 32px; 
    height: 32px; 
    border-radius: 6px; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
  }
  .close-btn:hover { background: rgba(255,255,255,0.1); color: white; }
  
  /* Conteúdo da sidebar — FLEX COLUMN PRA COMPONENTES APARECEREM */
  .sidebar-content { 
    flex: 1; 
    overflow-y: auto; 
    padding: 5%; 
    display: flex;
    flex-direction: column;
    gap: 5px; /* espaço entre ProjectControls e ColorPalette */
  }
  
  /* Garante que os componentes dentro ocupem espaço */
  .sidebar-content > * {
    width: 85%;
  }
  
  .canvas-area { 
    flex: 1; 
    background: #0f0f0f; 
    overflow: hidden; 
    position: relative; 
  }
  
  /* Scroll bonito */
  .sidebar-content::-webkit-scrollbar { width: 6px; }
  .sidebar-content::-webkit-scrollbar-track { background: transparent; }
  .sidebar-content::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }

  @media (max-width: 768px) {
  .side-hud {
    top: 70px !important; /* Espaço para o botão hambúrguer */
  }
}
  </style>

  