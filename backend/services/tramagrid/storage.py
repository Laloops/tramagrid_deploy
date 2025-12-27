import os
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import TramaGridSession

from ..config import DATA_DIR

def save_to_disk(session: "TramaGridSession", session_id: str, lite: bool = False):
    """Salva o estado da sessão no disco"""
    s_dir = os.path.join(DATA_DIR, session_id)
    os.makedirs(s_dir, exist_ok=True)

    meta = {
        "params": {
            "grid_width_cells": session.grid_width_cells,
            "max_colors": session.max_colors,
            "brightness": session.brightness,
            "contrast": session.contrast,
            "saturation": session.saturation,
            "gamma": session.gamma,
            "posterize": session.posterize,
            "gauge_stitches": session.gauge_stitches,
            "gauge_rows": session.gauge_rows,
            "show_grid": session.show_grid,
            "highlighted_row": session.highlighted_row
        },
        "palette": {str(k): v for k, v in session.palette.items()},
        "custom_palette": {str(k): v for k, v in session.custom_palette.items()}
    }

    with open(os.path.join(s_dir, "meta.json"), "w") as f:
        json.dump(meta, f)

    # OTIMIZAÇÃO: Se for 'lite', NÃO salva a original de novo
    if session.original and not lite:
        session.original.save(os.path.join(s_dir, "original.png"))

    if session.quantized:
        session.quantized.save(os.path.join(s_dir, "quantized.png"))

def load_from_disk(session: "TramaGridSession", session_id: str) -> bool:
    """Carrega o estado da sessão do disco"""
    s_dir = os.path.join(DATA_DIR, session_id)
    meta_path = os.path.join(s_dir, "meta.json")
    if not os.path.exists(meta_path):
        return False

    try:
        with open(meta_path, "r") as f:
            meta = json.load(f)

        p = meta.get("params", {})
        for k, v in p.items():
            if hasattr(session, k):
                setattr(session, k, v)

        session.palette = {int(k): tuple(v) for k, v in meta.get("palette", {}).items()}
        session.custom_palette = {int(k): tuple(v) for k, v in meta.get("custom_palette", {}).items()}

        if os.path.exists(os.path.join(s_dir, "original.png")):
            from PIL import Image
            session.original = Image.open(os.path.join(s_dir, "original.png")).convert("RGB")

        if os.path.exists(os.path.join(s_dir, "quantized.png")):
            from PIL import Image
            session.quantized = Image.open(os.path.join(s_dir, "quantized.png")).convert("P")
            flat_palette = [0] * 768
            for idx, (r, g, b) in session.palette.items():
                if idx < 256:
                    flat_palette[idx*3:idx*3+3] = [r, g, b]
            session.quantized.putpalette(flat_palette)

        if session.quantized:
            session._draw_grid()

        return True
    except Exception as e:
        print(f"Erro ao carregar sessão {session_id}: {e}")
        return False

def _save_state(session: "TramaGridSession"):
    """Salva o estado atual antes de uma modificação"""
    if not session.quantized:
        return

    # Salva o estado ATUAL antes da modificação
    state = {
        'quantized': session.quantized.copy(),
        'palette': session.palette.copy(),
        'custom_palette': session.custom_palette.copy()
    }

    if len(session.history) >= 30:
        session.history.pop(0)

    session.history.append(state)
    session.redo_history = []  # Limpa o refazer ao fazer nova ação
