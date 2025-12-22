import os
import json
import io
import base64
import uuid
import math
import stripe 
import string 
from dotenv import load_dotenv
from pathlib import Path 
from PIL import Image, ImageDraw, ImageEnhance, ImageOps, ImageFont
from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Tuple, List, Any
from supabase import create_client, Client
import requests

# ReportLab para PDF Profissional
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader, simpleSplit
from datetime import datetime

# --- CORREÇÃO DE CORS ---
# O navegador exige origens explícitas para permitir credenciais/pagamentos com segurança.

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # <--- Aqui usamos a lista específica
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

origins = [
    "https://tramagrid.com.br",
    "https://www.tramagrid.com.br",
    "http://localhost:5173",  # Para seus testes locais
    "http://127.0.0.1:5173"
]


# ================= CONFIGURAÇÃO DE AMBIENTE =================
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

if env_path.exists():
    print(f"✅ Arquivo .env carregado de: {env_path}")
else:
    print(f"❌ AVISO: Arquivo .env não encontrado em: {env_path}")

# ================= CONFIGURAÇÃO DE CHAVES =================
stripe.api_key = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

try:
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase Admin conectado!")
    else:
        print("⚠️ Variáveis do Supabase faltando no .env")
        supabase_admin = None
except Exception as e:
    print(f"⚠️ Erro ao conectar Supabase: {e}")
    supabase_admin = None

# ================= LÓGICA DE PROCESSAMENTO =================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
sessions: Dict[str, "TramaGridSession"] = {}

