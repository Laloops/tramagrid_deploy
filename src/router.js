import { createRouter, createWebHistory } from "vue-router";
import HomeView from "./views/HomeView.vue";
import LoginView from "./views/LoginView.vue";
import DashboardView from "./views/DashboardView.vue";
import EditorView from "./views/EditorView.vue";
import BuyCreditsView from "./views/BuyCreditsView.vue";

// NOVAS IMPORTS (Vamos criar esses arquivos no passo 4)
import BlogListView from "./views/BlogListView.vue";
import BlogPostView from "./views/BlogPostView.vue";
import AdminBlogView from "./views/AdminBlogView.vue";

import { supabase } from "./supabase";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/login", name: "login", component: LoginView },
    { path: "/dashboard", name: "dashboard", component: DashboardView },
    { path: "/editor", name: "editor", component: EditorView },
    { path: "/buy-credits", name: "buy-credits", component: BuyCreditsView },
    
    // === ROTAS DO BLOG ===
    { path: "/blog", name: "blog-list", component: BlogListView },
    { path: "/blog/:slug", name: "blog-post", component: BlogPostView },
    
    // === ÁREA ADMINISTRATIVA ===
    { 
      path: "/admin", 
      name: "admin", 
      component: AdminBlogView,
      meta: { requiresAuth: true, requiresAdmin: true } 
    },
  ],
});

// Guardas de Rota (Segurança)
router.beforeEach(async (to, from, next) => {
  const { data: { session } } = await supabase.auth.getSession();

  // Verifica se precisa de login
  if (to.meta.requiresAuth && !session) {
    next("/login");
    return;
  }

  // Verifica se precisa ser ADMIN
  if (to.meta.requiresAdmin) {
    // ⚠️ SUBSTITUA PELO SEU E-MAIL REAL PARA TER ACESSO ⚠️
    const MY_EMAIL = "millalopes.01@gmail.com"; 
    
    if (session?.user?.email !== MY_EMAIL) {
      alert("Acesso negado: Apenas administradores.");
      next("/dashboard"); // Manda usuário comum pro dashboard normal
      return;
    }
  }

  // Redireciona usuário logado da Home para o Dashboard
  if (to.path === "/" && session) {
    next("/dashboard");
    return;
  }

  next();
});

export default router;