from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import TramaGridSession

def undo(session: "TramaGridSession"):
    """Desfaz a última operação com reconstrução otimizada de imagem"""
    if not session.history:
        return

    # Salva o estado atual no REDO antes de voltar
    current_state = {
        'quantized_data': session.quantized.tobytes(),
        'quantized_size': session.quantized.size,
        'quantized_mode': session.quantized.mode,
        'palette': session.palette.copy(),
        'custom_palette': session.custom_palette.copy()
    }
    session.redo_history.append(current_state)

    last_state = session.history.pop()
    # Reconstrói a imagem a partir dos dados binários
    from PIL import Image
    session.quantized = Image.frombytes(last_state['quantized_mode'], last_state['quantized_size'], last_state['quantized_data'])
    session.palette = last_state['palette']
    session.custom_palette = last_state['custom_palette']
    session._draw_grid()

def redo(session: "TramaGridSession"):
    """Refaz a última operação desfeita com reconstrução otimizada de imagem"""
    if not session.redo_history:
        return

    state = session.redo_history.pop()
    # Antes de aplicar o redo, salva onde estamos no undo
    current_state = {
        'quantized_data': session.quantized.tobytes(),
        'quantized_size': session.quantized.size,
        'quantized_mode': session.quantized.mode,
        'palette': session.palette.copy(),
        'custom_palette': session.custom_palette.copy()
    }
    session.history.append(current_state)

    # Reconstrói a imagem a partir dos dados binários
    from PIL import Image
    session.quantized = Image.frombytes(state['quantized_mode'], state['quantized_size'], state['quantized_data'])
    session.palette = state['palette']
    session.custom_palette = state['custom_palette']
    session._draw_grid()