class TramaGridSession:
    def __init__(self):
        self.original: Optional[Image.Image] = None
        self.processed: Optional[Image.Image] = None
        self.quantized: Optional[Image.Image] = None
        self.palette: Dict[int, Tuple[int, int, int]] = {}
        self.custom_palette: Dict[int, Tuple[int, int, int]] = {}
        self.grid_image: Optional[Image.Image] = None
        self.history: List[Dict[str, Any]] = []
        
        self.grid_width_cells: int = 130
        self.cell_size: int = 22
        self.highlighted_row: int = -1
        self.max_colors: int = 64
        self.brightness: float = 1.0
        self.contrast: float = 1.0
        self.saturation: float = 1.0
        self.gamma: float = 1.0
        self.posterize: int = 8
        self.gauge_stitches: int = 20
        self.gauge_rows: int = 20
        self.show_grid: bool = True

   # 1. Altere a definição do método para aceitar o parâmetro 'lite'
    def save_to_disk(self, session_id: str, lite: bool = False):
        s_dir = os.path.join(DATA_DIR, session_id)
        os.makedirs(s_dir, exist_ok=True)
        
        meta = {
            "params": {
                # ... (mantenha os params iguais) ...
                "grid_width_cells": self.grid_width_cells,
                "max_colors": self.max_colors,
                "brightness": self.brightness,
                "contrast": self.contrast,
                "saturation": self.saturation,
                "gamma": self.gamma,
                "posterize": self.posterize,
                "gauge_stitches": self.gauge_stitches,
                "gauge_rows": self.gauge_rows,
                "show_grid": self.show_grid,
                "highlighted_row": self.highlighted_row
            },
            "palette": {str(k): v for k, v in self.palette.items()},
            "custom_palette": {str(k): v for k, v in self.custom_palette.items()}
        }
        
        with open(os.path.join(s_dir, "meta.json"), "w") as f: json.dump(meta, f)
        
        # OTIMIZAÇÃO AQUI: Se for 'lite', NÃO salva a original de novo
        if self.original and not lite: 
            self.original.save(os.path.join(s_dir, "original.png"))
            
        if self.quantized: 
            self.quantized.save(os.path.join(s_dir, "quantized.png"))

    def load_from_disk(self, session_id: str) -> bool:
        s_dir = os.path.join(DATA_DIR, session_id)
        meta_path = os.path.join(s_dir, "meta.json")
        if not os.path.exists(meta_path): return False
        try:
            with open(meta_path, "r") as f: meta = json.load(f)
            p = meta.get("params", {})
            for k, v in p.items():
                if hasattr(self, k): setattr(self, k, v)
            self.palette = {int(k): tuple(v) for k, v in meta.get("palette", {}).items()}
            self.custom_palette = {int(k): tuple(v) for k, v in meta.get("custom_palette", {}).items()}
            if os.path.exists(os.path.join(s_dir, "original.png")):
                self.original = Image.open(os.path.join(s_dir, "original.png")).convert("RGB")
            if os.path.exists(os.path.join(s_dir, "quantized.png")):
                self.quantized = Image.open(os.path.join(s_dir, "quantized.png")).convert("P")
                flat_palette = [0] * 768
                for idx, (r, g, b) in self.palette.items():
                    if idx < 256: flat_palette[idx*3:idx*3+3] = [r, g, b]
                self.quantized.putpalette(flat_palette)
            if self.quantized: self._draw_grid()
            return True
        except: return False

    def _save_state(self):
        if not self.quantized: return
        if len(self.history) >= 20: self.history.pop(0)
        self.history.append({'quantized': self.quantized.copy(), 'palette': self.palette.copy(), 'custom_palette': self.custom_palette.copy()})

    def undo(self):
        if not self.history: return
        s = self.history.pop()
        self.quantized = s['quantized']; self.palette = s['palette']; self.custom_palette = s['custom_palette']
        self._draw_grid()

    def load_image(self, file_bytes: bytes) -> None:
        self.original = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        self.history = []

    def generate_grid(self) -> None:
        if not self.original: return
        img = self.original.copy()
        if self.posterize < 8: img = ImageOps.posterize(img, max(1, min(8, int(self.posterize))))
        if self.gamma != 1.0: img = img.point([int(((i/255.0)**(1.0/self.gamma))*255) for i in range(256)]*3)
        if self.saturation != 1.0: img = ImageEnhance.Color(img).enhance(self.saturation)
        if self.brightness != 1.0: img = ImageEnhance.Brightness(img).enhance(self.brightness)
        if self.contrast != 1.0: img = ImageEnhance.Contrast(img).enhance(self.contrast)

        ratio = self.gauge_stitches / max(1, self.gauge_rows)
        w, h = img.size
        new_w = max(10, self.grid_width_cells)
        new_h = int((h / w) * new_w * ratio)
        
        self.processed = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.quantized = self.processed.quantize(colors=self.max_colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
        
        raw = self.quantized.getpalette()[:self.max_colors * 3]
        base = {}
        for i in range(self.max_colors):
            if i*3 + 2 < len(raw):
                r, g, b = raw[i*3:i*3+3]
                base[i] = (r, g, b)
        self.palette = {i: self.custom_palette.get(i, c) for i, c in base.items()}
        self._draw_grid()

    def _draw_grid(self) -> None:
        if not self.quantized: return
        
        # MARGENS: Espaço para números em BAIXO e na DIREITA
        pad_top_left = 20   
        pad_bot_right = 60 
        
        wc, hc = self.quantized.size
        total_w = pad_top_left + wc * self.cell_size + pad_bot_right
        total_h = pad_top_left + hc * self.cell_size + pad_bot_right
        
        if not self.show_grid:
            base = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
            prev = self.quantized.resize((wc * self.cell_size, hc * self.cell_size), Image.Resampling.NEAREST)
            base.paste(prev, (pad_top_left, pad_top_left))
            self.grid_image = base.convert("RGB")
            return

        base = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
        draw = ImageDraw.Draw(base)
        
        # Pixels
        for y in range(hc):
            for x in range(wc):
                color = self.palette.get(self.quantized.getpixel((x, y)), (255, 255, 255))
                px, py = pad_top_left + x * self.cell_size, pad_top_left + y * self.cell_size
                draw.rectangle([px, py, px + self.cell_size, py + self.cell_size], fill=color)

        overlay = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 0))
        d_ov = ImageDraw.Draw(overlay)
        
        # Linhas de Grade
        for y in range(hc + 1):
            py = pad_top_left + y * self.cell_size
            thk = (y % 10 == 0 or y == 0 or y == hc)
            d_ov.line([(pad_top_left, py), (pad_top_left + wc * self.cell_size, py)], fill=(255,255,255,180 if thk else 70), width=2 if thk else 1)
        for x in range(wc + 1):
            px = pad_top_left + x * self.cell_size
            thk = (x % 10 == 0 or x == 0 or x == wc)
            d_ov.line([(px, pad_top_left), (px, pad_top_left + hc * self.cell_size)], fill=(255,255,255,180 if thk else 70), width=2 if thk else 1)
            
        combined = Image.alpha_composite(base, overlay)
        d_comb = ImageDraw.Draw(combined)
        
              # --- NÚMEROS DA GRADE (PADRÃO CROCHÊ/TAPESTRY) ---
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        except:
            try:
                font = ImageFont.truetype("liberation-sans-bold.ttf", 14)
            except:
                font = ImageFont.load_default()

        text_color = (100, 100, 100)

        # EIXO X (embaixo da grade): Direita → Esquerda (1 na direita, max na esquerda)
        y_pos_x = pad_top_left + hc * self.cell_size + 5
        for x in range(wc):
            num = wc - x  # inverte: x=0 vira wc, x=wc-1 vira 1
            txt = str(num)
            bbox = draw.textbbox((0, 0), txt, font=font)
            tw = bbox[2] - bbox[0]
            tx = pad_top_left + x * self.cell_size + (self.cell_size - tw) / 2
            d_comb.text((tx, y_pos_x), txt, fill=text_color, font=font)

        # EIXO Y (lado DIREITO da grade): Baixo → Cima (1 embaixo, max em cima)
        x_pos_y = pad_top_left + wc * self.cell_size + 5  # 5px à direita da grade
        for y in range(hc):
            num = hc - y  # inverte: y=0 vira hc, y=hc-1 vira 1
            txt = str(num)
            bbox = draw.textbbox((0, 0), txt, font=font)
            th = bbox[3] - bbox[1]
            ty = pad_top_left + y * self.cell_size + (self.cell_size - th) / 2
            d_comb.text((x_pos_y, ty), txt, fill=text_color, font=font)

        self.grid_image = combined.convert("RGB")

        #
    def get_palette_info(self) -> List[Dict]:
        """Retorna TODAS as cores da paleta, mesmo as que têm 0 pixels."""
        if not self.palette: return []
        
        # 1. Contamos o uso de pixels de forma eficiente
        usage = defaultdict(int)
        if self.quantized:
            w, h = self.quantized.size
            for y in range(h):
                for x in range(w):
                    usage[self.quantized.getpixel((x, y))] += 1
                
        result = []
        # 2. Iteramos sobre self.palette para garantir que cores novas apareçam
        for idx, rgb in self.palette.items():
            r, g, b = rgb
            result.append({
                "index": idx,
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "count": usage.get(idx, 0) # Se não tiver na grade, o uso é 0
            })
            
        # 3. Ordenamos pelas mais usadas para facilitar o trabalho
        return sorted(result, key=lambda x: -x['count'])
        
    def paint_cell(self, x, y, idx):
        if not self.quantized or idx not in self.palette: return
        self._save_state()
        if 0 <= x < self.quantized.width and 0 <= y < self.quantized.height:
            self.quantized.putpixel((x, y), idx)
            self._draw_grid()

    def replace_color(self, idx, hex_val):
        self._save_state()
        self.custom_palette[idx] = self.palette[idx] = (int(hex_val[1:3],16), int(hex_val[3:5],16), int(hex_val[5:7],16))
        self._draw_grid()

    def merge_many_colors(self, from_list, to_index):
        if not self.quantized: return
        self._save_state()
        
        # OTIMIZAÇÃO SUPREMA: Cria uma tabela de substituição única para TODAS as cores
        # Em vez de processar a imagem 10 vezes, processamos 1 vez só.
        table = []
        for i in range(256):
            if i in from_list:
                table.append(to_index) # Se for uma das cores ruins, vira a cor boa
            else:
                table.append(i)        # Senão, mantém
        
        # Aplica a troca instantaneamente em C (super rápido)
        self.quantized = self.quantized.point(table)
        
        # Remove as cores antigas da paleta
        for idx in from_list:
            if idx != to_index: # Proteção extra
                self.palette.pop(idx, None)
                self.custom_palette.pop(idx, None)
            
        self._draw_grid()

        # Adicione isso no backend/tramagrid_backend.py dentro da classe TramaGridSession
    def merge_colors(self, f, t):
        if not self.quantized: return
        self._save_state()
        
        # OTIMIZAÇÃO: Substitui a cor 'f' pela 't' instantaneamente
        table = []
        for i in range(256):
            table.append(t if i == f else i)
        self.quantized = self.quantized.point(table)
        
        # Remove a cor antiga da paleta
        self.palette.pop(f, None)
        self.custom_palette.pop(f, None)
        self._draw_grid()

    def delete_color(self, idx):
        if not self.quantized: return
        self._save_state()
        
        # 1. Encontra a cor mais próxima para substituir (para não deixar buracos pretos)
        c1 = self.palette.get(idx)
        if not c1: return # Se a cor já não existe, sai
        
        best, min_d = None, float('inf')
        for i, c2 in self.palette.items():
            if i == idx: continue
            # Distância Euclidiana simples
            d = math.sqrt(sum((a-b)**2 for a,b in zip(c1,c2)))
            if d < min_d: min_d, best = d, i
            
        # 2. Se achou uma cor substituta, aplica a troca rápida
        if best is not None:
            table = []
            for i in range(256):
                table.append(best if i == idx else i)
            self.quantized = self.quantized.point(table)
            
        # 3. Remove a cor deletada
        self.palette.pop(idx, None)
        self.custom_palette.pop(idx, None)
        self._draw_grid()

    def get_pixel_index(self, x, y): 
        return int(self.quantized.getpixel((x,y))) if self.quantized and 0<=x<self.quantized.width and 0<=y<self.quantized.height else -1

    def replace_index_in_region(self, x, y, w, h, f, t):
        if not self.quantized: return
        self._save_state()
        for py in range(max(0,y), min(self.quantized.height, y+h)):
            for px in range(max(0,x), min(self.quantized.width, x+w)):
                if self.quantized.getpixel((px,py)) == f: self.quantized.putpixel((px,py), t)
        self._draw_grid()

   #
    def get_grid_base64(self) -> str:
        if not self.grid_image: return ""
        img = self.grid_image.copy()
        if self.highlighted_row >= 0:
            # Criamos o overlay totalmente transparente (0 alpha)
            ov = Image.new("RGBA", img.size, (0,0,0,0))
            d = ImageDraw.Draw(ov)
            
            row_idx = self.quantized.height - self.highlighted_row
            if 0 <= row_idx < self.quantized.height:
                # pad_top_left é 20 no seu código
                py = 20 + row_idx * self.cell_size 
                
                # Pintamos o "escuro" APENAS acima e abaixo da linha, 
                # deixando a linha com 0 alpha (cor original/branca)
                d.rectangle([0, 0, img.width, py], fill=(0, 0, 0, 180)) 
                d.rectangle([0, py + self.cell_size, img.width, img.height], fill=(0, 0, 0, 180))
                
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return base64.b64encode(buf.getvalue()).decode()
    
    def suggest_clusters(self, threshold=50.0):
        if not self.palette: return []
        colors = list(self.palette.items())
        groups = []
        visited = set()
        for i in range(len(colors)):
            idx1, rgb1 = colors[i]
            if idx1 in visited: continue
            grp = [idx1]
            for j in range(i+1, len(colors)):
                idx2, rgb2 = colors[j]
                if idx2 in visited: continue
                if math.sqrt(sum((a-b)**2 for a,b in zip(rgb1,rgb2))) < threshold:
                    grp.append(idx2); visited.add(idx2)
            if len(grp) > 1: visited.add(idx1); groups.append(grp)
        return groups

