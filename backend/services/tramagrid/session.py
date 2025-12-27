import os
from pathlib import Path
from typing import Optional, Dict, Tuple, List, Any
from PIL import Image

from .storage import save_to_disk, load_from_disk, _save_state
from .image_ops import load_image, paint_cell, get_pixel_index, replace_index_in_region, get_row_summary
from .palette import (
    get_palette_info, replace_color, merge_colors, merge_many_colors,
    delete_color, add_color_to_palette, suggest_clusters
)
from .grid import generate_grid, draw_grid, get_grid_base64
from .history import undo, redo
from .export import export_png, export_pdf

class TramaGridSession:
    """Classe principal da sessão TramaGrid que delega operações para módulos especializados"""

    def __init__(self):
        self.original: Optional[Image.Image] = None
        self.processed: Optional[Image.Image] = None
        self.quantized: Optional[Image.Image] = None
        self.palette: Dict[int, Tuple[int, int, int]] = {}
        self.custom_palette: Dict[int, Tuple[int, int, int]] = {}
        self.grid_image: Optional[Image.Image] = None
        self.history: List[Dict[str, Any]] = []
        self.redo_history: List[Dict[str, Any]] = []

        # Parâmetros de configuração
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
        # REMOVIDA: self.history: List[Dict[str, Any]] = [] (estava duplicada)

    # Delegações para storage.py
    def save_to_disk(self, session_id: str, lite: bool = False):
        save_to_disk(self, session_id, lite)

    def load_from_disk(self, session_id: str) -> bool:
        return load_from_disk(self, session_id)

    def _save_state(self):
        _save_state(self)

    # Delegações para image_ops.py
    def load_image(self, file_bytes: bytes) -> None:
        load_image(self, file_bytes)

    def paint_cell(self, x, y, idx):
        paint_cell(self, x, y, idx)

    def get_pixel_index(self, x, y):
        return get_pixel_index(self, x, y)

    def replace_index_in_region(self, x, y, w, h, f, t):
        replace_index_in_region(self, x, y, w, h, f, t)

    def get_row_summary(self, row_num: int):
        return get_row_summary(self, row_num)

    # Delegações para palette.py
    def get_palette_info(self) -> List[Dict]:
        return get_palette_info(self)

    def replace_color(self, idx, hex_val):
        replace_color(self, idx, hex_val)

    def merge_colors(self, f, t):
        merge_colors(self, f, t)

    def merge_many_colors(self, from_list, to_index):
        merge_many_colors(self, from_list, to_index)

    def delete_color(self, idx):
        delete_color(self, idx)

    def add_color_to_palette(self, hex_val: str):
        return add_color_to_palette(self, hex_val)

    def suggest_clusters(self, threshold=50.0):
        return suggest_clusters(self, threshold)

    # Delegações para grid.py
    def generate_grid(self) -> None:
        generate_grid(self)

    def _draw_grid(self) -> None:
        draw_grid(self)

    def get_grid_base64(self) -> str:
        return get_grid_base64(self)

    # Delegações para history.py
    def undo(self):
        undo(self)

    def redo(self):
        redo(self)

    # Delegações para export.py
    def export_png(self):
        return export_png(self)

    def export_pdf(self, sid: str):
        return export_pdf(self, sid)
