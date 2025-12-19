<script setup>
  import { ref, onMounted, onUnmounted } from 'vue'
  import { supabase } from '../supabase'
  import { useRouter, useRoute } from 'vue-router'
  import { showToast } from '../toast.js'
  import { API_BASE } from '../api' // <--- IMPORTANTE: Adicionado para o rastreio funcionar
  import { Mail, ArrowLeft, Chrome, Sparkles } from 'lucide-vue-next'
  import gsap from 'gsap'
  
  const email = ref('')
  const loading = ref(false)
  const loginBox = ref(null)
  const router = useRouter()
  const route = useRoute()
  
  // Lógica de Magic Link
  async function handleLogin() {
    // 1. Bloqueio de Alias (+)
    if (email.value.includes('+')) {
      alert('Por favor, use seu e-mail padrão (sem o sinal de +).');
      return;
    }
  
    // 2. Validação
    if (!email.value) return; 
    
    loading.value = true
    
    const baseUrl = import.meta.env.DEV 
      ? 'http://localhost:5173' 
      : 'https://tramagrid.com.br'
    
    const { error } = await supabase.auth.signInWithOtp({
      email: email.value,
      options: { 
        emailRedirectTo: `${baseUrl}/dashboard`
      }
    })
    
    if (error) {
      showToast("Erro: " + error.message, "error")
    } else {
      // === RASTREIO DE LOGIN REAL ===
      try {
        // Verifica se API_BASE está definida antes de chamar
        if (typeof API_BASE !== 'undefined') {
          fetch(`${API_BASE}/api/track/login`, { method: 'POST' });
        }
      } catch (e) { console.error("Erro tracking:", e) }
      // ==============================
  
      showToast("✨ Link enviado! Verifique seu e-mail.", "success")
      email.value = ""
    }
    
    loading.value = false
  }
  
  // Login Social
  async function handleSocialLogin(provider) {
    const baseUrl = import.meta.env.DEV 
      ? 'http://localhost:5173' 
      : 'https://tramagrid.com.br'
  
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${baseUrl}/dashboard` }
    })
    
    if (error) showToast("Erro no login: " + error.message, "error")
  }
  
  let authListener = null
  
  onMounted(() => {
    // Animação GSAP: Entrada suave
    if (loginBox.value) {
      gsap.from(loginBox.value, {
        y: 20,
        opacity: 0,
        duration: 0.6,
        ease: "power2.out"
      })
    }
  
    // Gerenciamento de estado de autenticação
    const { data } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') {
        const redirect = route.query.redirect || '/dashboard'
        router.push(redirect)
      }
    })
    authListener = data.subscription
  })
  
  onUnmounted(() => {
    if (authListener) authListener.unsubscribe()
  })
  </script>
  
  <template>
    <div class="login-page">
      <div class="bg-decoration" aria-hidden="true">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
      </div>
  
      <main ref="loginBox" class="login-card">
        <header class="card-header">
          <h1 class="brand-name">Trama<span class="highlight">Grid</span></h1>
          <p class="tagline">Sua arte em pixels.</p>
        </header>
  
        <div class="auth-section">
          <button class="btn-google" @click="handleSocialLogin('google')">
            <Chrome :size="18" /> 
            <span>Google</span>
          </button>
  
          <div class="separator">
            <span class="line"></span>
            <span class="text">ou</span>
            <span class="line"></span>
          </div>
  
          <div class="email-form">
            <div class="input-field">
              <Mail :size="16" class="input-icon" />
              <input 
                v-model="email" 
                type="email" 
                placeholder="seu@email.com" 
                @keyup.enter="handleLogin" 
              />
            </div>
            
            <button 
              @click="handleLogin" 
              :disabled="loading || !email" 
              class="btn-submit"
            >
              <span v-if="loading" class="spinner"></span>
              <template v-else>
                <Sparkles :size="16" /> <span>Enviar Link</span>
              </template>
            </button>
          </div>
        </div>
  
        <footer class="card-footer">
          <button @click="router.push('/')" class="btn-back">
            <ArrowLeft :size="14" /> Voltar
          </button>
        </footer>
      </main>
    </div>
  </template>
  
  <style scoped>
  /* Container Principal - Sem Scroll */
  .login-page {
    height: 100vh;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #0c0c0d;
    position: relative;
    overflow: hidden; /* Garante que nada vaze */
    padding: 20px;
  }
  
  /* Fundo Decorativo */
  .bg-decoration { position: absolute; inset: 0; pointer-events: none; z-index: 0; }
  .blob { position: absolute; width: 40vw; height: 40vw; max-width: 400px; filter: blur(90px); opacity: 0.15; border-radius: 50%; }
  .blob-1 { background: #e67d22a8; top: 10%; right: 10%; }
  .blob-2 { background: #9c59b68d; bottom: 10%; left: 10%; }
  
  /* === CARD ULTRA COMPACTO (DELICADO) === */
  .login-card {
    width: 100%;
    max-width: 320px; /* Largura bem reduzida */
    background: rgba(28, 28, 30, 0.85);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 24px 24px; /* Padding interno pequeno */
    box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.6);
    z-index: 10;
  }
  
  /* Header */
  .card-header { text-align: center; margin-bottom: 15px; }
  .brand-name { font-size: 1.5rem; font-weight: 800; color: #fff; letter-spacing: -0.5px; margin: 0; line-height: 1; }
  .highlight { color: #e67e22; }
  .tagline { color: #8e8e93; font-size: 0.8rem; margin-top: 5px; font-weight: 400; }
  
  /* Botões e Inputs - Slim (36px altura) */
  .auth-section { display: flex; flex-direction: column; gap: 10px; }
  
  .btn-google {
    width: 100%;
    height: 38px;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    background: #fff; color: #1c1c1e; border: none;
    border-radius: 8px; font-weight: 600; font-size: 0.85rem;
    cursor: pointer; transition: transform 0.2s;
  }
  .btn-google:hover { transform: translateY(-1px); background: #f2f2f7; }
  
  .separator { display: flex; align-items: center; gap: 8px; margin: 2px 0; }
  .line { flex: 1; height: 1px; background: rgba(255, 255, 255, 0.1); }
  .text { color: #555; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
  
  .email-form { display: flex; flex-direction: column; gap: 10px; }
  .input-field { position: relative; width: 100%; }
  .input-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #666; }
  
  input {
    width: 85%;
    height: 38px;
    padding: 0 12px 0 34px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px; color: #fff; font-size: 0.85rem;
    transition: all 0.2s;
  }
  input:focus { outline: none; border-color: #e67e22; box-shadow: 0 0 0 2px rgba(230, 126, 34, 0.15); background: rgba(0,0,0,0.6); }
  input::placeholder { color: #555; }
  
  .btn-submit {
    width: 100%;
    height: 38px;
    background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
    color: #fff; border: none; border-radius: 8px; font-weight: 600; font-size: 0.85rem;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    cursor: pointer; transition: all 0.2s;
  }
  .btn-submit:hover:not(:disabled) { transform: translateY(-1px); filter: brightness(1.1); }
  .btn-submit:disabled { opacity: 0.5; cursor: wait; }
  
  /* Footer */
  .card-footer { margin-top: 15px; text-align: center; }
  .btn-back { background: none; border: none; color: #555; font-size: 0.75rem; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; transition: color 0.2s; }
  .btn-back:hover { color: #aaa; }
  
  .spinner { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s infinite linear; }
  @keyframes spin { to { transform: rotate(360deg); } }
  
  /* Responsividade */
  @media (max-width: 480px) {
    .login-card { width: 90%; max-width: 300px; padding: 20px; }
  }
  </style>