# --- MODELOS DO BLOG ---
class BlogPostModel(BaseModel):
    title: str
    slug: str
    content: str
    image_url: str
    excerpt: str
    published: bool = True

# --- ROTAS DO BLOG (Adicione junto com as outras rotas @app) ---

# 1. LISTAR POSTS (Público)
@app.get("/api/posts")
def get_posts():
    # Retorna posts mais recentes primeiro
    res = supabase_admin.table('posts').select('*').eq('published', True).order('created_at', desc=True).execute()
    return res.data

# 2. LER UM POST (Público)
@app.get("/api/posts/{slug}")
def get_post(slug: str):
    res = supabase_admin.table('posts').select('*').eq('slug', slug).single().execute()
    if not res.data: raise HTTPException(404, "Post não encontrado")
    return res.data

# 3. CRIAR POST (Admin)
@app.post("/api/posts")
def create_post(post: BlogPostModel):
    # Aqui você poderia verificar se o usuário é admin, mas como é MVP,
    # vamos confiar que a rota só é chamada pelo painel protegido do Vue.
    try:
        data = post.dict()
        res = supabase_admin.table('posts').insert(data).execute()
        return {"ok": True, "data": res.data}
    except Exception as e:
        raise HTTPException(400, str(e))

# 4. DELETAR POST (Admin)
@app.delete("/api/posts/{id}")
def delete_post(id: int):
    try:
        supabase_admin.table('posts').delete().eq('id', id).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))
    

    # ... (imports existentes)

