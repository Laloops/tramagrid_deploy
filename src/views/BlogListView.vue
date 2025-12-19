<script setup>
    import { ref, onMounted, computed } from 'vue';
    import { useRouter } from 'vue-router';
    import { API_BASE } from '../api';
    import { BookOpen, ArrowRight, Calendar } from 'lucide-vue-next';
    
    const posts = ref([]);
    const loading = ref(true);
    const router = useRouter();
    
    onMounted(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/posts`);
        if(res.ok) posts.value = await res.json();
      } catch (e) {
        console.error(e);
      } finally {
        loading.value = false;
      }
    });
    
    // Lógica de posts
    const featuredPost = computed(() => posts.value.length > 0 ? posts.value[0] : null);
    const gridPosts = computed(() => posts.value.length > 0 ? posts.value.slice(1) : []);
    
    function formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
    }
    </script>
    
    <template>
      <div class="blog-wrapper">
        
        <header class="blog-header">
          <div class="header-content">
            <div class="brand" @click="router.push('/')">TRAMA<span class="highlight">GRID</span></div>
            <h1>Blog & Tutoriais</h1>
            <p>Inspiração, dicas técnicas e novidades do mundo do pixel art têxtil.</p>
          </div>
        </header>
    
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Carregando ideias...</p>
        </div>
    
        <div v-else class="content-container">
          
          <main class="main-column">
            
            <section v-if="featuredPost" class="featured-section" @click="router.push(`/blog/${featuredPost.slug}`)">
              <div class="featured-card">
                <div class="featured-image" :style="{ backgroundImage: `url(${featuredPost.image_url})` }"></div>
                <div class="featured-info">
                  <span class="tag">Destaque</span>
                  <h2>{{ featuredPost.title }}</h2>
                  <p>{{ featuredPost.excerpt }}</p>
                  <div class="meta">
                    <span><Calendar :size="14"/> {{ formatDate(featuredPost.created_at) }}</span>
                    <span class="read-btn">Ler <ArrowRight :size="16"/></span>
                  </div>
                </div>
              </div>
            </section>
    
            <div class="ad-mobile-banner">
              <span class="ad-label">Patrocinado</span>
              <div class="ad-mockup-mobile">320x100</div>
            </div>
    
            <section v-if="gridPosts.length > 0" class="posts-grid">
              <article 
                v-for="post in gridPosts" 
                :key="post.id" 
                class="post-card" 
                @click="router.push(`/blog/${post.slug}`)"
              >
                <div class="card-image-wrap">
                  <div class="card-image" :style="{ backgroundImage: `url(${post.image_url})` }"></div>
                </div>
                <div class="card-content">
                  <span class="date">{{ formatDate(post.created_at) }}</span>
                  <h3>{{ post.title }}</h3>
                  <p>{{ post.excerpt.substring(0, 80) }}...</p>
                  <div class="card-footer">Ler mais</div>
                </div>
              </article>
            </section>
    
            <div v-else-if="!featuredPost" class="empty-state">
              <BookOpen :size="48" color="#333" />
              <p>Ainda não temos publicações.</p>
            </div>
          </main>
    
          <aside class="blog-sidebar">
            <div class="sticky-wrapper">
              
              <div class="ad-slot large">
                <span class="ad-label">Publicidade</span>
                <div class="ad-mockup">
                  <span>300x600</span>
                  <small>Half Page Ad</small>
                </div>
              </div>
    
              <div class="promo-box">
                <h3>Quer criar o seu?</h3>
                <p>Use nosso conversor de imagens.</p>
                <button @click="router.push('/login')">Começar Grátis</button>
              </div>
    
            </div>
          </aside>
    
        </div>
    
        <footer class="blog-footer">
          <p>© 2025 TramaGrid Blog</p>
        </footer>
      </div>
    </template>
    
    <style scoped>
    /* ESTRUTURA GLOBAL */
    .blog-wrapper {
      min-height: 100vh;
      background-color: #050505;
      color: #e0e0e0;
      font-family: 'Inter', sans-serif;
      overflow-x: hidden;
    }
    
    /* HEADER */
    .blog-header {
      padding: 80px 20px 60px; text-align: center;
      background: radial-gradient(circle at top, #1a1a1a 0%, #050505 100%);
      border-bottom: 1px solid #111; margin-bottom: 40px;
    }
    .brand { font-weight: 900; letter-spacing: 2px; margin-bottom: 20px; cursor: pointer; display: inline-block; opacity: 0.7; transition: 0.3s; }
    .brand:hover { opacity: 1; }
    .highlight { color: #e67e22; }
    .blog-header h1 { font-size: 3rem; font-weight: 800; margin-bottom: 15px; background: linear-gradient(to right, #fff, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .blog-header p { color: #888; font-size: 1.1rem; max-width: 600px; margin: 0 auto; }
    
    /* CONTAINER PRINCIPAL (GRID 2 COLUNAS) */
    .content-container {
      max-width: 1200px; margin: 0 auto; padding: 0 20px;
      display: grid;
      grid-template-columns: 1fr 300px; /* Conteúdo Flexível | Sidebar Fixa */
      gap: 40px;
      align-items: start; /* Importante para o sticky funcionar */
    }
    
    /* SIDEBAR & ADS */
    .blog-sidebar { height: 100%; display: block; }
    .sticky-wrapper { position: sticky; top: 40px; display: flex; flex-direction: column; gap: 30px; }
    
    .ad-slot {
      background: #0f0f0f; border: 1px solid #222; border-radius: 8px;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      position: relative; overflow: hidden;
    }
    .large { width: 300px; height: 600px; }
    .ad-label { position: absolute; top: 5px; right: 5px; font-size: 0.6rem; color: #444; text-transform: uppercase; letter-spacing: 1px; }
    .ad-mockup { color: #333; font-weight: 700; text-align: center; }
    .ad-mockup small { font-weight: 400; color: #e67e22; display: block; margin-top: 5px; }
    
    /* Promo Box */
    .promo-box { background: linear-gradient(135deg, #1a1a1a, #000); border: 1px solid #333; border-radius: 8px; padding: 25px; text-align: center; }
    .promo-box h3 { color: white; margin-bottom: 10px; }
    .promo-box p { font-size: 0.9rem; color: #999; margin-bottom: 20px; }
    .promo-box button { background: #e67e22; color: white; border: none; width: 100%; padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; }
    .promo-box button:hover { background: #d35400; }
    
    /* FEATURED POST */
    .featured-section { margin-bottom: 40px; }
    .featured-card {
      display: grid; grid-template-columns: 1.2fr 1fr;
      background: #0f0f0f; border: 1px solid #222; border-radius: 16px;
      overflow: hidden; cursor: pointer; transition: transform 0.3s, border-color 0.3s;
    }
    .featured-card:hover { transform: translateY(-5px); border-color: #e67e22; }
    .featured-image { background-size: cover; background-position: center; min-height: 300px; }
    .featured-info { padding: 30px; display: flex; flex-direction: column; justify-content: center; }
    .tag { background: #e67e22; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; width: fit-content; margin-bottom: 15px; }
    .featured-info h2 { font-size: 1.8rem; margin-bottom: 15px; line-height: 1.2; color: white; }
    .featured-info p { color: #aaa; margin-bottom: 20px; line-height: 1.5; font-size: 0.95rem; }
    .meta { display: flex; align-items: center; gap: 20px; font-size: 0.85rem; color: #666; margin-top: auto; }
    .read-btn { color: #e67e22; font-weight: 600; display: flex; align-items: center; gap: 5px; }
    
    /* POSTS GRID */
    .posts-grid {
      display: grid; 
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); /* Ajustado para caber ao lado da sidebar */
      gap: 25px;
    }
    .post-card {
      background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px; overflow: hidden;
      cursor: pointer; transition: all 0.3s ease; display: flex; flex-direction: column;
    }
    .post-card:hover { transform: translateY(-5px); border-color: #444; }
    .card-image-wrap { height: 160px; overflow: hidden; }
    .card-image { width: 100%; height: 100%; background-size: cover; background-position: center; transition: transform 0.5s; }
    .post-card:hover .card-image { transform: scale(1.1); }
    .card-content { padding: 20px; flex: 1; display: flex; flex-direction: column; }
    .date { font-size: 0.75rem; color: #555; margin-bottom: 8px; display: block; }
    .post-card h3 { font-size: 1.1rem; margin-bottom: 10px; color: #ddd; line-height: 1.3; }
    .post-card:hover h3 { color: #e67e22; }
    .post-card p { font-size: 0.85rem; color: #888; line-height: 1.5; margin-bottom: 15px; flex: 1; }
    .card-footer { font-size: 0.85rem; font-weight: 600; color: #e67e22; margin-top: auto; }
    
    /* MOBILE ADS */
    .ad-mobile-banner { display: none; background: #111; margin: 0 0 30px 0; border: 1px dashed #333; padding: 10px; text-align: center; border-radius: 8px; }
    .ad-mockup-mobile { color: #444; font-weight: bold; }
    
    /* LOADING & FOOTER */
    .loading-state, .empty-state { text-align: center; padding: 100px 0; color: #555; }
    .spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #e67e22; border-radius: 50%; margin: 0 auto 20px; animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .blog-footer { text-align: center; padding: 40px; border-top: 1px solid #111; color: #444; margin-top: 60px; font-size: 0.9rem; }
    
    /* RESPONSIVO */
    @media (max-width: 1000px) {
      /* Em tablets/celulares, o layout vira uma coluna só */
      .content-container { grid-template-columns: 1fr; }
      .blog-sidebar { display: none; } /* Esconde sidebar lateral */
      .ad-mobile-banner { display: block; } /* Mostra banner horizontal */
      
      .featured-card { grid-template-columns: 1fr; }
      .featured-image { min-height: 200px; }
      .posts-grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
    }
    </style>