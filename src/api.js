import { ref } from 'vue'

// Definição da URL base da API
const RENDER_URL = 'https://tramagrid-api.onrender.com';
export const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000' : RENDER_URL);

// --- ESTADO GLOBAL ---
export const sessionId = ref(localStorage.getItem('tramagrid_session_id') || '') 
export const eventBus = new EventTarget()
export const activeColorIndex = ref(0)

export const mergeState = ref({
  isActive: false, 
  sourceIndex: null 
})

// --- SESSÃO ---
export async function createSession() {
  try {
    const res = await fetch(`${API_BASE}/api/session`, { method: 'POST' })
    if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`)
    const data = await res.json()
    
    sessionId.value = data.session_id
    localStorage.setItem('tramagrid_session_id', data.session_id)
    console.log("Sessão criada:", sessionId.value)
  } catch (err) {
    console.error("Erro ao criar sessão:", err)
    sessionId.value = ''
    localStorage.removeItem('tramagrid_session_id')
    throw err
  }
}

// Verifica se a sessão antiga ainda existe no servidor
export async function restoreSession() {
  const savedId = localStorage.getItem('tramagrid_session_id');
  if (!savedId) return false;

  try {
    // Adicionamos timestamp (?t=) para evitar cache na verificação
    const res = await fetch(`${API_BASE}/api/params/${savedId}?t=${Date.now()}`);
    if (res.ok) {
      sessionId.value = savedId;
      console.log("Sessão restaurada:", savedId);
      eventBus.dispatchEvent(new Event('refresh'));
      return true;
    } else {
      console.warn("Sessão antiga expirou.");
      sessionId.value = '';
      localStorage.removeItem('tramagrid_session_id');
      return false;
    }
  } catch (e) {
    console.error("Erro ao tentar restaurar sessão:", e);
    return false;
  }
}

export async function uploadImage(file) {
  if (!sessionId.value) throw new Error("Sem sessão ativa para upload")
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/api/upload/${sessionId.value}`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`Erro upload: ${await res.text()}`)
}

export async function generateGrid() {
  if (!sessionId.value) throw new Error("Sem sessão ativa para gerar grade")
  const res = await fetch(`${API_BASE}/api/generate/${sessionId.value}`, { method: 'POST' })
  if (!res.ok) throw new Error(`Erro generate: ${await res.text()}`)
  eventBus.dispatchEvent(new Event('refresh'))
}

// --- FERRAMENTAS ---

export async function paintCell(x, y) {
  if (!sessionId.value) return;
  // Voltamos ao AWAIT para garantir que a ação foi gravada
  const res = await fetch(`${API_BASE}/api/paint/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x, y, color_index: activeColorIndex.value })
  });
  return res.ok;
}

export async function getPixelIndex(x, y) {
  if (!sessionId.value) return -1
  try {
    const res = await fetch(`${API_BASE}/api/query-pixel/${sessionId.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ x, y })
    })
    const data = await res.json()
    return data.index ?? -1
  } catch { return -1 }
}

// No arquivo src/api.js

export async function undoLastAction() {
  if (!sessionId.value) return false;
  try {
    const res = await fetch(`${API_BASE}/api/undo/${sessionId.value}`, { method: 'POST' });
    eventBus.dispatchEvent(new Event('refresh'));
    return res.ok; // Agora retorna o status real do servidor
  } catch (e) {
    console.error("Erro no Undo:", e);
    return false;
  }
}

export async function redoLastAction() {
  if (!sessionId.value) return false;
  try {
    const res = await fetch(`${API_BASE}/api/redo/${sessionId.value}`, { method: 'POST' });
    eventBus.dispatchEvent(new Event('refresh'));
    return res.ok; // Retorna o status real do servidor
  } catch (e) {
    console.error("Erro no Redo:", e);
    return false;
  }
}