# === ROTA DE ESTATÍSTICAS DO ADMIN ===
@app.get("/api/admin/stats")
def get_admin_stats():
    try:
        # Conta Usuários (Profiles)
        res_users = supabase_admin.table('profiles').select('id', count='exact').execute()
        count_users = res_users.count if res_users.count else 0
        
        # Conta Projetos
        res_projects = supabase_admin.table('projects').select('id', count='exact').execute()
        count_projects = res_projects.count if res_projects.count else 0
        
        # Mock para dados que ainda não temos rastreamento
        # (Visitantes e Logins precisariam de uma tabela de analytics)
        return {
            "total_users": count_users,
            "total_projects": count_projects,
            "daily_visits": 142,      # Placeholder
            "daily_logins": 28,       # Placeholder
            "new_subs": 3             # Placeholder
        }
    except Exception as e:
        print(f"Erro stats: {e}")
        return {"total_users": 0, "total_projects": 0, "daily_visits": 0}


@app.post("/api/track/visit")
def track_visit():
    try:
        if supabase_admin:
            # Chama a função segura no banco de dados
            supabase_admin.rpc('increment_visit').execute()
        return {"ok": True}
    except Exception as e:
        print(f"Erro tracking visit: {e}")
        # Retornamos OK mesmo com erro para não travar o front
        return {"ok": True}



@app.post("/api/track/login")
def track_login():
    try:
        if supabase_admin:
            supabase_admin.rpc('increment_login').execute()
        return {"ok": True}
    except Exception as e:
        print(f"Erro tracking login: {e}")
        return {"ok": False}

# === Atualize a rota get_admin_stats para ler os logins reais ===
@app.get("/api/admin/stats")
def get_admin_stats():
    try:
        count_users = 0
        count_projects = 0
        
        # Contagens Totais
        if supabase_admin:
            res_u = supabase_admin.table('profiles').select('id', count='exact').execute()
            count_users = res_u.count if res_u.count else 0
            res_p = supabase_admin.table('projects').select('id', count='exact').execute()
            count_projects = res_p.count if res_p.count else 0
        
        # Estatísticas do Dia (Visitas e Logins)
        visits = 0
        logins = 0 # <--- Variável nova
        
        if supabase_admin:
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                res_stats = supabase_admin.table('daily_stats').select('*').eq('date', today).single().execute()
                if res_stats.data:
                    visits = res_stats.data.get('visits', 0)
                    logins = res_stats.data.get('logins', 0) # <--- Pega do banco
            except: pass 

        return {
            "total_users": count_users,
            "total_projects": count_projects,
            "daily_visits": visits, 
            "daily_logins": logins, # <--- Agora envia o valor real
            "new_subs": 0 # Esse continua fake até configurarmos o Stripe Webhook
        }
    except Exception as e:
        print(f"Stats Error: {e}")
        return {"total_users": 0, "total_projects": 0, "daily_visits": 0, "daily_logins": 0}
