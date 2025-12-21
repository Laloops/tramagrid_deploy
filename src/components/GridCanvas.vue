<script setup>
  import { ref, onMounted, onUnmounted, watch, computed } from "vue";
  import { 
    getGridImage, updateParams, paintCell, getPixelIndex, 
    mergeColors, replaceColorInRegion, activeColorIndex, 
    getPalette, eventBus, addColor, getRowSummary 
  } from "../api.js"; 
  import { showToast, showConfirm } from "../toast.js"; 
  import { 
    Undo2, Ruler, Pencil, PaintBucket, 
    Pipette, ChevronRight, ChevronLeft,
    SquareDashedMousePointer, ZoomIn, X, Undo,
    ChevronUp, ChevronDown, ArrowLeft, ArrowRight
  } from "lucide-vue-next";
  
  const imageSrc = ref("");
  const zoom = ref(1.0);
  const highlightedRow = ref(-1);
  const currentTool = ref('brush'); 
  const isHudMinimized = ref(false);
  const colorPickerInput = ref(null);
  const fullPalette = ref([]); 
  const rowSummary = ref([]);
  
  const BACKEND_MARGIN = 20; 
  const CELL_SIZE = 22;
  
  // === VARIÁVEIS DO CANVAS (ZOOM E PAN) ===
  const panX = ref(0), panY = ref(0);
  const isDragging = ref(false);
  const dragStart = ref({ x: 0, y: 0 });
  const isSpacePressed = ref(false); // Controle da tecla Espaço
  
  const selectionRect = ref(null); 
  const isSelecting = ref(false);
  const selStart = ref({ x: 0, y: 0 });

  // === ARRASTAR O HUD (CAIXA DE FERRAMENTAS) ===
  const hudPos = ref({ x: window.innerWidth - 190, y: 200 }); 
  const isHudDragging = ref(false);
  const hudDragOffset = ref({ x: 0, y: 0 });

  function startHudDrag(e) {
    if (e.target.closest('button') || e.target.closest('input') || e.target.closest('.color-block')) return;

    isHudDragging.value = true;
    hudDragOffset.value = {
      x: e.clientX - hudPos.value.x,
      y: e.clientY - hudPos.value.y
    };
    window.addEventListener('mousemove', onHudDrag);
    window.addEventListener('mouseup', stopHudDrag);
  }

  function onHudDrag(e) {
    if (!isHudDragging.value) return;
    hudPos.value = {
      x: e.clientX - hudDragOffset.value.x,
      y: e.clientY - hudDragOffset.value.y
    };
  }

  function stopHudDrag() {
    isHudDragging.value = false;
    window.removeEventListener('mousemove', onHudDrag);
    window.removeEventListener('mouseup', stopHudDrag);
  }
  

  const activeColorHex = computed(() => {
    const color = fullPalette.value.find(c => c.index === activeColorIndex.value);
    return color ? color.hex : '#ffffff';
  });
  
  async function refresh() {
    const data = await getGridImage();
    imageSrc.value = data;
    const pal = await getPalette();
    fullPalette.value = Array.isArray(pal) ? pal : pal.palette || [];
  }
  
  watch(highlightedRow, async (newVal) => {
    await updateParams({ highlighted_row: newVal });
    if (newVal !== -1) {
      try {
        rowSummary.value = await getRowSummary(newVal); 
      } catch (e) { console.error(e); rowSummary.value = []; }
    } else {
      rowSummary.value = [];
    }
    refresh();
  });
  
  // === CONTROLES DE TECLADO (ESPAÇO PARA ARRASTAR) ===
  function handleKeyDown(e) {
    if (e.code === 'Space' && !isSpacePressed.value) {
      isSpacePressed.value = true;
    }
  }

  function handleKeyUp(e) {
    if (e.code === 'Space') {
      isSpacePressed.value = false;
      isDragging.value = false; // Para o arraste se soltar o espaço
    }
  }

  onMounted(() => {
    refresh();
    eventBus.addEventListener('refresh', refresh);
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
  });
  
  onUnmounted(() => {
    eventBus.removeEventListener('refresh', refresh);
    window.removeEventListener('mousemove', onHudDrag);
    window.removeEventListener('mouseup', stopHudDrag);
    window.removeEventListener('keydown', handleKeyDown);
    window.removeEventListener('keyup', handleKeyUp);
  });
  
  // === LÓGICA DE ZOOM (RODA DO MOUSE) ===