export async function mergeColors(fromIndex, toIndex) {
  if (!sessionId.value) return
  await fetch(`${API_BASE}/api/merge/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from_index: fromIndex, to_index: toIndex })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function getColorClusters() {
  if (!sessionId.value) return []
  const res = await fetch(`${API_BASE}/api/clusters/${sessionId.value}`)
  const data = await res.json()
  return data.clusters || []
}

// --- VISUALIZAÇÃO ---

export async function getPalette() {
  if (!sessionId.value) return []
  // CORREÇÃO DE CACHE: Adicionado ?t=... para atualizar cores
  const res = await fetch(`${API_BASE}/api/palette/${sessionId.value}?t=${Date.now()}`)
  return await res.json()
}

export async function getGridImage() {
  if (!sessionId.value) return ""
  // CORREÇÃO DE CACHE: Adicionado ?t=... para o Desfazer funcionar
  const res = await fetch(`${API_BASE}/api/grid/${sessionId.value}?t=${Date.now()}`)
  const data = await res.json()
  if (!data) return ""
  if (typeof data === "string") return data
  if (data.image_base64) {
    return data.image_base64.startsWith("data:") 
      ? data.image_base64 
      : `data:image/png;base64,${data.image_base64}`
  }
  return ""
}

export async function updateParams(params) {
  if (!sessionId.value) return
  await fetch(`${API_BASE}/api/params/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
}

export async function replaceColor(index, new_hex) {
  if (!sessionId.value) return
  await fetch(`${API_BASE}/api/color/replace/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index, new_hex })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function deleteColor(index) {
  if (!sessionId.value) return
  await fetch(`${API_BASE}/api/color/delete/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function getParams() {
  if (!sessionId.value) return {}
  const res = await fetch(`${API_BASE}/api/params/${sessionId.value}`)
  return await res.json()
}

export async function replaceColorInRegion(x, y, w, h, fromIndex, toIndex) {
  if (!sessionId.value) return
  await fetch(`${API_BASE}/api/region/replace/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      x, y, w, h, 
      from_index: fromIndex, 
      to_index: toIndex 
    })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function loadProjectFromSupabase(project) {
  try {
    const imageUrl = project.image_url || project.image_path
    if (!imageUrl) throw new Error("Projeto sem imagem.")

    let blob;
    try {
      const response = await fetch(imageUrl, { mode: 'cors' });
      if (!response.ok) throw new Error("Falha direta");
      blob = await response.blob();
    } catch (directError) {
      console.warn("CORS detectado, tentando via Proxy...", directError);
      const proxyUrl = `${API_BASE}/api/proxy-image?url=${encodeURIComponent(imageUrl)}`;
      const proxyRes = await fetch(proxyUrl);
      if (!proxyRes.ok) throw new Error("Falha também no proxy");
      blob = await proxyRes.blob();
    }

    const file = new File([blob], "project_source.png", { type: "image/png" })

    await createSession()
    if (!sessionId.value) throw new Error("Falha ao criar sessão")

    await uploadImage(file)

    if (project.settings) {
      await updateParams(project.settings)
    } else if (project.params) {
      await updateParams(project.params)
    }

    await generateGrid()
    return true
  } catch (e) {
    console.error("Erro ao abrir projeto:", e)
    sessionId.value = ''
    throw e
  }
}

// --- DOWNLOADS ---
export async function downloadPdf() {
  if (!sessionId.value) return
  try {
    const res = await fetch(`${API_BASE}/api/export-pdf/${sessionId.value}`)
    if (!res.ok) throw new Error("Erro ao gerar PDF")
    
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tramagrid-receita-${Date.now()}.pdf`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (e) {
    console.error("Erro no download PDF:", e)
    throw e
  }
}

export async function downloadPng() {
  if (!sessionId.value) return
  try {
    const res = await fetch(`${API_BASE}/api/export-png/${sessionId.value}`)
    if (!res.ok) throw new Error("Erro ao baixar imagem")
    
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tramagrid-grafico-${Date.now()}.png`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (e) {
    console.error("Erro no download PNG:", e)
    throw e
  }
}

export async function addColor(hex) {
  if (!sessionId.value) return
  const res = await fetch(`${API_BASE}/api/color/add/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hex })
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || "Erro ao adicionar cor")
  }
  const data = await res.json()
  return data.index
}

export async function getRowSummary(rowNum) {
  if (!sessionId.value) return []
  const res = await fetch(`${API_BASE}/api/row-summary/${sessionId.value}/${rowNum}`)
  const data = await res.json()
  return data.summary || []
}

export async function mergeBatch(fromIndices, toIndex) {
  if (!sessionId.value) return
  await fetch(`${API_BASE}/api/merge-batch/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from_indices: fromIndices, to_index: toIndex })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

