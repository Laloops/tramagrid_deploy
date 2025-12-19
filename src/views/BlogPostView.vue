<script setup>
    import { ref, onMounted } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { API_BASE } from '../api';
    import { 
      ArrowLeft, Calendar, Share2, 
      Twitter, Facebook, Linkedin, X 
    } from 'lucide-vue-next';
    
    const route = useRoute();
    const router = useRouter();
    const post = ref(null);
    const loading = ref(true);
    
    onMounted(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/posts/${route.params.slug}`);
        if(!res.ok) throw new Error("404");
        post.value = await res.json();
      } catch (e) {
        router.push('/blog'); 
      } finally {
        loading.value = false;
      }
    });
    
    function formatDate(dateStr) {
      if(!dateStr) return '';
      return new Date(dateStr).toLocaleDateString('pt-BR', { 
        day: 'numeric', month: 'long', year: 'numeric' 
      });
    }
    </script>
    
    <template>
      <div class="page-wrapper">
        
        <nav class="post-nav">
          <div class="nav-content">
            <button @click="router.push('/blog')" class="back-link">
              <ArrowLeft :size="20"/> <span class="hide-mobile">Voltar para o Blog</span>
            </button>
            <div class="brand-mini">TRAMA<span class="highlight">GRID</span></div>
            <button class="share-btn-mini"><Share2 :size="18"/></button>
          </div>
        </nav>
    
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
        </div>
    
        <div v-else-if="post" class="main-scroll-area">
          <div class="layout-grid">
            
            <aside class="sidebar left-sidebar">
              <div class="ad-sticky-container">
                <div class="ad-slot half-page">
                  <span class="ad-label">Publicidade</span>
                  <div class="ad-mockup">
                    <span>300x600</span>
                    <small>High Impact</small>
                  </div>
                </div>
              </div>
            </aside>
    
            <main class="article-container">
              
              <header class="article-header">
                <div class="meta-top">
                  <span class="category-tag">Tutorial</span>
                  <span class="dot">•</span>
                  <span class="date"><Calendar :size="14"/> {{ formatDate(post.created_at) }}</span>
                </div>
                
                <h1 class="title">{{ post.title }}</h1>
                
                <div class="author-row">
                  <div class="avatar-placeholder">TG</div>
                  <div class="author-info">
                    <span class="name">Equipe TramaGrid</span>
                    <span class="role">Pixel Art Expert</span>
                  </div>
                </div>
              </header>
    
              <figure class="hero-image-wrapper">
                <img :src="post.image_url" :alt="post.title" class="hero-image" />
              </figure>
    
              <article class="content-body" v-html="post.content"></article>
    
              <div class="ad-mobile-slot">
                 <span class="ad-label">Patrocinado</span>
                 <div class="ad-mockup mobile">300x250</div>
              </div>
    
              <div class="article-footer">
                <div class="share-cta">
                  <h3>Gostou? Compartilhe essa ideia.</h3>
                  <div class="share-icons">
                    <button class="s-btn tw"><Twitter :size="20"/></button>
                    <button class="s-btn fb"><Facebook :size="20"/></button>
                    <button class="s-btn in"><Linkedin :size="20"/></button>
                  </div>
                </div>
              </div>
    
            </main>
    
            <aside class="sidebar right-sidebar">
              <div class="ad-sticky-container">
                <div class="ad-slot half-page">
                  <span class="ad-label">Patrocinado</span>
                  <div class="ad-mockup">
                    <span>300x600</span>
                    <small>Sticky Ad</small>
                  </div>
                </div>
                
                <div class="promo-box">
                  <h3>Faça igual!</h3>
                  <p>Crie sua própria receita agora.</p>
                  <button @click="router.push('/login')">Testar Grátis</button>
                </div>
              </div>
            </aside>
    
          </div>
        </div>
      </div>
    </template>
    
    <style scoped>
    /* ================= CORREÇÃO DO SCROLL ================= */
    .page-wrapper {
      background-color: #050505;
      color: #e0e0e0;
      height: 100vh; /* Ocupa a tela toda */
      width: 100vw;
      overflow-y: auto; /* FORÇA A BARRA DE ROLAGEM AQUI */
      overflow-x: hidden;
      font-family: 'Inter', sans-serif;
      scroll-behavior: smooth;
    }
    
    /* ================= NAV ================= */
    .post-nav {
      position: sticky; top: 0; z-index: 100;
      background: rgba(5, 5, 5, 0.9); backdrop-filter: blur(12px);
      border-bottom: 1px solid #222; padding: 12px 0;
    }
    .nav-content {
      max-width: 1400px; margin: 0 auto; padding: 0 20px;
      display: flex; justify-content: space-between; align-items: center;
    }
    .back-link {
      background: none; border: none; color: #888; font-weight: 500;
      display: flex; align-items: center; gap: 8px; cursor: pointer; transition: 0.2s;
    }
    .back-link:hover { color: #e67e22; }
    .brand-mini { font-weight: 800; color: #fff; letter-spacing: 1px; }
    .highlight { color: #e67e22; }
    .share-btn-mini { background: none; border: 1px solid #333; color: #888; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
    
    /* ================= GRID DE LUCRO (3 COLUNAS) ================= */
    .main-scroll-area { padding-bottom: 80px; }
    .layout-grid {
      display: grid;
      /* 300px (Anuncio) | Flexível (Texto) | 300px (Anuncio) */
      grid-template-columns: 300px minmax(600px, 800px) 300px;
      gap: 40px;
      max-width: 1500px; margin: 0 auto; padding: 40px 20px;
      justify-content: center;
    }
    
    /* ================= ANÚNCIOS (SIDEBARS) ================= */
    .sidebar { display: block; height: 100%; }
    .ad-sticky-container {
      position: sticky; top: 100px; /* Faz o anúncio acompanhar o scroll */
      display: flex; flex-direction: column; gap: 20px;
    }
    
    .ad-slot {
      background: #111; border: 1px solid #222; border-radius: 4px;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      position: relative; overflow: hidden;
    }
    
    /* O Formato Rentável (300x600) */
    .half-page { width: 300px; height: 600px; }
    
    .ad-label {
      position: absolute; top: 5px; right: 5px; 
      font-size: 0.6rem; color: #444; text-transform: uppercase; letter-spacing: 1px;
    }
    .ad-mockup { color: #333; font-weight: 700; text-align: center; display: flex; flex-direction: column; }
    .ad-mockup small { font-weight: 400; color: #e67e22; margin-top: 5px; }
    
    /* Box Produto Próprio */
    .promo-box {
      background: linear-gradient(135deg, #1a1a1a, #000);
      border: 1px solid #333; border-radius: 8px; padding: 25px; text-align: center;
      width: 250px;
    }
    .promo-box h3 { color: white; margin-bottom: 8px; font-size: 1.1rem; }
    .promo-box p { font-size: 0.9rem; color: #999; margin-bottom: 20px; }
    .promo-box button {
      background: #e67e22; color: white; border: none; width: 100%; padding: 12px; 
      border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s;
      box-shadow: 0 4px 15px rgba(230, 126, 34, 0.2);
    }
    .promo-box button:hover { background: #d35400; transform: translateY(-2px); }
    
    /* ================= ARTIGO ================= */
    .article-container { width: 100%; }
    
    .meta-top { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; font-size: 0.85rem; color: #888; }
    .category-tag { color: #e67e22; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
    .dot { color: #333; }
    .date { display: flex; align-items: center; gap: 6px; }
    
    .title { 
      font-size: clamp(2.5rem, 5vw, 3.5rem); 
      font-weight: 800; line-height: 1.1; color: white; margin-bottom: 30px; letter-spacing: -1px;
    }
    
    .author-row { display: flex; align-items: center; gap: 15px; border-top: 1px solid #222; padding-top: 25px; margin-bottom: 40px; }
    .avatar-placeholder { width: 40px; height: 40px; background: #222; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #666; font-size: 0.8rem; }
    .name { color: white; font-weight: 600; font-size: 0.9rem; display: block; }
    .role { color: #666; font-size: 0.8rem; }
    
    .hero-image-wrapper { margin: 0 0 50px 0; border-radius: 12px; overflow: hidden; border: 1px solid #222; }
    .hero-image { width: 100%; height: auto; display: block; max-height: 550px; object-fit: cover; }
    
    /* TIPOGRAFIA DO TEXTO */
    .content-body {
      font-size: 1.25rem; line-height: 1.8; color: #d0d0d0; font-weight: 300;
    }
    :deep(p) { margin-bottom: 32px; }
    :deep(h2) { font-size: 2rem; color: white; margin: 60px 0 25px 0; font-weight: 700; border-bottom: 1px solid #222; padding-bottom: 15px; }
    :deep(a) { color: #e67e22; text-decoration: none; border-bottom: 1px solid rgba(230, 126, 34, 0.4); }
    :deep(img) { width: 100%; border-radius: 8px; margin: 30px 0; border: 1px solid #222; }
    :deep(blockquote) { border-left: 4px solid #e67e22; padding: 20px 40px; background: #0f0f0f; font-style: italic; color: #bbb; margin: 40px 0; border-radius: 0 8px 8px 0; }
    
    /* FOOTER / SHARE */
    .article-footer { margin-top: 80px; padding: 40px; background: #0f0f0f; border-radius: 12px; border: 1px solid #222; text-align: center; }
    .share-cta h3 { color: white; margin-bottom: 20px; font-size: 1.2rem; }
    .share-icons { display: flex; justify-content: center; gap: 15px; }
    .s-btn { width: 50px; height: 50px; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: white; transition: 0.3s; }
    .s-btn:hover { transform: translateY(-5px); }
    .tw { background: #1da1f2; } .fb { background: #1877f2; } .in { background: #0077b5; }
    
    /* MOBILE ADS */
    .ad-mobile-slot { display: none; margin: 40px 0; text-align: center; background: #111; padding: 20px; border: 1px dashed #333; }
    .ad-mockup.mobile { width: 300px; height: 250px; margin: 0 auto; line-height: 250px; background: #000; border: 1px solid #222; color: #444; font-weight: bold; }
    
    /* ================= RESPONSIVO ================= */
    @media (max-width: 1400px) {
      /* Em telas médias (laptops), esconde uma lateral ou reduz */
      .layout-grid { grid-template-columns: 1fr 300px; max-width: 1000px; }
      .left-sidebar { display: none; } /* Esconde esquerda, mantém direita */
    }
    
    @media (max-width: 1000px) {
      /* Tablet/Mobile */
      .layout-grid { grid-template-columns: 1fr; max-width: 700px; }
      .sidebar { display: none; } /* Esconde todas as laterais */
      .ad-mobile-slot { display: block; } /* Mostra anúncio dentro do texto */
      .nav-content { padding: 0 15px; }
      .hide-mobile { display: none; }
      .title { font-size: 2.2rem; }
    }
    </style>