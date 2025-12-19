<script setup>
    import { ref, onMounted } from 'vue';
    import { API_BASE } from '../api';
    import { useRouter } from 'vue-router';
    import { 
      LayoutDashboard, FileText, Users, Settings, 
      Bold, Italic, Link as IconLink, Image as IconImage, 
      Youtube, Trash2, LogOut, Eye, Key, Layers 
    } from 'lucide-vue-next';
    
    const router = useRouter();
    const currentTab = ref('dashboard'); // 'dashboard', 'posts', 'settings'
    
    // DADOS REAIS DO DASHBOARD
    const stats = ref({ 
      total_users: 0, 
      total_projects: 0, 
      daily_visits: 0, 
      daily_logins: 0 
    });
    
    const posts = ref([]);
    
    // Editor State
    const isEditing = ref(false); 
    const form = ref({ title: '', slug: '', image_url: '', excerpt: '', content: '', published: true });
    const textAreaRef = ref(null);
    
    // --- BUSCAR DADOS (FETCH) ---
    async function fetchStats() {
      try {
        const res = await fetch(`${API_BASE}/api/admin/stats`);
        if(res.ok) {
          stats.value = await res.json();
        }
      } catch(e) { console.error("Erro ao carregar stats:", e); }
    }
    
    async function fetchPosts() {
      try {
        const res = await fetch(`${API_BASE}/api/posts`);
        if(res.ok) posts.value = await res.json();
      } catch(e) { console.error(e); }
    }
    
    onMounted(() => {
      fetchStats();
      fetchPosts();
    });
    
    // --- LÓGICA DO EDITOR RICO (Mantida igual) ---
    function insertTag(tag, value = null) {
      const textarea = textAreaRef.value;
      if (!textarea) return;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = form.value.content;
      const before = text.substring(0, start);
      const selection = text.substring(start, end);
      const after = text.substring(end);
      let insertion = '';
      
      if (tag === 'b') insertion = `<b>${selection || 'texto negrito'}</b>`;
      else if (tag === 'i') insertion = `<i>${selection || 'texto itálico'}</i>`;
      else if (tag === 'a') {
        const url = prompt("URL do Link:", "https://");
        if(url) insertion = `<a href="${url}" target="_blank">${selection || 'link aqui'}</a>`;
      }
      else if (tag === 'img') {
        const url = prompt("URL da Imagem:", "https://");
        if(url) insertion = `<img src="${url}" alt="Imagem" style="width:100%; border-radius:8px; margin: 20px 0;" />`;
      }
      else if (tag === 'yt') {
        const code = prompt("ID do Vídeo YouTube:", "");
        if(code) insertion = `<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:20px 0;"><iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:8px;" src="https://www.youtube.com/embed/${code}" frameborder="0" allowfullscreen></iframe></div>`;
      }
    
      if (insertion) {
        form.value.content = before + insertion + after;
        setTimeout(() => {
          textarea.focus();
          textarea.selectionStart = textarea.selectionEnd = start + insertion.length;
        }, 0);
      }
    }
    
    // --- CRUD POSTS (Mantido igual) ---
    function generateSlug() {
      form.value.slug = form.value.title.toLowerCase().replace(/ /g, '-').replace(/[^\w-]+/g, '');
    }
    
    async function submitPost() {
      if(!form.value.title || !form.value.content) return alert("Preencha título e conteúdo!");
      try {
        const res = await fetch(`${API_BASE}/api/posts`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form.value)
        });
        if(res.ok) {
          alert("Post Publicado!");
          closeEditor();
          fetchPosts();
        }
      } catch(e) { console.error(e); }
    }
    
    async function deletePost(id) {
      if(!confirm("Apagar post?")) return;
      await fetch(`${API_BASE}/api/posts/${id}`, { method: "DELETE" });
      fetchPosts();
    }
    
    function openNewPost() {
      form.value = { title: '', slug: '', image_url: '', excerpt: '', content: '', published: true };
      isEditing.value = true;
    }
    function closeEditor() { isEditing.value = false; }
    </script>
    
    <template>
      <div class="admin-layout">
        
        <header class="topbar">
          <div class="logo">TRAMA<span class="highlight">ADMIN</span></div>
          
          <nav class="tabs">
            <button :class="{ active: currentTab === 'dashboard' }" @click="currentTab = 'dashboard'">
              <LayoutDashboard :size="18" /> Dashboard
            </button>
            <button :class="{ active: currentTab === 'posts' }" @click="currentTab = 'posts'">
              <FileText :size="18" /> Blog Posts
            </button>
            <button :class="{ active: currentTab === 'settings' }" @click="currentTab = 'settings'">
              <Settings :size="18" /> Config
            </button>
          </nav>
    
          <button @click="router.push('/')" class="btn-logout">
            <LogOut :size="18" /> Sair
          </button>
        </header>
    
        <main class="content-area">
          
          <div v-if="currentTab === 'dashboard'" class="dashboard-view fade-in">
            <div class="stats-grid">
              
              <div class="stat-card">
                <div class="stat-icon ico-blue"><Eye :size="24" /></div>
                <div class="stat-info">
                  <span class="stat-value">{{ stats.daily_visits }}</span>
                  <span class="stat-label">Visitas Hoje</span>
                </div>
              </div>
    
              <div class="stat-card">
                <div class="stat-icon ico-green"><Key :size="24" /></div>
                <div class="stat-info">
                  <span class="stat-value">{{ stats.daily_logins }}</span>
                  <span class="stat-label">Logins Hoje</span>
                </div>
              </div>
    
              <div class="stat-card">
                <div class="stat-icon ico-orange"><Layers :size="24" /></div>
                <div class="stat-info">
                  <span class="stat-value">{{ stats.total_projects }}</span>
                  <span class="stat-label">Projetos Totais</span>
                </div>
              </div>
    
              <div class="stat-card">
                <div class="stat-icon ico-purple"><Users :size="24" /></div>
                <div class="stat-info">
                  <span class="stat-value">{{ stats.total_users }}</span>
                  <span class="stat-label">Usuários Cadastrados</span>
                </div>
              </div>
    
            </div>
    
            <div class="dash-placeholder">
              <h3>Gráficos de Desempenho</h3>
              <p>Dados de visitas e logins sendo coletados em tempo real.</p>
            </div>
          </div>
    
          <div v-if="currentTab === 'posts'" class="posts-view fade-in">
            <div v-if="!isEditing" class="list-mode">
              <div class="list-header">
                <h2>Publicações ({{ posts.length }})</h2>
                <button class="btn-primary" @click="openNewPost">+ Novo Artigo</button>
              </div>
              <div class="posts-table-wrapper">
                <table class="posts-table">
                  <thead>
                    <tr>
                      <th>Título</th>
                      <th>Data</th>
                      <th>Status</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in posts" :key="p.id">
                      <td>{{ p.title }}</td>
                      <td>{{ new Date(p.created_at).toLocaleDateString() }}</td>
                      <td><span class="badge-pub">Publicado</span></td>
                      <td>
                        <button class="btn-icon delete" @click="deletePost(p.id)"><Trash2 :size="16"/></button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
    
            <div v-else class="editor-mode">
              <div class="editor-header">
                <button class="btn-text" @click="closeEditor">← Voltar</button>
                <h2>Criar Nova Publicação</h2>
                <button class="btn-primary" @click="submitPost">Publicar</button>
              </div>
    
              <div class="editor-grid">
                <div class="meta-col">
                  <label>Título</label>
                  <input v-model="form.title" @input="generateSlug" placeholder="Título do Post" />
                  <label>Slug (URL)</label>
                  <input v-model="form.slug" disabled />
                  <label>Capa (URL)</label>
                  <input v-model="form.image_url" placeholder="https://..." />
                  <label>Resumo</label>
                  <textarea v-model="form.excerpt" rows="4" placeholder="Breve descrição..."></textarea>
                </div>
    
                <div class="content-col">
                  <label>Conteúdo</label>
                  <div class="toolbar">
                    <button @click="insertTag('b')" title="Negrito"><Bold :size="16"/></button>
                    <button @click="insertTag('i')" title="Itálico"><Italic :size="16"/></button>
                    <button @click="insertTag('a')" title="Link"><IconLink :size="16"/></button>
                    <div class="sep"></div>
                    <button @click="insertTag('img')" title="Imagem"><IconImage :size="16"/></button>
                    <button @click="insertTag('yt')" title="Vídeo YouTube"><Youtube :size="16"/></button>
                  </div>
                  <textarea ref="textAreaRef" v-model="form.content" class="main-editor" placeholder="Escreva seu artigo aqui..."></textarea>
                </div>
              </div>
            </div>
          </div>
    
          <div v-if="currentTab === 'settings'" class="settings-view fade-in">
            <h2>Configurações</h2>
            <p style="color:#666">Em breve: Gerenciamento de planos e usuários.</p>
          </div>
    
        </main>
      </div>
    </template>
    
    <style scoped>
    /* ESTILOS MANTIDOS IDÊNTICOS */
    .admin-layout { min-height: 100vh; background: #080808; color: #eee; display: flex; flex-direction: column; }
    .topbar { background: #111; border-bottom: 1px solid #222; height: 60px; display: flex; align-items: center; justify-content: space-between; padding: 0 30px; position: sticky; top: 0; z-index: 100; }
    .logo { font-weight: 800; font-size: 1.1rem; }
    .highlight { color: #e67e22; }
    .tabs { display: flex; gap: 5px; height: 100%; }
    .tabs button { background: transparent; border: none; color: #888; height: 100%; padding: 0 20px; cursor: pointer; display: flex; align-items: center; gap: 8px; font-weight: 500; border-bottom: 2px solid transparent; transition: 0.2s; }
    .tabs button:hover { color: white; background: #1a1a1a; }
    .tabs button.active { color: #e67e22; border-bottom-color: #e67e22; background: rgba(230,126,34,0.05); }
    .btn-logout { background: none; border: 1px solid #333; color: #aaa; padding: 6px 12px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 0.8rem; }
    .btn-logout:hover { border-color: #555; color: white; }
    .content-area { padding: 30px; max-width: 1200px; margin: 0 auto; width: 100%; }
    
    /* DASHBOARD STATS */
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
    .stat-card { background: #111; border: 1px solid #222; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 20px; }
    .stat-icon { width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; }
    .ico-blue { background: rgba(52, 152, 219, 0.2); color: #3498db; }
    .ico-green { background: rgba(46, 204, 113, 0.2); color: #2ecc71; }
    .ico-orange { background: rgba(230, 126, 34, 0.2); color: #e67e22; }
    .ico-purple { background: rgba(155, 89, 182, 0.2); color: #9b59b6; }
    .stat-value { font-size: 1.8rem; font-weight: 800; display: block; line-height: 1; margin-bottom: 5px; }
    .stat-label { font-size: 0.85rem; color: #888; }
    .dash-placeholder { border: 2px dashed #222; padding: 40px; text-align: center; border-radius: 12px; color: #444; }
    
    /* POSTS */
    .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .btn-primary { background: #e67e22; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; }
    .posts-table-wrapper { background: #111; border-radius: 12px; border: 1px solid #222; overflow: hidden; }
    .posts-table { width: 100%; border-collapse: collapse; }
    .posts-table th, .posts-table td { padding: 15px 20px; text-align: left; border-bottom: 1px solid #222; }
    .posts-table th { background: #161616; color: #888; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; }
    .badge-pub { background: rgba(39, 174, 96, 0.2); color: #2ecc71; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; }
    .btn-icon.delete { background: rgba(231, 76, 60, 0.1); color: #e74c3c; border: none; width: 32px; height: 32px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    
    /* EDITOR */
    .editor-header { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
    .btn-text { background: none; border: none; color: #888; cursor: pointer; font-size: 1rem; }
    .editor-grid { display: grid; grid-template-columns: 1fr 2fr; gap: 30px; }
    .meta-col, .content-col { display: flex; flex-direction: column; gap: 15px; }
    input, textarea { background: #000; border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%; outline: none; }
    input:focus, textarea:focus { border-color: #e67e22; }
    label { font-size: 0.85rem; color: #888; font-weight: 600; }
    .toolbar { background: #161616; border: 1px solid #333; border-bottom: none; border-radius: 8px 8px 0 0; padding: 8px; display: flex; gap: 5px; }
    .toolbar button { width: 32px; height: 32px; background: #222; border: 1px solid #333; color: #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    .sep { width: 1px; background: #444; margin: 0 5px; }
    .main-editor { border-top-left-radius: 0; border-top-right-radius: 0; height: 500px; font-family: monospace; line-height: 1.5; resize: vertical; }
    
    .fade-in { animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>