# ==================== ROTAS API ====================


def get_session_or_load(sid: str) -> TramaGridSession:
    if sid in sessions: return sessions[sid]
    s = TramaGridSession()
    if s.load_from_disk(sid): sessions[sid] = s; return s
    raise HTTPException(404, "Sessão não encontrada.")

class ParamsUpdate(BaseModel):
    max_colors: int|None=None; grid_width_cells: int|None=None; brightness: float|None=None
    contrast: float|None=None; saturation: float|None=None; gamma: float|None=None
    posterize: int|None=None; highlighted_row: int|None=None; gauge_stitches: int|None=None
    gauge_rows: int|None=None; show_grid: bool|None=None
class Paint(BaseModel): x: int; y: int; color_index: int
class Pixel(BaseModel): x: int; y: int
class ColRep(BaseModel): index: int; new_hex: str
class ColDel(BaseModel): index: int
class Merge(BaseModel): from_index: int; to_index: int
class RegRep(BaseModel): x: int; y: int; w: int; h: int; from_index: int; to_index: int
class CheckoutSession(BaseModel): quantity: int; user_id: str
class UserRequest(BaseModel): user_id: str
class BatchMerge(BaseModel):
    to_index: int
    from_indices: List[int]

@app.post("/api/session")
@app.post("/api/create-session")
def create_sess():
    sid = str(uuid.uuid4()); sessions[sid] = TramaGridSession(); sessions[sid].save_to_disk(sid); return {"session_id": sid}

@app.post("/api/upload/{sid}")
async def up(sid: str, file: UploadFile = File(...)):
    s = get_session_or_load(sid); s.load_image(await file.read()); s.generate_grid(); s.save_to_disk(sid); return {"ok": True}

@app.post("/api/generate/{sid}")
def gen(sid: str):
    s = get_session_or_load(sid); s.generate_grid(); s.save_to_disk(sid); return {"ok": True}

@app.get("/api/grid/{sid}")
def grd(sid: str): return {"image_base64": get_session_or_load(sid).get_grid_base64()}

@app.get("/api/palette/{sid}")
def pal(sid: str): return get_session_or_load(sid).get_palette_info()

@app.post("/api/params/{sid}")
def par(sid: str, d: ParamsUpdate):
    s = get_session_or_load(sid)
    s._save_state()
    changed_grid = False
    for k, v in d.dict(exclude_unset=True).items():
        setattr(s, k, v)
        if k in ["show_grid", "highlighted_row"]:
            changed_grid = True
    
    if changed_grid:
        s._draw_grid()
    
    # Atualizar parâmetros não muda a imagem original, então usamos lite=True
    s.save_to_disk(sid, lite=True) 
    return {"ok": True}

@app.get("/api/params/{sid}")
def gpar(sid: str):
    s = get_session_or_load(sid); return {k: getattr(s, k) for k in ["max_colors","grid_width_cells","brightness","contrast","saturation","gamma","posterize","gauge_stitches","gauge_rows","show_grid","highlighted_row"]}

@app.post("/api/paint/{sid}")
def pnt(sid: str, d: Paint):
    s = get_session_or_load(sid)
    s.paint_cell(d.x, d.y, d.color_index)
    # Pintar um pixel é uma operação frequente: lite=True é essencial aqui
    s.save_to_disk(sid, lite=True) 
    return {"ok": True}

@app.post("/api/query-pixel/{sid}")
def qpx(sid: str, d: Pixel): return {"index": get_session_or_load(sid).get_pixel_index(d.x, d.y)}

@app.post("/api/color/replace/{sid}")
def cr(sid: str, d: ColRep):
    s = get_session_or_load(sid)
    s.replace_color(d.index, d.new_hex)
    s.save_to_disk(sid, lite=True) # Otimizado
    return {"ok": True}

@app.post("/api/color/delete/{sid}")
def cd(sid: str, d: ColDel):
    s = get_session_or_load(sid)
    s.delete_color(d.index)
    s.save_to_disk(sid, lite=True) # Otimizado
    return {"ok": True}

@app.post("/api/merge/{sid}")
def mg(sid: str, d: Merge):
    s = get_session_or_load(sid)
    s.merge_colors(d.from_index, d.to_index)
    s.save_to_disk(sid, lite=True) # Otimizado
    return {"ok": True}

@app.post("/api/region/replace/{sid}")
def rr(sid: str, d: RegRep):
    s = get_session_or_load(sid)
    s.replace_index_in_region(d.x, d.y, d.w, d.h, d.from_index, d.to_index)
    s.save_to_disk(sid, lite=True) # Otimizado
    return {"ok": True}

