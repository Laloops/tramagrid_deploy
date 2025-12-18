<script setup>
  import { ref, onMounted, onUnmounted } from "vue";
  import { useRouter } from "vue-router";
  import { supabase } from "../supabase";
  import { createSession, uploadImage, eventBus } from "../api.js";
  import { showToast } from "../toast.js";
  import gsap from "gsap";
  
  // Refs pra animações de texto
  const contentLeft = ref(null);
  
  // =================================================================================
  // 1. LÓGICA DE NEGÓCIOS (Upload, Auth, Supabase)
  // =================================================================================
  const router = useRouter();
  const fileInput = ref(null);
  const isLoading = ref(false);
  const showFreeBadge = ref(false);
  const LOCAL_STORAGE_KEY = "tramagrid_anon_used";
  
  async function getOrCreateProfile(user) {
    let { data: profile } = await supabase
      .from("profiles")
      .select("credits, free_generation_used")
      .eq("id", user.id)
      .maybeSingle();
  
    if (!profile) {
      const { data: newProfile } = await supabase
        .from("profiles")
        .insert([
          {
            id: user.id,
            email: user.email,
            credits: 0,
            free_generation_used: false,
          },
        ])
        .select()
        .single();
      return newProfile;
    }
    return profile;
  }
  
  async function handleStartUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
  
    isLoading.value = true;
    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();
  
      if (user) {
        const apiBase = import.meta.env.VITE_API_URL || "";
        const res = await fetch(`${apiBase}/api/consume-credit`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: user.id }),
        });
  
        if (!res.ok) {
          if (res.status === 402) {
            showToast("Seus créditos acabaram!", "warning");
            setTimeout(() => router.push("/buy-credits"), 1500);
          } else {
            showToast(`Erro no backend`, "error");
          }
          if (fileInput.value) fileInput.value.value = "";
          return;
        }
        eventBus.dispatchEvent(new Event("credits-updated"));
      } else {
        if (localStorage.getItem(LOCAL_STORAGE_KEY)) {
          showToast("Cota esgotada. Entre para continuar!", "info");
          setTimeout(() => router.push("/login"), 1500);
          if (fileInput.value) fileInput.value.value = "";
          return;
        }
        localStorage.setItem(LOCAL_STORAGE_KEY, "true");
      }
  
      await createSession();
      await uploadImage(file);
      showToast("Sucesso! Processando...", "success");
      router.push("/editor");
    } catch (err) {
      console.error(err);
      showToast("Erro de conexão.", "error");
    } finally {
      isLoading.value = false;
    }
  }
  
  // =================================================================================
  // 2. ANIMAÇÃO DO CANVAS (ondas DISCRETAS e LEVES)
  // =================================================================================
  const canvasRef = ref(null);
  let ctx = null;
  let cw = 0;
  let ch = 0;
  let hue = 180;
  let nCubes = 0;
  let cubes = [];
  let staggerAnim = null;
  
  const img = new Image();
  const img2 = new Image();
  
  const imgSrc1 =
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAADIBAMAAADsElnyAAAAJFBMVEVHcEw+Pj5aWloQEBAZGRleXl6AgIDAwMBwcHCampq7u7tzc3M0sGdFAAAABXRSTlMAp/UwQ5FLsO8AAADxSURBVHgB7c9HcQRhDITRn8NgMABDWAjO6ewMYLgsWef8akelk1Pr/upTj023mkZxiK3dqSsODnpmdXBwUBlEaRCYckdtEKVBYModmKbQKDrGHZpaaPyqZxQaRc8oNPVyTaehUVRGURhFYerlmu2D5k3jqimO1+MCU4h5XFzc9sQjaXTO1vMTobMkXgmdBfFKNnTY8UroLIp3YkfxldBhB4QOAkIHAaHDDggdBIQOX0HoICB0EBA6CAgdlkPoICB0+ApCBwGhw1cQOggIBgHh5pCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQH0XuAS5hV4q0a3iHAAAAAElFTkSuQmCC";
  const imgSrc2 =
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAADIBAMAAADsElnyAAAAJFBMVEVHcEylpaXv7+/Gxsa+vr7m5uahoaE/Pz9/f3+Ojo5lZWWCgoKkaSxxAAAABnRSTlMA9TCcskPTdr2ZAAAA40lEQVR4Ae3POW0EQQBE0UZhBEawWBaAzz0QDIVhYgxmZ3X6pFZpIl/18xf8sep8GinFwzMmi8sFk8TlctFkockiGz80WWiyyMYPTRbZKLLxIxtFMIoVwCCSUQSTRDaeZ3POAKPIRpGNIhvPs3m8HOw0Pg+K+8fYo0FsY48GMUkyiEmSQUySDGKSZBCTJIOYZG0QkIVBQDQKydogIBqFRKOQaBSQYBAQDAKCQQSCUUg0CAhmLSAYhUSDgCwMIpFpFJnsW0lJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUnJjyJfg4PNmR1hT+AAAAAASUVORK5CYII=";
  
  const Cube = function (index, _x, _y, _s) {
    this.img = img;
    this.img2 = img2;
    this.scale = _s;
    this.x = _x;
    this.y = _y;
    this.z = 0;
    this.img2_opacity = 0;
  
    this.draw = function () {
      if (!ctx) return;
      ctx.translate(this.x, this.y + this.z);
      ctx.drawImage(
        this.img,
        (-100 / 2) * this.scale,
        (-200 / 2) * this.scale,
        100 * this.scale,
        200 * this.scale
      );
      ctx.globalAlpha = this.img2_opacity;
      ctx.drawImage(
        this.img2,
        (-100 / 2) * this.scale,
        (-200 / 2) * this.scale,
        100 * this.scale,
        200 * this.scale
      );
      ctx.globalAlpha = 1;
      ctx.translate(-this.x, -(this.y + this.z));
    };
  };
  
  function setGrid() {
    if (!canvasRef.value) return;
    const c = canvasRef.value;
    c.width = window.innerWidth;
    c.height = window.innerHeight;
  
    cw = Math.ceil(c.width / 100 + 1);
    ch = Math.floor(c.height / 25 + 10);
    cubes = [];
    let i = 0;
    for (let _y = 0; _y < ch; _y++) {
      for (let _x = 0; _x < cw; _x++) {
        if (_y % 2 === 0) {
          cubes.push(new Cube(i, -25 + _x * 100, -75 + _y * 25, 0.9));
        } else {
          cubes.push(new Cube(i, 25 + _x * 100, -75 + _y * 25, 0.9));
        }
        i++;
      }
    }
    nCubes = cubes.length;
  }
  
  // ANIMAÇÃO DISCRETA E LEVE (ondas suaves)
  function staggerFrom(from) {
    return gsap
      .timeline()
      .to(
        cubes,
        {
          duration: 3,
          z: 30,
          ease: "sine.inOut",
          stagger: {
            yoyo: true,
            amount: 6,
            grid: [ch, cw],
            overwrite: "auto",
            from: from,
            onComplete: function () {
              gsap.to(this.targets(), { duration: 4, z: 0, ease: "sine.inOut" });
            },
          },
        },
        0
      )
      .to(
        cubes,
        {
          duration: 1.5,
          img2_opacity: 0.5,
          stagger: {
            yoyo: true,
            amount: 6,
            grid: [ch, cw],
            overwrite: "auto",
            from: from,
            onComplete: function () {
              gsap.to(this.targets(), { duration: 2, img2_opacity: 0 });
            },
          },
        },
        0
      );
  }
  
  function anim() {
    staggerAnim = gsap
      .timeline({
        onComplete: anim,
        delay: 8,
      })
      .add(staggerFrom(gsap.utils.random(0, nCubes, 1)));
  }
  
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
  // 3. LIFECYCLE + ANIMAÇÕES DE TEXTO SUAVES (fade in)
   // =================================================================================
  onMounted(async () => {
    if (canvasRef.value) {
      ctx = canvasRef.value.getContext("2d");
      let loadedCount = 0;
      const checkLoad = () => {
        loadedCount++;
        if (loadedCount === 2) {
          setGrid();
          gsap.ticker.add(renderLoop);
          gsap.delayedCall(0.2, anim);
        }
      };
      img.onload = checkLoad;
      img2.onload = checkLoad;
      img.src = imgSrc1;
      img2.src = imgSrc2;
      window.addEventListener("resize", handleResize);
    }
  
    // Auth Badge
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (user) {
      const p = await getOrCreateProfile(user);
      if (p && !p.free_generation_used) showFreeBadge.value = true;
    } else {
      if (!localStorage.getItem(LOCAL_STORAGE_KEY)) showFreeBadge.value = true;
    }
  
    // ANIMAÇÕES DE TEXTO SUAVES (fade in + leve movimento de cima)
    gsap.timeline()
      .from(contentLeft.value.children, {
        y: 40,
        opacity: 0,
        duration: 1.2,
        stagger: 0.2,
        ease: "power2.out",
      });
  });
  
  onUnmounted(() => {
    gsap.ticker.remove(renderLoop);
    window.removeEventListener("resize", handleResize);
    gsap.killTweensOf(cubes);
    if (staggerAnim) staggerAnim.kill();
  });
  </script>
  
  <template>
    <div class="landing-container">
      <!-- CANVAS -->
      <canvas ref="canvasRef" class="c"></canvas>
  
      <!-- OVERLAY PRETO COM GRADIENT -->
      <div class="dark-overlay"></div>
  
      <!-- UI — TEXTO SOLTO, SEM CAIXA -->
      <div class="ui-overlay">
        <div ref="contentLeft" class="content-left">
          
          <div v-if="showFreeBadge" class="badge-pill">
            🎁 1ª Geração Grátis
          </div>
    
          <h1 class="brand-title">TRAMA<span class="highlight">GRID</span></h1>
          
          <h2 class="hero-headline">
            Transforme qualquer imagem em
            <span class="text-gradient">PIXELS</span>
          </h2>
    
          <p class="hero-description">
            O TramaGrid converte suas fotos favoritas em gráficos prontos para crochê, 
            tricô ou pixel art. Simplifique cores, edite a grade e baixe sua receita 
            em segundos. Crie mais, conte menos pontos.
          </p>
    
          <div class="action-area">
            <input 
              type="file" 
              ref="fileInput" 
              @change="handleStartUpload" 
              hidden 
              accept="image/*" 
            />
            
            <button 
              class="cta-btn-primary" 
              @click="fileInput.click()" 
              :disabled="isLoading"
            >
              <span v-if="isLoading" class="spinner"></span>
              <span v-else>1º Teste Grátis &rarr;</span>
            </button>
          </div>
    
        </div>
      </div>
    </div>
  </template>
  
  <style scoped>
  /* =========================================
     1. ESTRUTURA GERAL
     ========================================= */
  .landing-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    background: #000;
  }
  
  /* CANVAS */
  canvas.c {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
  }
  
  /* OVERLAY PRETO COM GRADIENT */
  .dark-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 100%);
    z-index: 1;
    pointer-events: none;
  }
  
  /* =========================================
     2. UI & TIPOGRAFIA (SEM CAIXA — TEXTO SOLTO)
     ========================================= */
  .ui-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10;
    display: flex;
    align-items: center;
    padding-left: 8%;
  }
  
  .content-left {
    max-width: 700px;
    color: white;
    text-align: left;
  }
  
  /* Badge */
  .badge-pill {
    display: inline-block;
    background: rgba(39, 174, 96, 0.2);
    border: 1px solid #27ae60;
    color: #2ecc71;
    padding: 6px 16px;
    border-radius: 50px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 24px;
    letter-spacing: 0.5px;
    backdrop-filter: blur(4px);
  }
  
  /* Título da Marca */
  .brand-title {
    font-family: system-ui, sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: 2px;
    margin: 0 0 40px 0;
    opacity: 0.8;
    color: #fff;
  }
  .highlight { color: #e67e22; }
  
  /* Headline Principal */
  .hero-headline {
    font-family: system-ui, -apple-system, sans-serif;
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 24px;
  }
  
  .text-gradient {
    background: linear-gradient(135deg, #e07e06e7 30%, #ede878 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
  }
  
  /* Texto Explicativo */
  .hero-description {
    font-size: 1.15rem;
    line-height: 1.6;
    color: #ccc;
    margin-bottom: 40px;
    max-width: 480px;
    font-weight: 300;
  }
  
  /* Botão de Ação */
  .action-area {
    margin-top: 40px;
  }
  
  .cta-btn-primary {
    background: #e67e22;
    color: white;
    border: none;
    padding: 18px 48px;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(230, 126, 34, 0.3);
    display: inline-flex;
    align-items: center;
    gap: 12px;
  }
  
  .cta-btn-primary:hover:not(:disabled) {
    background: #d35400;
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(230, 126, 34, 0.5);
  }
  
  .cta-btn-primary:disabled {
    opacity: 0.7;
    cursor: wait;
    filter: grayscale(0.8);
  }
  
  .spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,255,255,0.3);
    border-radius: 50%;
    border-top-color: #fff;
    animation: spin 1s infinite linear;
  }
  
  @keyframes spin { 
    to { transform: rotate(360deg); } 
  }
  
  /* Responsivo Mobile */
  @media (max-width: 768px) {
    .ui-overlay {
      padding: 20px;
      align-items: flex-end;
      background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.9) 50%, #000 100%);
    }
  
    .content-left {
      margin-bottom: 40px;
    }
  
    .hero-headline {
      font-size: 2.2rem;
    }
  
    .hero-description {
      font-size: 1rem;
    }
  
    .brand-title {
      display: none;
    }
  }
  </style>