import os
from pathlib import Path
from dotenv import load_dotenv

# Carregamento do arquivo .env
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

if env_path.exists():
    print("Arquivo .env carregado com sucesso")
else:
    print("AVISO: Arquivo .env nao encontrado")

# Configurações do Stripe
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Configurações de CORS (origens permitidas)
ALLOWED_ORIGINS = [
    "https://tramagrid.com.br",
    "https://www.tramagrid.com.br",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

# Configurações gerais
DATA_DIR = "data"

print("Configuracoes carregadas com sucesso!")