@app.post("/api/undo/{sid}")
def und(sid: str):
    s = get_session_or_load(sid)
    s.undo()
    s.save_to_disk(sid, lite=True) # Otimizado
    return {"ok": True}

@app.get("/api/clusters/{sid}")
def clu(sid: str): return {"clusters": get_session_or_load(sid).suggest_clusters()}

@app.get("/api/original/{sid}")
def ori(sid: str):
    s = get_session_or_load(sid)
    if not s.original: raise HTTPException(404, "Original não encontrada")
    buf = io.BytesIO(); s.original.save(buf, "PNG"); return {"image_base64": base64.b64encode(buf.getvalue()).decode()}

# === CONSUMIR CRÉDITOS ===
@app.post("/api/consume-credit")
async def consume_credit(data: UserRequest):
    if not supabase_admin: raise HTTPException(500, "Supabase Admin não configurado.")
    try:
        res = supabase_admin.table('profiles').select('*').eq('id', data.user_id).single().execute()
        if not res.data: raise HTTPException(404, "Perfil não encontrado.")
        profile = res.data
    except Exception as e: raise HTTPException(500, f"DB Error: {e}")
    has_free = not profile.get('free_generation_used', False)
    current_credits = profile.get('credits', 0)
    if not has_free and current_credits <= 0: raise HTTPException(402, "Saldo insuficiente.")
    update = {'free_generation_used': True} if has_free else {'credits': current_credits - 1}
    try: supabase_admin.table('profiles').update(update).eq('id', data.user_id).execute()
    except Exception as e: raise HTTPException(500, f"Update Error: {e}")
    return {"ok": True}

# === STRIPE ===
@app.post("/api/create-checkout-session")
async def create_checkout_session(data: CheckoutSession, request: Request):
    try:
        # Pega a URL de origem ou usa a padrão
        origin = request.headers.get('origin')
        if not origin or "localhost" in origin:
             base_url = origin # Usa localhost se estiver testando local
        else:
             base_url = "https://tramagrid.com.br" # Usa produção se não achar
        
        unit = 500
        if data.quantity == 2: unit = 495
        elif data.quantity == 10: unit = 299
        elif data.quantity == 50: unit = 179
        
        checkout = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl', 
                    'product_data': {'name': f'{data.quantity} Créditos TramaGrid'}, 
                    'unit_amount': unit
                }, 
                'quantity': 1
            }],
            mode='payment',
            # IMPORTANTE: As URLs aqui precisam ser absolutas e corretas
            success_url=f'{base_url}/buy-credits?success=true',
            cancel_url=f'{base_url}/buy-credits?canceled=true',
            client_reference_id=data.user_id,
            metadata={'credits': data.quantity}
        )
        return {"url": checkout.url}
    except Exception as e: 
        print(f"Erro Stripe: {e}")
        raise HTTPException(500, str(e))

@app.post("/api/webhook")
async def webhook_received(request: Request):
    payload = await request.body()
    
    # 1. Log para saber se a requisição chegou
    print(f"🔔 Webhook recebido! Tamanho: {len(payload)}")

    try: 
        event = stripe.Webhook.construct_event(
            payload, 
            request.headers.get('stripe-signature'), 
            STRIPE_WEBHOOK_SECRET
        )
    except Exception as e: # Capture o erro exato
        print(f"❌ Erro de Assinatura: {e}")
        raise HTTPException(400, "Webhook Error")

    if event['type'] == 'checkout.session.completed':
        s = event['data']['object']
        uid = s.get('client_reference_id')
        credits = int(s.get('metadata', {}).get('credits', 0))
        
        print(f"💰 Pagamento Aprovado: User={uid}, Credits={credits}")

        # 2. Log para ver se o Supabase Admin existe
        if not supabase_admin:
            print("❌ ERRO CRÍTICO: supabase_admin não está conectado! Verifique as chaves no .env")
            # Aqui não adianta retornar sucesso, o cliente pagou e não recebeu!
            # Mas por enquanto, só o log vai te dizer o que houve.
        
        if uid and credits > 0 and supabase_admin:
            try:
                # 1. Busca o saldo atual do usuário
                res = supabase_admin.table('profiles').select('credits').eq('id', uid).single().execute()
                
                # Se o usuário não tiver perfil, assumimos 0
                current_credits = res.data.get('credits', 0) if res.data else 0
                
                # 2. Soma os créditos comprados
                new_total = current_credits + credits
                
                # 3. Grava o novo total no banco
                supabase_admin.table('profiles').update({'credits': new_total}).eq('id', uid).execute()
                
                print(f"✅ SUCESSO: {credits} créditos adicionados para {uid}. Novo saldo: {new_total}")
                
            except Exception as e: 
                print(f"❌ ERRO CRÍTICO ao salvar no banco: {e}")

    return {"status": "success"}

