<script setup>
  import { ref, onMounted, onUnmounted } from 'vue'
  import { supabase } from '../supabase'
  import { useRouter, useRoute } from 'vue-router'
  import { showToast } from '../toast.js'
  import { Mail, ArrowLeft, Chrome, Sparkles } from 'lucide-vue-next'
  import gsap from 'gsap'
  
  const email = ref('')
  const loading = ref(false)
  const loginBox = ref(null)
  const router = useRouter()
  const route = useRoute()
  
  // Lógica de Magic Link
  async function handleLogin() {
    if (!email.value) return
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
    gsap.from(loginBox.value, {
      y: 30,
      opacity: 0,
      duration: 0.8,
      ease: "power2.out"
    })
  
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
          <p class="tagline">Sua arte em pixels, salva para sempre.</p>
        </header>
  
        <div class="auth-section">
          <button class="btn-google" @click="handleSocialLogin('google')">
            <Chrome :size="20" /> 
            <span>Entrar com Google</span>
          </button>
  
          <div class="separator">
            <span class="line"></span>
            <span class="text">ou e-mail</span>
            <span class="line"></span>
          </div>
  
          <div class="email-form">
            <div class="input-field">
              <Mail :size="18" class="input-icon" />
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
                <Sparkles :size="18" /> <span>Receber Link Mágico</span>
              </template>
            </button>
          </div>
        </div>
  
        <footer class="card-footer">
          <button @click="router.push('/')" class="btn-back">
            <ArrowLeft :size="14" /> Voltar ao início
          </button>
        </footer>
      </main>
    </div>
  </template>
  
  <style scoped>
  /* Container Principal Responsivo */
  .login-page {
    min-height: 100vh;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #0c0c0d;
    position: relative;
    overflow-x: hidden;
    padding: 24px;
  }
  
  /* Fundo Decorativo */
  .bg-decoration {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 0;
  }
  .blob {
    position: absolute;
    width: 60vw;
    height: 60vw;
    max-width: 600px;
    filter: blur(100px);
    opacity: 0.1;
    border-radius: 50%;
  }
  .blob-1 { background: #e67e22; top: -10%; right: -10%; }
  .blob-2 { background: #9b59b6; bottom: -10%; left: -10%; }
  
  /* Card com Glassmorphism */
  .login-card {
    width: 100%;
    max-width: 420px;
    background: rgba(28, 28, 30, 0.8);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 32px;
    padding: 48px 32px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    z-index: 10;
  }
  
  .card-header { text-align: center; margin-bottom: 40px; }
  .brand-name { font-size: 2.2rem; font-weight: 800; color: #fff; letter-spacing: -1.5px; }
  .highlight { color: #e67e22; }
  .tagline { color: #8e8e93; font-size: 0.95rem; margin-top: 8px; }
  
  /* Botões e Inputs */
  .auth-section { display: flex; flex-direction: column; gap: 20px; }
  
  .btn-google {
    width: 100%;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: #fff;
    color: #1c1c1e;
    border: none;
    border-radius: 16px;
    font-weight: 700;
    font-size: 1rem;
    cursor: pointer;
    transition: transform 0.2s;
  }
  .btn-google:hover { transform: translateY(-2px); background: #f2f2f7; }
  
  .separator { display: flex; align-items: center; gap: 12px; margin: 8px 0; }
  .line { flex: 1; height: 1px; background: rgba(255, 255, 255, 0.1); }
  .text { color: #636366; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }
  
  .email-form { display: flex; flex-direction: column; gap: 14px; }
  .input-field { position: relative; width: 83%; }
  .input-icon { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: #8e8e93; }
  
  input {
    width: 100%;
    height: 56px;
    padding: 0 16px 0 52px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    color: #fff;
    font-size: 1rem;
    transition: all 0.2s;
  }
  input:focus { outline: none; border-color: #e67e22; box-shadow: 0 0 0 4px rgba(230, 126, 34, 0.15); }
  
  .btn-submit {
    width: 100%;
    height: 56px;
    background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
    color: #fff;
    border: none;
    border-radius: 16px;
    font-weight: 700;
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-submit:hover:not(:disabled) { transform: translateY(-2px); filter: brightness(1.1); }
  .btn-submit:disabled { opacity: 0.5; cursor: wait; }
  
  .card-footer { margin-top: 32px; text-align: center; }
  .btn-back { background: none; border: none; color: #636366; font-size: 0.9rem; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; transition: color 0.2s; }
  .btn-back:hover { color: #fff; }
  
  .spinner { width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s infinite linear; }
  @keyframes spin { to { transform: rotate(360deg); } }
  
  /* Responsividade Mobile Extrema */
  @media (max-width: 480px) {
    .login-page { padding: 0; background: #0c0c0d; }
    .login-card { 
      height: 100vh; 
      max-width: none; 
      border-radius: 0; 
      border: none; 
      padding: 60px 24px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .bg-decoration { display: none; }
  }
  </style>