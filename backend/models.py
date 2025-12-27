from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Modelos para parâmetros de atualização
class ParamsUpdate(BaseModel):
    max_colors: Optional[int] = None
    grid_width_cells: Optional[int] = None
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    saturation: Optional[float] = None
    gamma: Optional[float] = None
    posterize: Optional[int] = None
    highlighted_row: Optional[int] = None
    gauge_stitches: Optional[int] = None
    gauge_rows: Optional[int] = None
    show_grid: Optional[bool] = None

# Modelos para operações de pintura
class Paint(BaseModel):
    x: int
    y: int
    color_index: int

# Modelo para consulta de pixel
class Pixel(BaseModel):
    x: int
    y: int

# Modelo para substituição de cor
class ColRep(BaseModel):
    index: int
    new_hex: str

# Modelo para exclusão de cor
class ColDel(BaseModel):
    index: int

# Modelo para mesclagem de cores
class Merge(BaseModel):
    from_index: int
    to_index: int

# Modelo para substituição regional
class RegRep(BaseModel):
    x: int
    y: int
    w: int
    h: int
    from_index: int
    to_index: int

# Modelo para checkout do Stripe
class CheckoutSession(BaseModel):
    quantity: int
    user_id: str

# Modelo para solicitação de usuário
class UserRequest(BaseModel):
    user_id: str

# Modelo para mesclagem em lote
class BatchMerge(BaseModel):
    to_index: int
    from_indices: List[int]

# Modelo para post do blog
class BlogPostModel(BaseModel):
    title: str
    slug: str
    content: str
    image_url: str
    excerpt: str
    published: bool = True
