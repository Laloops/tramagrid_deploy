<script setup>
  import { ref, onMounted, computed } from "vue";
  import { useRouter } from "vue-router";
  import { supabase } from "../supabase";
  // Importamos API_BASE e eventBus para lidar com os créditos
  import {
    API_BASE,
    loadProjectFromSupabase,
    createSession,
    uploadImage,
    generateGrid,
    eventBus
  } from "../api.js";
  import { showToast, showConfirm } from "../toast.js";
  
  const router = useRouter();
  const projects = ref([]);
  const loading = ref(true);
  const userProfile = ref(null);
  const hasFreeGeneration = ref(false);
  const currentCredits = ref(0);
  
  // Painel flutuante
  const showUploadModal = ref(false);
  const uploadFile = ref(null);
  const uploadLoading = ref(false);
  
  const firstName = computed(() => {
    const email = userProfile.value?.email || "";
    return email.split("@")[0] || "Artista";
  });
  
  onMounted(async () => {
    await fetchUserData();
    await fetchProjects();
  });
  
  async function fetchUserData() {
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) {
      router.push("/login");
      return;
    }
    userProfile.value = user;
  
    const { data: profile } = await supabase
      .from("profiles")
      .select("credits, free_generation_used")
      .eq("id", user.id)
      .single();
  
    if (profile) {
      currentCredits.value = profile.credits || 0;
      hasFreeGeneration.value = !profile.free_generation_used;
    }
  }
  
  async function fetchProjects() {
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) return;
  
    const { data, error } = await supabase
      .from("projects")
      .select("*")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false });
  
    if (error) {
      console.error("Erro:", error);
      showToast("Erro ao carregar projetos", "error");
    } else {
      projects.value = data || [];
    }
    loading.value = false;
  }
  
  async function openProject(project) {
    const confirmed = await showConfirm(
      `Abrir "${project.name}"?\nIsso vai substituir o trabalho atual.`
    );
    if (!confirmed) return;
  
    loading.value = true;
    try {
      const projectAdapter = {
        ...project,
        image_path: project.image_url || project.image_path,
      };
  
      const success = await loadProjectFromSupabase(projectAdapter);
  
      if (success) {
        router.push("/editor");
      } else {
        throw new Error("Falha ao carregar projeto");
      }
    } catch (e) {
      showToast("Erro ao abrir projeto: " + e.message, "error");
      loading.value = false;
    }
  }
  
  async function deleteProject(id) {
    const confirmed = await showConfirm(
      "Tem certeza que quer apagar este projeto?"
    );
    if (!confirmed) return;
  
    const previousList = [...projects.value];
    projects.value = projects.value.filter((p) => p.id !== id);
  
    const { error } = await supabase.from("projects").delete().eq("id", id);
  
    if (error) {
      showToast("Erro ao apagar projeto.", "error");
      projects.value = previousList;
    } else {
      showToast("Projeto apagado com sucesso.", "success");
    }
  }
  
  function openUploadModal() {
    showUploadModal.value = true;
  }
  
  // === LÓGICA DE CRÉDITOS LINKADA AQUI ===
  async function createNewGrid() {
    if (!uploadFile.value) {
      showToast("Selecione uma imagem primeiro!", "warning");
      return;
    }
  
    uploadLoading.value = true;
    try {
      const user = userProfile.value;
      if (!user) throw new Error("Sessão expirada. Entre novamente.");
  
      // 1. CONSUMIR CRÉDITO NO BACKEND
      // Chamamos a mesma rota usada na HomeView para garantir que o saldo seja reduzido
      const res = await fetch(`${API_BASE}/api/consume-credit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id }),
      });
  
      if (!res.ok) {
        if (res.status === 402) {
          showToast("Seus créditos acabaram!", "warning");
          setTimeout(() => router.push("/buy-credits"), 1500);
        } else {
          const errorMsg = await res.text();
          showToast("Erro ao validar créditos: " + errorMsg, "error");
        }
        return; // Interrompe o processo se não houver crédito
      }
  
      // Notifica outros componentes que o saldo mudou
      eventBus.dispatchEvent(new Event("credits-updated"));
  
      // 2. PROCESSO NORMAL (Sessão -> Upload -> Grade)
      await createSession();
      await uploadImage(uploadFile.value);
      await generateGrid();
  
      showToast("Sucesso! Processando...", "success");
      router.push("/editor");
    } catch (e) {
      showToast("Erro ao criar grade: " + e.message, "error");
    } finally {
      uploadLoading.value = false;
      showUploadModal.value = false;
      uploadFile.value = null;
    }
  }
  
  function onFileChange(e) {
    uploadFile.value = e.target.files[0];
  }
  </script>
  
  <template>
    <div class="dashboard-page">
      <header class="dash-header">
        <div class="header-inner">
          <h1>
            Olá, <span class="gradient-text">{{ firstName }}</span>
          </h1>
          <p class="subtitle">Sua coleção ({{ projects.length }})</p>
        </div>
      </header>
  
      <main class="content-scroll-area">
        <div class="content-inner">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
          </div>
  
          <div v-else class="projects-grid">
            <div class="card create-card" @click="openUploadModal">
              <div class="icon-circle"><span class="plus">+</span></div>
              <span class="create-label">Novo</span>
            </div>
  
            <div
              v-for="p in projects"
              :key="p.id"
              class="card project-card"
              @click="openProject(p)"
            >
              <div
                class="card-thumb"
                :style="{ backgroundImage: `url(${p.image_url})` }"
                crossorigin="anonymous"
              >
                <div class="overlay"><span>✏️</span></div>
              </div>
              <div class="card-info">
                <h3>{{ p.name }}</h3>
                <button @click.stop="deleteProject(p.id)" class="btn-icon">
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
  
      <div
        v-if="showUploadModal"
        class="modal-overlay"
        @click="showUploadModal = false"
      >
        <div class="modal-content" @click.stop>
          <h2>Nova Grade</h2>
          <p class="credit-warning">
            <strong>Atenção:</strong> 1 crédito será gasto ao gerar a grade.
            <br />
            <span v-if="hasFreeGeneration" class="free-note"
              >Você tem 1 geração grátis disponível!</span
            >
            <span v-else class="credits-note"
              >Créditos atuais: {{ currentCredits }}</span
            >
          </p>
  
          <div class="upload-area">
            <input
              type="file"
              accept="image/*"
              @change="onFileChange"
              id="file-input"
            />
            <label for="file-input" class="upload-label">
              <span v-if="!uploadFile">Clique para selecionar imagem</span>
              <span v-else>{{ uploadFile.name }}</span>
            </label>
          </div>
  
          <div class="modal-actions">
            <button @click="showUploadModal = false" class="btn-cancel">
              Cancelar
            </button>
            <button
              @click="createNewGrid"
              :disabled="uploadLoading || !uploadFile"
              class="btn-create"
            >
              <span v-if="uploadLoading" class="spinner-small"></span>
              <span v-else>Criar Grade</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <style scoped>
  /* Estilos mantidos conforme o seu Dashboard anterior */
  .dashboard-page { flex: 1; display: flex; flex-direction: column; background-color: #121212; color: #ecf0f1; overflow: hidden; }
  .dash-header { background: #181818; border-bottom: 1px solid #333; padding: 15px 30px; flex-shrink: 0; }
  .header-inner { max-width: 1400px; margin: 0 auto; display: flex; align-items: baseline; gap: 15px; }
  .dash-header h1 { font-size: 1.5rem; margin: 0; font-weight: 700; }
  .subtitle { color: #666; font-size: 0.9rem; margin: 0; }
  .gradient-text { background: linear-gradient(to right, #e67e22, #f1c40f); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .content-scroll-area { flex: 1; overflow-y: auto; padding: 20px 30px; }
  .content-inner { max-width: 1400px; margin: 0 auto; }
  .projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; }
  .card { background: #1e1e1e; border-radius: 12px; overflow: hidden; cursor: pointer; transition: all 0.2s; border: 1px solid #333; position: relative; display: flex; flex-direction: column; }
  .card:hover { transform: translateY(-3px); border-color: #555; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3); }
  .create-card { background: rgba(255, 255, 255, 0.03); border: 2px dashed #444; align-items: center; justify-content: center; min-height: 180px; }
  .create-card:hover { border-color: #e67e22; background: rgba(230, 126, 34, 0.05); }
  .icon-circle { width: 40px; height: 40px; border-radius: 50%; background: #252526; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; border: 1px solid #444; }
  .plus { font-size: 1.5rem; color: #aaa; margin-top: -3px; }
  .create-label { font-weight: bold; color: #888; font-size: 0.85rem; }
  .project-card { min-height: 180px; }
  .card-thumb { flex: 1; background-size: cover; background-position: center; background-color: #000; position: relative; }
  .overlay { position: absolute; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; opacity: 0; transition: 0.2s; }
  .card:hover .overlay { opacity: 1; }
  .card-info { padding: 10px; background: #252526; border-top: 1px solid #333; display: flex; justify-content: space-between; align-items: center; height: 40px; box-sizing: border-box; }
  .card-info h3 { margin: 0; font-size: 0.85rem; color: #ddd; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100px; }
  .btn-icon { background: transparent; border: none; color: #666; cursor: pointer; font-size: 1.1rem; padding: 0 5px; }
  .btn-icon:hover { color: #e74c3c; }
  .loading-state { text-align: center; margin-top: 50px; }
  .spinner { width: 30px; height: 30px; border: 3px solid rgba(255, 255, 255, 0.1); border-top-color: #e67e22; border-radius: 50%; animation: spin 1s infinite linear; margin: 0 auto; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .content-scroll-area::-webkit-scrollbar { width: 6px; }
  .content-scroll-area::-webkit-scrollbar-track { background: transparent; }
  .content-scroll-area::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
  .content-scroll-area::-webkit-scrollbar-thumb:hover { background: #444; }
  
  @media (max-width: 600px) {
    .projects-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
    .content-scroll-area { padding: 15px; }
  }
  
  /* PAINEL FLUTUANTE */
  .modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.8); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(5px); }
  .modal-content { background: #252526; padding: 30px; border-radius: 16px; width: 90%; max-width: 500px; text-align: center; border: 1px solid #444; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6); }
  .modal-content h2 { margin: 0 0 20px 0; color: white; font-size: 1.8rem; }
  .credit-warning { background: rgba(230, 126, 34, 0.2); border: 1px solid #e67e22; padding: 15px; border-radius: 12px; margin-bottom: 25px; color: #f1c40f; font-size: 1rem; }
  .free-note { display: block; margin-top: 8px; color: #27ae60; font-weight: bold; }
  .credits-note { display: block; margin-top: 8px; color: #ccc; }
  .upload-area { margin-bottom: 30px; }
  #file-input { display: none; }
  .upload-label { display: block; padding: 30px; border: 2px dashed #e67e22; border-radius: 12px; background: rgba(230, 126, 34, 0.1); color: #e67e22; font-size: 1.1rem; cursor: pointer; transition: all 0.2s; }
  .upload-label:hover { background: rgba(230, 126, 34, 0.2); border-color: #f39c12; }
  .modal-actions { display: flex; gap: 15px; justify-content: center; }
  .btn-cancel { padding: 12px 30px; background: transparent; border: 1px solid #666; color: #aaa; border-radius: 8px; cursor: pointer; }
  .btn-cancel:hover { background: rgba(255, 255, 255, 0.1); color: white; }
  .btn-create { padding: 12px 30px; background: #e67e22; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; display: flex; align-items: center; gap: 8px; }
  .btn-create:hover:not(:disabled) { background: #d35400; }
  .btn-create:disabled { opacity: 0.6; cursor: not-allowed; }
  .spinner-small { width: 18px; height: 18px; border: 2px solid rgba(255, 255, 255, 0.3); border-top-color: white; border-radius: 50%; animation: spin 1s infinite linear; }
  </style>