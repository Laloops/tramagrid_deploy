from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import TramaGridSession

def undo(session: "TramaGridSession"):
    """Desfaz a última operação"""
    if not session.history:
        return

    # Salva o estado atual no REDO antes de voltar
    session.redo_history.append({
        'quantized': session.quantized.copy(),
        'palette': session.palette.copy(),
        'custom_palette': session.custom_palette.copy()
    })

    last_state = session.history.pop()
    session.quantized = last_state['quantized']
    session.palette = last_state['palette']
    session.custom_palette = last_state['custom_palette']
    session._draw_grid()

def redo(session: "TramaGridSession"):
    """Refaz a última operação desfeita"""
    if not session.redo_history:
        return

    state = session.redo_history.pop()
    # Antes de aplicar o redo, salva onde estamos no undo
    session.history.append({
        'quantized': session.quantized.copy(),
        'palette': session.palette.copy(),
        'custom_palette': session.custom_palette.copy()
    })
    session.quantized = state['quantized']
    session.palette = state['palette']
    session.custom_palette = state['custom_palette']
    session._draw_grid()