// === LÓGICA DE ZOOM E PAN (TRACKPAD FRIENDLY) ===
function handleWheel(e) {
    e.preventDefault(); // Impede o navegador de rolar a página inteira

    // Detecta se é gesto de PINÇA (Trackpad) ou CTRL+SCROLL
    // A maioria dos navegadores ativa e.ctrlKey automaticamente no gesto de pinça
    if (e.ctrlKey) {
      // --- MODO ZOOM (Pinça ou Ctrl+Roda) ---
      const zoomIntensity = 0.05; // Mais suave para trackpad
      // No trackpad, deltaY é pequeno, então normalizamos um pouco
      const delta = -e.deltaY; 
      const direction = delta > 0 ? 1 : -1;
      
      const newZoom = Math.max(0.1, Math.min(10.0, zoom.value + (direction * zoomIntensity * zoom.value)));

      // Zoom focado no ponteiro do mouse
      const rect = e.currentTarget.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const worldX = (mouseX - panX.value) / zoom.value;
      const worldY = (mouseY - panY.value) / zoom.value;

      panX.value = mouseX - worldX * newZoom;
      panY.value = mouseY - worldY * newZoom;
      zoom.value = newZoom;

    } else {
      // --- MODO PAN (Scroll normal com 2 dedos) ---
      // Inverte os eixos se necessário, mas geralmente:
      // deltaX = scroll horizontal, deltaY = scroll vertical
      panX.value -= e.deltaX;
      panY.value -= e.deltaY;
    }
  }

  // === SUPORTE A TOUCH (Mapeia toque para mouse) ===
  function handleTouchStart(e) {
    if (e.touches.length === 1) {
      // Toque único = Clique esquerdo
      const touch = e.touches[0];
      // Emulamos o evento de mouse para reutilizar a lógica existente
      onMouseDown({
        clientX: touch.clientX,
        clientY: touch.clientY,
        button: 0, // Botão esquerdo
        preventDefault: () => e.preventDefault()
      });
    } else if (e.touches.length === 2) {
      // Dois dedos = Iniciar Arraste (Pan)
      isDragging.value = true;
      const t1 = e.touches[0];
      dragStart.value = { x: t1.clientX - panX.value, y: t1.clientY - panY.value };
    }
  }

  function handleTouchMove(e) {
    e.preventDefault(); // Impede arrastar a página do navegador
    if (isDragging.value && e.touches.length === 2) {
      const t1 = e.touches[0];
      panX.value = t1.clientX - dragStart.value.x;
      panY.value = t1.clientY - dragStart.value.y;
    } else if (e.touches.length === 1) {
      // Move a ferramenta (pincel ou seleção)
      const touch = e.touches[0];
      onMouseMove({
        clientX: touch.clientX,
        clientY: touch.clientY,
        preventDefault: () => {}
      });
    }
  }

  function handleTouchEnd(e) {
    onMouseUp();
  }

  function moveRow(delta) {
    const imgEl = document.getElementById('grid-canvas');
    if (!imgEl) return;
    const maxRows = Math.round((imgEl.naturalHeight - 80) / CELL_SIZE);
    
    let next = highlightedRow.value + delta;
    if (next < 1) next = 1;
    if (next > maxRows) next = maxRows;
    highlightedRow.value = next;
  }
  
  function getGridCoords(clientX, clientY) {
    const canvasEl = document.querySelector('.canvas'); 
    if (!canvasEl) return { gridX: -1, gridY: -1 };
    const rect = canvasEl.getBoundingClientRect();
    // Ajuste da fórmula para considerar o zoom e pan atuais
    const relX = (clientX - rect.left - panX.value) / zoom.value;
    const relY = (clientY + 2 - rect.top - panY.value) / zoom.value;
    const gridX = Math.floor((relX - BACKEND_MARGIN) / CELL_SIZE);
    const gridY = Math.floor((relY - BACKEND_MARGIN) / CELL_SIZE);
    return { gridX, gridY };
  }
  
  // --- 1. Adicione estas definições logo ANTES da função handleClick ---

// Função auxiliar para evitar chamadas excessivas
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Cria uma versão do refresh que espera 300ms após o último clique para rodar
const debouncedRefresh = debounce(() => {
  refresh();
}, 300);


