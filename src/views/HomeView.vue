<script setup>
  import { ref, onMounted, onUnmounted } from "vue";
  import { useRouter } from "vue-router";
  import { supabase } from "../supabase";
  import gsap from "gsap";
  import { 
    MessageCircle, X, Send, Instagram, 
    Linkedin, Twitter, BookOpen, LogIn 
  } from "lucide-vue-next"; 
  
  const router = useRouter();
  
  // =================================================================================
  // 1. ESTADO E LÓGICA
  // =================================================================================
  const isChatOpen = ref(false);
  const chatForm = ref({ name: '', email: '', message: '' });
  const isSending = ref(false);
  const contentLeft = ref(null); 
  const scrollY = ref(0); 
  const showFreeBadge = ref(false);
  const LOCAL_STORAGE_KEY = "tramagrid_anon_used";
  
  async function checkUserStatus() {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const { data: profile } = await supabase.from("profiles").select("free_generation_used").eq("id", user.id).maybeSingle();
      if (profile && !profile.free_generation_used) showFreeBadge.value = true;
    } else {
      if (!localStorage.getItem(LOCAL_STORAGE_KEY)) showFreeBadge.value = true;
    }
  }
  
  function toggleChat() { isChatOpen.value = !isChatOpen.value; }
  
  async function sendContactMessage() {
    if(!chatForm.value.message) return;
    isSending.value = true;
    await new Promise(r => setTimeout(r, 1500));
    alert("Mensagem enviada! Entraremos em contato em breve.");
    chatForm.value = { name: '', email: '', message: '' };
    isSending.value = false;
    isChatOpen.value = false;
  }
  
  // =================================================================================
  // 2. CANVAS BACKGROUND
  // =================================================================================
  const canvasRef = ref(null);
  let ctx = null, cw = 0, ch = 0, hue = 180;
  let cubes = [], nCubes = 0, staggerAnim = null;
  const img = new Image(); const img2 = new Image();
  const imgSrc1 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAADIBAMAAADsElnyAAAAJFBMVEVHcEw+Pj5aWloQEBAZGRleXl6AgIDAwMBwcHCampq7u7tzc3M0sGdFAAAABXRSTlMAp/UwQ5FLsO8AAADxSURBVHgB7c9HcQRhDITRn8NgMABDWAjO6ewMYLgsWef8akelk1Pr/upTj023mkZxiK3dqSsODnpmdXBwUBlEaRCYckdtEKVBYModmKbQKDrGHZpaaPyqZxQaRc8oNPVyTaehUVRGURhFYerlmu2D5k3jqimO1+MCU4h5XFzc9sQjaXTO1vMTobMkXgmdBfFKNnTY8UroLIp3YkfxldBhB4QOAkIHAaHDDggdBIQOX0HoICB0EBA6CAgdlkPoICB0+ApCBwGhw1cQOggIBgHh5pCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQH0XuAS5hV4q0a3iHAAAAAElFTkSuQmCC";
  const imgSrc2 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAADIBAMAAADsElnyAAAAJFBMVEVHcEylpaXv7+/Gxsa+vr7m5uahoaE/Pz9/f3+Ojo5lZWWCgoKkaSxxAAAABnRSTlMA9TCcskPTdr2ZAAAA40lEQVR4Ae3POW0EQQBE0UZhBEawWBaAzz0QDIVhYgxmZ3X6pFZpIl/18xf8sep8GinFwzMmi8sFk8TlctFkockiGz80WWiyyMYPTRbZKLLxIxtFMIoVwCCSUQSTRDaeZ3POAKPIRpGNIhvPs3m8HOw0Pg+K+8fYo0FsY48GMUkyiEmSQUySDGKSZBCTJIOYZG0QkIVBQDQKydogIBqFRKOQaBSQYBAQDAKCQQSCUUg0CAhmLSAYhUSDgCwMIpFpFJnsW0lJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUnJjyJfg4PNmR1hT+AAAAAASUVORK5CYII=";
  
  const Cube = function (index, _x, _y, _s) {
    this.img = img; this.img2 = img2; this.scale = _s; this.x = _x; this.y = _y; this.z = 0; this.img2_opacity = 0;
    this.draw = function () {
      if (!ctx) return;
      ctx.translate(this.x, this.y + this.z);
      ctx.drawImage(this.img, (-100/2)*this.scale, (-200/2)*this.scale, 100*this.scale, 200*this.scale);
      ctx.globalAlpha = this.img2_opacity;
      ctx.drawImage(this.img2, (-100/2)*this.scale, (-200/2)*this.scale, 100*this.scale, 200*this.scale);
      ctx.globalAlpha = 1;
      ctx.translate(-this.x, -(this.y + this.z));
    };
  };
  
  function setGrid() {
    if (!canvasRef.value) return;
    const c = canvasRef.value;
    c.width = window.innerWidth; c.height = window.innerHeight;
    cw = Math.ceil(c.width/100 + 1); ch = Math.floor(c.height/25 + 10);
    cubes = []; let i = 0;
    for (let _y = 0; _y < ch; _y++) {
      for (let _x = 0; _x < cw; _x++) {
        if (_y % 2 === 0) cubes.push(new Cube(i, -25+_x*100, -75+_y*25, 0.9));
        else cubes.push(new Cube(i, 25+_x*100, -75+_y*25, 0.9));
        i++;
      }
    }
    nCubes = cubes.length;
  }
  
  function staggerFrom(from) {
    return gsap.timeline()
      .to(cubes, { duration: 3, z: 30, ease: "sine.inOut", stagger: { yoyo: true, amount: 6, grid: [ch, cw], overwrite: "auto", from: from, onComplete: function () { gsap.to(this.targets(), { duration: 4, z: 0, ease: "sine.inOut" }); } } }, 0)
      .to(cubes, { duration: 1.5, img2_opacity: 0.5, stagger: { yoyo: true, amount: 6, grid: [ch, cw], overwrite: "auto", from: from, onComplete: function () { gsap.to(this.targets(), { duration: 2, img2_opacity: 0 }); } } }, 0);
  }
  
  function anim() { staggerAnim = gsap.timeline({ onComplete: anim, delay: 8 }).add(staggerFrom(gsap.utils.random(0, nCubes, 1))); }
  
  const renderLoop = () => {
    if (!ctx || !canvasRef.value) return;
    const c = canvasRef.value;
    ctx.clearRect(0, 0, c.width, c.height);
    ctx.globalCompositeOperation = "source-over";
    for (let i = 0; i < nCubes; i++) cubes[i].draw();
    hue -= 0.5;
    ctx.globalCompositeOperation = "lighter";
    ctx.fillStyle = "hsl(" + hue + ", 75%, 25%)";
    ctx.fillRect(0, 0, c.width, c.height);
  };
  
  const handleResize = () => setGrid();
  
  // =================================================================================
  // 3. LIFECYCLE
  // =================================================================================
  function handleScroll() {
    scrollY.value = window.scrollY;
  }
  
  onMounted(async () => {
    window.addEventListener("scroll", handleScroll);
    if (canvasRef.value) {
      ctx = canvasRef.value.getContext("2d");
      let loadedCount = 0;
      const checkLoad = () => {
        loadedCount++;
        if (loadedCount === 2) { setGrid(); gsap.ticker.add(renderLoop); gsap.delayedCall(0.2, anim); }
      };
      img.onload = checkLoad; img2.onload = checkLoad; img.src = imgSrc1; img2.src = imgSrc2;
      window.addEventListener("resize", handleResize);
    }
    await checkUserStatus();
    
    // Hero Animation
    gsap.timeline().from(contentLeft.value.children, { y: 40, opacity: 0, duration: 1.2, stagger: 0.2, ease: "power2.out" });
    
    // Cards Animation Trigger
    const cards = document.querySelectorAll('.info-card');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => { if(entry.isIntersecting) entry.target.classList.add('visible'); });
    }, { threshold: 0.2 });
    cards.forEach(c => observer.observe(c));
  });
  
  onUnmounted(() => {
    gsap.ticker.remove(renderLoop);
    window.removeEventListener("resize", handleResize);
    window.removeEventListener("scroll", handleScroll);
    gsap.killTweensOf(cubes);
    if (staggerAnim) staggerAnim.kill();
  });
  </script>
  
  <template>
    <div class="page-wrapper">
      
      <div class="fixed-bg">
        <canvas ref="canvasRef" class="c"></canvas>
        <div class="dark-overlay"></div>
      </div>
  
      <div class="scroll-content">
        
        <nav class="navbar" :class="{ 'scrolled': scrollY > 20 }">
          <div class="nav-inner">
            
            <div class="logo nav-logo" :class="{ 'visible': scrollY > 280 }">
              TRAMA<span class="highlight">GRID</span>
            </div>
  
            <div class="nav-links">
              <a href="#" @click.prevent="router.push('/blog')" class="nav-link">
                <BookOpen :size="16" /> <span class="nav-text">Blog</span>
              </a>
              <a href="#" @click.prevent="router.push('/login')" class="nav-btn-login">
                <LogIn :size="16" /> <span class="nav-text">Entrar</span>
              </a>
            </div>
          </div>
        </nav>
  
        <header class="hero-section">
          <div class="ui-overlay">
            <div ref="contentLeft" class="content-left" :style="{ transform: `translateY(${scrollY * 0.4}px)`, opacity: 1 - scrollY/700 }">
              <div v-if="showFreeBadge" class="badge-pill">🎁 1ª Geração Grátis</div>
              
              <h1 class="brand-title">TRAMA<span class="highlight">GRID</span></h1>
              
              <h2 class="hero-headline">Transforme imagens em <span class="text-gradient">PIXELS</span></h2>
              <p class="hero-description">
                Converta fotos em gráficos prontos para crochê, tricô ou pixel art. 
                Simplifique cores, edite a grade e baixe sua receita em segundos.
              </p>
              <div class="action-area">
                <button class="cta-btn-primary" @click="router.push('/login')">
                  <span>Teste agora &rarr;</span>
                </button>
              </div>
            </div>
          </div>
          
          <div class="scroll-hint" :style="{ opacity: 1 - scrollY/300 }">
            <div class="mouse-icon">
              <div class="wheel"></div>
            </div>
          </div>
        </header>
  
        <section class="info-section">
          <div class="section-container">
            <h2 class="section-title">Como Funciona?</h2>
            <div class="cards-grid">
              
              <div class="info-card">
                <div class="card-bg bg-1"></div> 
                <div class="card-content">
                  <div class="card-icon">📤</div>
                  <h3>1. Envie sua Foto</h3>
                  <p>Faça upload de qualquer imagem. Nosso algoritmo inteligente processa as melhores cores e contrastes em segundos.</p>
                </div>
              </div>
  
              <div class="info-card">
                <div class="card-bg bg-2"></div>
                <div class="card-content">
                  <div class="card-icon">🎨</div>
                  <h3>2. Edite a Grade</h3>
                  <p>Ganhe tempo: defina as dimensões e use a mudança de cores em massa para fazer alterações no gráfico sem precisar pintar pixel por pixel.</p>
                </div>
              </div>
  
              <div class="info-card">
                <div class="card-bg bg-3"></div>
                <div class="card-content">
                  <div class="card-icon">📄</div>
                  <h3>3. Baixe o PDF</h3>
                  <p>Exporte seu PDF completo com a receita linha por linha e contagem exata de cores.</p>
                </div>
              </div>
  
            </div>
          </div>
        </section>
  
        <footer class="site-footer">
          <div class="footer-inner">
            <div class="footer-left">
              <span class="footer-logo">TRAMA<span class="highlight">GRID</span></span>
              <span class="sep">|</span>
              <span class="copyright">© 2025</span>
            </div>
            
            <div class="footer-center">
              <a href="#">Privacidade</a>
              <a href="#">Termos</a>
              <a href="#">Suporte</a>
            </div>
  
            <div class="footer-right">
               <a href="#" aria-label="Instagram"><Instagram :size="16"/></a>
               <a href="#" aria-label="Twitter"><Twitter :size="16"/></a>
               <a href="#" aria-label="LinkedIn"><Linkedin :size="16"/></a>
            </div>
          </div>
        </footer>
  
      </div>
  
      <div class="chat-widget">
        <div v-if="isChatOpen" class="chat-window">
          <div class="chat-header">
            <span>Fale Conosco</span>
            <button @click="toggleChat"><X :size="18" /></button>
          </div>
          <form @submit.prevent="sendContactMessage" class="chat-body">
            <input v-model="chatForm.name" placeholder="Nome" required />
            <input v-model="chatForm.email" type="email" placeholder="E-mail" required />
            <textarea v-model="chatForm.message" placeholder="Mensagem..." required></textarea>
            <button type="submit" :disabled="isSending">
              <span v-if="isSending">...</span>
              <span v-else>Enviar <Send :size="14" style="margin-left:5px"/></span>
            </button>
          </form>
        </div>
        <button class="chat-fab" @click="toggleChat">
          <MessageCircle :size="24" />
        </button>
      </div>
  
    </div>
  </template>
  
  <style scoped>
  /* ========================
     ESTRUTURA
     ======================== */
  .page-wrapper {
    position: relative; width: 100vw; height: 100vh;
    background: #000; overflow: hidden;
  }
  .fixed-bg {
    position: absolute; inset: 0; z-index: 0; pointer-events: none;
  }
  canvas.c { width: 100%; height: 100%; }
  .dark-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.5) 50%, #050505 100%);
  }
  .scroll-content {
    position: absolute; inset: 0; overflow-y: auto; overflow-x: hidden; z-index: 10; scroll-behavior: smooth;
  }
  
  /* ========================
     NAVBAR (Efeito Glass + Hide Logo)
     ======================== */
  .navbar {
    position: fixed; top: 0; left: 0; width: 100%;
    padding: 25px 40px;
    display: flex; justify-content: center;
    z-index: 100;
    transition: all 0.4s ease;
    background: transparent;
  }
  
  /* Quando rola a página */
  .navbar.scrolled {
    background: rgba(10, 10, 10, 0.7);
    backdrop-filter: blur(12px);
    padding: 15px 40px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
  }
  
  .nav-inner { width: 100%; max-width: 1200px; display: flex; justify-content: space-between; align-items: center; }
  
  /* LOGO NA NAVBAR (Com transição de opacidade) */
  .nav-logo {
    font-size: 1.1rem; font-weight: 800; color: white; letter-spacing: 1px;
    opacity: 0; transform: translateY(-10px); /* Começa escondido */
    transition: all 0.4s ease;
  }
  
  /* Classe ativada pelo scroll */
  .nav-logo.visible {
    opacity: 1; transform: translateY(0);
  }
  
  .highlight { color: #e67e22; }
  
  .nav-links { display: flex; gap: 25px; align-items: center; }
  .nav-link { 
    color: #aaa; text-decoration: none; font-size: 0.9rem; font-weight: 500;
    display: flex; align-items: center; gap: 6px; transition: 0.2s; 
  }
  .nav-link:hover { color: white; }
  .nav-btn-login {
    background: rgba(230, 126, 34, 0.15); border: 1px solid rgba(230, 126, 34, 0.5); color: #e67e22;
    padding: 8px 20px; border-radius: 20px; text-decoration: none;
    font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 6px;
    transition: all 0.3s;
  }
  .nav-btn-login:hover { background: #e67e22; color: white; box-shadow: 0 0 15px rgba(230, 126, 34, 0.4); }
  
  /* ========================
     HERO & TIPOGRAFIA
     ======================== */
  .hero-section {
    position: relative; height: 100vh; display: flex; align-items: center; padding-left: 10%;
  }
  .content-left { max-width: 650px; color: white; will-change: transform, opacity; z-index: 2; }
  
  .badge-pill { background: rgba(39, 174, 96, 0.15); border: 1px solid #27ae60; color: #2ecc71; padding: 5px 14px; border-radius: 50px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 24px; display: inline-block; backdrop-filter: blur(5px); }
  .brand-title { font-size: 1.2rem; font-weight: 800; letter-spacing: 3px; margin: 0 0 30px 0; color: #fff; }
  .highlight { color: #e67e22; }
  .hero-headline { font-size: clamp(2.5rem, 4.5vw, 4.5rem); font-weight: 800; line-height: 1.05; margin-bottom: 24px; letter-spacing: -1px; }
  .text-gradient { background: linear-gradient(135deg, #e07e06 30%, #f1c40f 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: inline-block; }
  .hero-description { font-size: 1.4rem; line-height: 1.6; color: #d7d7d7; margin-bottom: 40px; max-width: 480px; font-weight: 333; }
  .cta-btn-primary { 
    background: #e67e22; color: white; border: none; padding: 16px 42px; 
    font-size: 1rem; font-weight: 700; border-radius: 8px; cursor: pointer; transition: 0.3s; 
    box-shadow: 0 10px 30px rgba(230, 126, 34, 0.25);
  }
  .cta-btn-primary:hover { background: #d35400; transform: translateY(-3px); box-shadow: 0 15px 40px rgba(230, 126, 34, 0.4); }
  
  /* Scroll Mouse Icon */
  .scroll-hint { position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%); opacity: 0.7; }
  .mouse-icon {
    width: 26px; height: 42px; border: 2px solid #666; border-radius: 20px; position: relative;
  }
  .wheel {
    width: 4px; height: 8px; background: #fff; position: absolute; top: 6px; left: 50%; transform: translateX(-50%); border-radius: 2px;
    animation: scrollWheel 2s infinite;
  }
  @keyframes scrollWheel { 0% { top: 6px; opacity: 1; } 100% { top: 24px; opacity: 0; } }
  
  /* ========================
     CARDS (PREMIUM LOOK)
     ======================== */
  .info-section {
    background: #080808; padding: 120px 20px; position: relative; z-index: 20; border-top: 1px solid #1a1a1a;
  }
  .section-container { max-width: 1200px; margin: 0 auto; }
  .section-title { font-size: 2.2rem; color: white; margin-bottom: 70px; font-weight: 700; text-align: center; }
  
  .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 40px; }
  
  .info-card {
    position: relative;
    background: #0f0f0f; 
    border-radius: 20px; 
    overflow: hidden; 
    border: 1px solid #222;
    height: 380px; 
    transition: transform 0.4s ease, border-color 0.4s ease;
    opacity: 0; transform: translateY(30px); 
    display: flex; flex-direction: column; justify-content: flex-end; 
  }
  
  .info-card.visible { opacity: 1; transform: translateY(0); }
  
  .card-bg {
    position: absolute; inset: 0; z-index: 1;
    background-size: cover; background-position: center;
    transition: all 0.5s ease;
    opacity: 0.4;
  }
  
  .bg-1 { background: linear-gradient(45deg, #2c3e50, #000); }
  .bg-2 { background: linear-gradient(45deg, #4b3d30, #000); }
  .bg-3 { background: linear-gradient(45deg, #1a252f, #000); }
  
  .card-content {
    position: relative; z-index: 2;
    padding: 30px;
    background: linear-gradient(0deg, rgba(0,0,0,1) 0%, rgba(0,0,0,0.6) 80%, rgba(0,0,0,0) 100%);
    transform: translateY(20px); transition: transform 0.4s ease;
  }
  
  .card-icon { font-size: 2.5rem; margin-bottom: 15px; text-shadow: 0 0 20px rgba(255,255,255,0.2); }
  .info-card h3 { color: white; margin-bottom: 10px; font-size: 1.4rem; font-weight: 700; }
  .info-card p { color: #999; line-height: 1.5; font-size: 0.95rem; opacity: 0.8; transition: opacity 0.3s; }
  
  .info-card:hover {
    transform: translateY(-8px);
    border-color: rgba(230, 126, 34, 0.4); 
    box-shadow: 0 20px 50px rgba(0,0,0,0.6);
  }
  
  .info-card:hover .card-bg {
    transform: scale(1.1); 
    filter: blur(4px) brightness(0.6); 
    opacity: 1; 
  }
  
  .info-card:hover .card-content { transform: translateY(0); }
  .info-card:hover p { opacity: 1; color: white; }
  
  /* ========================
     FOOTER (MINIMALISTA)
     ======================== */
  .site-footer { 
    background: #050505; border-top: 1px solid #151515; 
    padding: 25px 0; font-size: 0.85rem; color: #555; 
  }
  .footer-inner { 
    max-width: 1200px; margin: 0 auto; padding: 0 40px;
    display: flex; justify-content: space-between; align-items: center;
  }
  
  .footer-left { display: flex; align-items: center; gap: 10px; }
  .footer-logo { font-weight: 700; color: #888; }
  .sep { color: #333; }
  
  .footer-center { display: flex; gap: 20px; }
  .footer-center a { color: #666; text-decoration: none; transition: 0.2s; }
  .footer-center a:hover { color: #e67e22; }
  
  .footer-right { display: flex; gap: 15px; }
  .footer-right a { color: #666; transition: 0.2s; }
  .footer-right a:hover { color: white; }
  
  /* ========================
     CHAT WIDGET
     ======================== */
  .chat-widget { position: fixed; bottom: 30px; right: 30px; z-index: 200; display: flex; flex-direction: column; align-items: flex-end; }
  .chat-fab {
    width: 56px; height: 56px; border-radius: 50%; background: #e67e22; color: white;
    border: none; cursor: pointer; box-shadow: 0 8px 25px rgba(230,126,34,0.3);
    display: flex; align-items: center; justify-content: center; transition: 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }
  .chat-fab:hover { transform: scale(1.1); background: #d35400; }
  .chat-window {
    width: 320px; background: #161616; border-radius: 12px; margin-bottom: 15px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6); overflow: hidden; border: 1px solid #333;
    animation: slideUp 0.3s ease;
  }
  @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
  .chat-header { background: #202020; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; color: white; font-weight: 600; font-size: 0.95rem; border-bottom: 1px solid #333; }
  .chat-header button { background: none; border: none; color: #888; cursor: pointer; }
  .chat-header button:hover { color: white; }
  .chat-body { padding: 18px; display: flex; flex-direction: column; gap: 12px; }
  .chat-body input, .chat-body textarea {
    background: #0a0a0a; border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; outline: none; font-size: 0.9rem; transition: border-color 0.2s;
  }
  .chat-body input:focus, .chat-body textarea:focus { border-color: #e67e22; }
  .chat-body textarea { min-height: 90px; resize: none; }
  .chat-body button {
    background: #e67e22; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s;
  }
  .chat-body button:hover { background: #d35400; }
  
  /* RESPONSIVO */
  @media (max-width: 768px) {
    .hero-headline { font-size: 2.8rem; }
    .footer-inner { flex-direction: column; gap: 20px; padding: 0 20px; text-align: center; }
    .navbar { padding: 15px 20px; }
    .nav-text { display: none; }
    .hero-section { padding-left: 20px; padding-right: 20px; justify-content: center; text-align: center; }
    .content-left { align-items: center; display: flex; flex-direction: column; }
  }
  </style>