# === EXPORTAR PNG (SALVAR GRÁFICO) ===
@app.get("/api/export-png/{sid}")
def export_png(sid: str):
    s = get_session_or_load(sid)
    if not s.grid_image:
        raise HTTPException(400, "Grade não gerada")
    buf = io.BytesIO()
    s.grid_image.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png", headers={"Content-Disposition": f"attachment; filename=tramagrid-grafico-{sid}.png"})

# === EXPORT PDF V7 (INLINE PREVIEW + LAYOUT CORRIGIDO) ===
@app.get("/api/export-pdf/{sid}")
def export_pdf(sid: str):
    s = get_session_or_load(sid)
    if not s.grid_image: raise HTTPException(400, "Grade não gerada")

    is_landscape = s.grid_width_cells > s.quantized.height
    page_size = landscape(A4) if is_landscape else portrait(A4)
    pg_w, pg_h = page_size
    
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=page_size)
    c.setTitle("Receita TramaGrid")

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.5*cm, pg_h - 1.5*cm, "TramaGrid")
    c.setFont("Helvetica", 9)
    info_text = f"Dim: {s.grid_width_cells}x{s.quantized.height} pts | Data: {datetime.now().strftime('%d/%m/%Y')}"
    if s.gauge_stitches and s.gauge_rows:
        cm_w = round(s.grid_width_cells * 10 / s.gauge_stitches, 1)
        cm_h = round(s.quantized.height * 10 / s.gauge_rows, 1)
        info_text += f" | Tam: {cm_w}x{cm_h}cm"
    c.drawRightString(pg_w - 1.5*cm, pg_h - 1.5*cm, info_text)

    # Grade
    grid_img = s.grid_image.copy()
    img_buffer = io.BytesIO()
    grid_img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    avail_w, avail_h = pg_w - 2*cm, pg_h - 4*cm
    iw, ih = grid_img.size
    scale = min(avail_w / iw, avail_h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(ImageReader(img_buffer), (pg_w - dw)/2, pg_h - 2.5*cm - dh, width=dw, height=dh)
    
    # Legenda Compacta
    c.showPage()
    palette = s.get_palette_info()
    safe_symbols = string.ascii_uppercase + string.ascii_lowercase + "!@#$%&*?+-"
    symbol_map = {}
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5*cm, pg_h - 2*cm, "Legenda de Cores")
    c.setFont("Helvetica", 9)
    
    cols = 4 if is_landscape else 3
    col_width = (pg_w - 3*cm) / cols
    row_height = 0.8*cm
    start_y = pg_h - 3*cm
    curr_x, curr_y = 1.5*cm, start_y
    
    for i, color in enumerate(palette):
        sym = safe_symbols[i % len(safe_symbols)]
        symbol_map[color['index']] = sym
        c.setFillColor(HexColor(color['hex']))
        c.rect(curr_x, curr_y - 0.4*cm, 0.4*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(HexColor("#000000"))
        c.drawString(curr_x + 0.6*cm, curr_y - 0.3*cm, f"{sym} : {color['hex']} ({color['count']} pts)")
        curr_x += col_width
        if (i + 1) % cols == 0:
            curr_x = 1.5*cm
            curr_y -= row_height
        if curr_y < 2*cm:
            c.showPage()
            curr_y = pg_h - 2*cm
            curr_x = 1.5*cm

    # Instruções (TABELA ZEBRADA + ZIGZAG)
    if curr_y > pg_h - 10*cm: curr_y -= 1.5*cm
    else:
        c.showPage()
        curr_y = pg_h - 2*cm

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor("#000000"))
    c.drawString(1.5*cm, curr_y, "Instruções Linha a Linha")
    curr_y -= 1*cm
    
    w, h = s.quantized.size
    available_text_width = pg_w - 3.5*cm 

    for row in range(h-1, -1, -1):
        line = []
        current_idx = None
        count = 0
        
        # ZigZag:
        line_num = h - row
        is_odd_line = (line_num % 2 != 0)
        
        arrow = "←" if is_odd_line else "→"
        
        # Se Impar: D->E (Pixel Final -> Pixel 0)
        col_range = range(w-1, -1, -1) if is_odd_line else range(w)
        
        for col in col_range:
            idx = s.quantized.getpixel((col, row))
            sym = symbol_map.get(idx, "?")
            if idx == current_idx: count += 1
            else:
                if current_idx is not None: line.append(f"{count}x{sym}")
                current_idx = idx
                count = 1
        if current_idx is not None: line.append(f"{count}x{sym}")
        
        full_text = f"L{line_num} [{arrow}]:  " + "  ".join(line)
        
        lines = simpleSplit(full_text, "Helvetica", 9, available_text_width)
        row_height = (len(lines) * 0.5 * cm) + 0.2 * cm 
        
        if curr_y - row_height < 1.5*cm:
            c.showPage()
            curr_y = pg_h - 2*cm
            
        if line_num % 2 == 1:
            c.setFillColor(HexColor("#F2F2F2"))
            c.rect(1.5*cm, curr_y - row_height, pg_w - 3*cm, row_height, fill=1, stroke=0)
            
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(0.5)
        c.line(1.5*cm, curr_y - row_height, pg_w - 1.5*cm, curr_y - row_height)
        
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica", 9)
        text_y = curr_y - 0.4*cm
        for txt_line in lines:
            c.drawString(1.7*cm, text_y, txt_line) 
            text_y -= 0.5*cm
            
        curr_y -= row_height

    c.save()
    buffer.seek(0)
    
    # ATENÇÃO: Mudou para "inline" -> Abre no navegador
    return Response(content=buffer.read(), media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=tramagrid-{sid}.pdf"})


# --- NOVOS ENDPOINTS ---

# No arquivo backend/tramagrid_backend.py

@app.post("/api/color/add/{sid}")
def add_color_to_palette(sid: str, d: Dict[str, str]):
    s = get_session_or_load(sid)
    hex_val = d.get("hex")
    if not hex_val or len(hex_val) != 7 or hex_val[0] != '#':
        raise HTTPException(400, "Hex inválido")
    
    try:
        rgb = (int(hex_val[1:3], 16), int(hex_val[3:5], 16), int(hex_val[5:7], 16))
    except:
        raise HTTPException(400, "Cor inválida")

    # 1. Verifica se a cor já existe
    for idx, color in s.palette.items():
        if color == rgb:
            return {"index": idx}
    
    # 2. LIMPEZA: Remove cores que não estão sendo usadas na imagem
    # Isso libera espaço na paleta deletando cores antigas
    if s.quantized:
        used_colors = set(c[1] for c in s.quantized.getcolors(maxcolors=1000))
        s.palette = {k: v for k, v in s.palette.items() if k in used_colors}
        s.custom_palette = {k: v for k, v in s.custom_palette.items() if k in used_colors}

    # 3. EXPANSÃO: Se mesmo limpando estiver cheio, aumenta o limite
    if len(s.palette) >= s.max_colors:
        if s.max_colors < 256:
            s.max_colors = min(256, s.max_colors + 16)
        else:
            raise HTTPException(400, "Limite máximo de 256 cores reais atingido.")
    
    # 4. Encontra um índice livre
    new_idx = 0
    while new_idx in s.palette:
        new_idx += 1
        
    s.palette[new_idx] = s.custom_palette[new_idx] = rgb
    
    # Atualiza a grade visualmente se necessário (apenas se for repaint, mas aqui é só add palette)
    # Mas como adicionamos uma cor nova, precisamos garantir que ela exista na estrutura interna
    
    s.save_to_disk(sid, lite=True)
    return {"index": new_idx}

@app.get("/api/row-summary/{sid}/{row_num}")
def get_row_summary(sid: str, row_num: int):
    s = get_session_or_load(sid)
    if not s.quantized: return {"summary": []}
    
    w, h = s.quantized.size
    # Converte o número da carreira (1...H) para o índice da imagem (H-1...0)
    img_row = h - row_num
    if img_row < 0 or img_row >= h: return {"summary": []}
    
    summary = []
    curr_idx = None
    count = 0
    
    # ZigZag: Linhas ímpares (←), Linhas pares (→)
    col_range = range(w-1, -1, -1) if row_num % 2 != 0 else range(w)
    
    for x in col_range:
        idx = s.quantized.getpixel((x, img_row))
        if idx == curr_idx: count += 1
        else:
            if curr_idx is not None:
                summary.append({"count": count, "hex": f"#{s.palette[curr_idx][0]:02x}{s.palette[curr_idx][1]:02x}{s.palette[curr_idx][2]:02x}"})
            curr_idx, count = idx, 1
    summary.append({"count": count, "hex": f"#{s.palette[curr_idx][0]:02x}{s.palette[curr_idx][1]:02x}{s.palette[curr_idx][2]:02x}"})
    return {"summary": summary}

@app.post("/api/merge-batch/{sid}")
def mgb(sid: str, d: BatchMerge):
    s = get_session_or_load(sid)
    # Filtra para não tentar mesclar a cor com ela mesma
    clean_list = [i for i in d.from_indices if i != d.to_index]
    if clean_list:
        s.merge_many_colors(clean_list, d.to_index)
        s.save_to_disk(sid, lite=True) # Usa o modo leve que criamos antes!
    return {"ok": True}

@app.get("/api/proxy-image")
def proxy_image(url: str):
    if not url: 
        raise HTTPException(400, "URL necessária")
    
    try:
        # O Backend baixa a imagem (ele não sofre bloqueio de CORS)
        r = requests.get(url, stream=True)
        r.raise_for_status()
        
        # E repassa para o Frontend com os cabeçalhos corretos
        return Response(
            content=r.content, 
            media_type=r.headers.get('Content-Type', 'image/png'),
            headers={"Access-Control-Allow-Origin": "*"} 
        )
    except Exception as e:
        print(f"Erro no proxy: {e}")
        raise HTTPException(404, "Imagem não encontrada ou inacessível")