// --- 2. Aqui está a função handleClick modificada e otimizada ---

async function handleClick(e) {
  // Verificações iniciais de estado (arrastando, selecionando, espaço apertado)
  if (isDragging.value || isSelecting.value || isSpacePressed.value) return; 
  
  const { gridX, gridY } = getGridCoords(e.clientX, e.clientY);
  
  // Se clicou fora da grade, ignora
  if (gridX < 0 || gridY < 0) return; 

  // --- Ferramenta: RÉGUA ---
  if (currentTool.value === 'ruler') {
    const imgEl = document.getElementById('grid-canvas');
    // Cálculo da altura corrigido conforme seu código original
    const hc = Math.round((imgEl.naturalHeight - 80) / CELL_SIZE);
    const rowNumber = hc - gridY;
    highlightedRow.value = (highlightedRow.value === rowNumber) ? -1 : rowNumber;
    return;
  }

  // Pega o índice da cor no pixel clicado
  const clickedIndex = await getPixelIndex(gridX, gridY);
  if (clickedIndex === -1) return;

  // --- Ferramenta: PINCEL (Otimizada) ---
  if (currentTool.value === 'brush') {
    // CORREÇÃO DE PERFORMANCE:
    // 1. Chamamos paintCell sem 'await' bloqueante no UI thread principal,
    //    usando .then() para garantir que o envio ocorreu.
    // 2. Chamamos debouncedRefresh() em vez de refresh() direto. 
    //    Isso acumula os cliques rápidos e só recarrega a imagem no final.
    paintCell(gridX, gridY).then(() => {
      debouncedRefresh();
    });

  // --- Ferramenta: CONTA-GOTAS ---
  } else if (currentTool.value === 'picker') {
    activeColorIndex.value = clickedIndex;
    currentTool.value = 'brush';
    showToast("Cor capturada!", "info");

  // --- Ferramenta: BALDE DE TINTA ---
  } else if (currentTool.value === 'bucket') {
    const target = activeColorIndex.value;
    
    // Se a cor já é a mesma, não faz nada
    if (target === clickedIndex) return;

    if (selectionRect.value) {
      // Substituição em região (mantém await pois é operação única e pesada)
      await replaceColorInRegion(
        selectionRect.value.x, 
        selectionRect.value.y, 
        selectionRect.value.w, 
        selectionRect.value.h, 
        clickedIndex, 
        target
      );
      refresh(); // Refresh imediato é ok aqui (clique único)
    } else {
      // Substituição global
      if (await showConfirm("Substituir cor no gráfico todo?")) { 
        await mergeColors(clickedIndex, target); 
        refresh(); // Refresh imediato é ok aqui
      }
    }
  }
}
  
  async function toggleRuler() {
    if (currentTool.value === 'ruler') {
      currentTool.value = 'brush';
      highlightedRow.value = -1;
    } else {
      currentTool.value = 'ruler';
    }
  }
  
  async function handleColorPicked(e) {
    try {
      const newIndex = await addColor(e.target.value);
      activeColorIndex.value = newIndex;
      refresh();
    } catch (err) { showToast("Limite atingido", "warning"); }
  }
  
  function onMouseDown(e) {
    // Permite arrastar se for botão do meio (1) OU botão esquerdo (0) com Espaço apertado
    if (e.button === 1 || (e.button === 0 && isSpacePressed.value)) { 
      isDragging.value = true;
      dragStart.value = { x: e.clientX - panX.value, y: e.clientY - panY.value };
      return;
    }
    if (currentTool.value === 'select') {
      const { gridX, gridY } = getGridCoords(e.clientX, e.clientY);
      isSelecting.value = true;
      selStart.value = { x: gridX, y: gridY };
      selectionRect.value = { x: gridX, y: gridY, w: 1, h: 1 };
    }
  }
  
  function onMouseMove(e) {
    if (isDragging.value) {
      panX.value = e.clientX - dragStart.value.x;
      panY.value = e.clientY - dragStart.value.y;
    } else if (isSelecting.value) {
      const { gridX, gridY } = getGridCoords(e.clientX, e.clientY);
      const x = Math.min(selStart.value.x, gridX);
      const y = Math.min(selStart.value.y, gridY);
      const w = Math.abs(gridX - selStart.value.x) + 1;
      const h = Math.abs(gridY - selStart.value.y) + 1;
      selectionRect.value = { x, y, w, h };
    }
  }
  
  function onMouseUp() { isDragging.value = false; isSelecting.value = false; }
  </script>
  
  <template>
    <div class="canvas-wrapper">
      <div 
        class="side-hud" 
        :class="{ minimized: isHudMinimized }"
        :style="{ left: hudPos.x + 'px', top: hudPos.y + 'px' }"
        @mousedown="startHudDrag"
      >
        <button class="toggle-btn" @click.stop="isHudMinimized = !isHudMinimized">
          <ChevronRight v-if="!isHudMinimized" /><ChevronLeft v-else />
        </button>
  
        <div class="hud-inner custom-scroll">
          <div class="section">
            <span class="label">Cor Ativa</span>
            <div class="color-row">
              <input type="color" ref="colorPickerInput" @change="handleColorPicked" style="position:absolute; opacity:0; pointer-events:none;" />
              <div class="color-block" :style="{ background: activeColorHex }" @click="colorPickerInput.click()"></div>
              <button @click="currentTool = 'picker'" :class="{ active: currentTool === 'picker' }"><Pipette :size="18" /></button>
            </div>
          </div>
  
          <div class="divider"></div>
  
          <div class="section">
            <span class="label">Ferramentas</span>
            <div class="grid-tools">
              <button @click="currentTool = 'brush'" :class="{ active: currentTool === 'brush' }" title="Pincel"><Pencil :size="20" /></button>
              <button @click="currentTool = 'bucket'" :class="{ active: currentTool === 'bucket' }" title="Balde"><PaintBucket :size="20" /></button>
              <button @click="currentTool = 'select'" :class="{ active: currentTool === 'select' }" title="Seleção"><SquareDashedMousePointer :size="20" /></button>
              <button @click="refresh" title="Undo"><Undo :size="20" /></button>
            </div>
          </div>
  
          <div class="divider"></div>
  
          <div class="section">
            <button @click="toggleRuler" :class="{ active: currentTool === 'ruler' || highlightedRow !== -1 }" class="wide-btn">
              <Ruler :size="18" /> <span>Régua</span>
            </button>
            
            <div v-if="highlightedRow !== -1" class="ruler-panel">
               <div class="nav-row">
                  <button @click="moveRow(1)" class="nav-btn"><ChevronUp :size="20" /></button>
                  <div class="row-num">
                    <small>CARR.</small><strong>{{ highlightedRow }}</strong>
                  </div>
                  <button @click="moveRow(-1)" class="nav-btn"><ChevronDown :size="20" /></button>
               </div>
  
               <div v-if="rowSummary.length" class="summary-box">
                  <div class="dir-header" :class="{ 'dir-left': highlightedRow % 2 !== 0, 'dir-right': highlightedRow % 2 === 0 }">
                    <ArrowLeft v-if="highlightedRow % 2 !== 0" :size="20" stroke-width="2.5" />
                    <ArrowRight v-else :size="20" stroke-width="2.5" />
                  </div>
  
                  <div class="pills-list">
                    <div v-for="(item, idx) in rowSummary" :key="idx" class="pill">
                      <div class="dot" :style="{ background: item.hex }"></div>
                      <span>{{ item.count }}</span>
                    </div>
                  </div>
               </div>
            </div>
  
            <div v-if="selectionRect" class="selection-status">
              <span>Seleção Ativa</span>
              <button @click="selectionRect = null" class="btn-close-sel"><X :size="14" /></button>
            </div>
          </div>
        </div>
      </div>
  
      <div 
        class="canvas" 
        @mousedown="onMouseDown" 
        @mousemove="onMouseMove" 
        @mouseup="onMouseUp" 
        @mouseleave="onMouseUp"
        @wheel.prevent="handleWheel" 
        @touchstart.passive="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
        :style="{ cursor: isSpacePressed || isDragging ? 'grab' : 'crosshair' }"
      >
        <div class="transform-container" :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoom})`, transformOrigin: '0 0' }">
          <img v-if="imageSrc" id="grid-canvas" :src="imageSrc" @click="handleClick" draggable="false" class="pixel-art" />
          <div v-if="selectionRect" class="selection-overlay" 
               :style="{ left: (BACKEND_MARGIN + selectionRect.x * CELL_SIZE) + 'px', top: (BACKEND_MARGIN + selectionRect.y * CELL_SIZE) + 'px', width: (selectionRect.w * CELL_SIZE) + 'px', height: (selectionRect.h * CELL_SIZE) + 'px' }">
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <style scoped>
  .canvas-wrapper { position: relative; width: 100%; height: 100%; background: #0b0b0b; overflow: hidden; }
  
  /* HUD - CSS AJUSTADO PARA MOVER */
  .side-hud { 
    position: fixed; 
    /* Right e Top removidos aqui pois são controlados pelo JS (style inline) */
    width: 165px; 
    background: rgba(30, 30, 31, 0.95); backdrop-filter: blur(10px); 
    border: 1px solid #444; border-radius: 16px; z-index: 900; 
    transition: width 0.3s; /* Removi transição de posição para não dar lag ao arrastar */
    box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
    cursor: move; /* Cursor de movimento */
    user-select: none;
  }
  
  /* Quando minimizado, apenas encolhe a largura */
  .side-hud.minimized { 
    width: 50px; 
    /* Removi 'right: -5px' para não pular de lugar */
    overflow: hidden;
  }
  
  .side-hud.minimized .hud-inner { opacity: 0; pointer-events: none; }
  
  .toggle-btn { position: absolute; left: -12px; top: 20px; width: 24px; height: 24px; background: #e67e22; border: none; border-radius: 50%; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 10; }
  .hud-inner { padding: 15px; display: flex; flex-direction: column; gap: 12px; max-height: 70vh; overflow-y: auto; }
  .section { display: flex; flex-direction: column; gap: 8px; }
  .label { font-size: 0.6rem; text-transform: uppercase; color: #777; font-weight: 800; }
  
  .color-row { display: flex; gap: 8px; align-items: center; }
  .color-block { width: 44px; height: 44px; border-radius: 8px; border: 2px solid #555; cursor: pointer; }
  .grid-tools { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
  button { background: #252526; border: 1px solid #333; color: #ccc; border-radius: 8px; height: 38px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
  button:hover { background: #333; color: white; }
  button.active { background: #e67e22; border-color: #ff9d42; color: white; }
  .wide-btn { width: 100%; gap: 10px; font-weight: 600; font-size: 0.8rem; }
  
  /* PAINEL DA RÉGUA */
  .ruler-panel { background: rgba(0,0,0,0.3); border-radius: 8px; padding: 8px; margin-top: 5px; border: 1px solid #333; }
  .nav-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .nav-btn { width: 30px; height: 30px; background: #1a1a1a; border: 1px solid #444; color: #e67e22; border-radius: 6px; }
  .row-num { text-align: center; line-height: 1; color: white; }
  .row-num small { font-size: 0.5rem; color: #888; display: block; }
  
  /* SÓ SETA (Direção) */
  .dir-header { display: flex; align-items: center; justify-content: center; padding: 6px; border-radius: 4px; margin-bottom: 8px; }
  .dir-left { background: rgba(52, 152, 219, 0.2); color: #3498db; }
  .dir-right { background: rgba(230, 126, 34, 0.2); color: #e67e22; }
  
  .pills-list { display: flex; flex-wrap: wrap; gap: 4px; justify-content: center; }
  .pill { display: flex; align-items: center; gap: 5px; background: #252526; padding: 3px 8px; border-radius: 12px; border: 1px solid #444; color: white; font-size: 0.75rem; font-weight: bold; }
  .dot { width: 10px; height: 10px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.3); }
  
  .divider { height: 1px; background: #333; }
  .selection-status { background: rgba(230, 126, 34, 0.1); border: 1px solid rgba(230, 126, 34, 0.3); border-radius: 8px; padding: 6px 10px; font-size: 0.7rem; color: #e67e22; display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
  .btn-close-sel { background: transparent; border: none; color: #e74c3c; width: auto; height: auto; }
  
  /* CANVAS: sem cursor fixo aqui, usamos style binding no template */
  .canvas { width: 100%; height: 100%; }
  
  .pixel-art { image-rendering: pixelated; }
  .selection-overlay { position: absolute; border: 2px dashed #f1c40f; background: rgba(241, 196, 15, 0.1); pointer-events: none; }
  .custom-scroll::-webkit-scrollbar { width: 3px; }
  .custom-scroll::-webkit-scrollbar-thumb { background: #444; }
  </style>