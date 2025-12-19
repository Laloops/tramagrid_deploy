export async function getDeviceFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const txt = 'TramaGrid-Security-v1';
    ctx.textBaseline = "top";
    ctx.font = "14px 'Arial'";
    ctx.textBaseline = "alphabetic";
    ctx.fillStyle = "#f60";
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = "#069";
    ctx.fillText(txt, 2, 15);
    ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
    ctx.fillText(txt, 4, 17);
    
    const dataURI = canvas.toDataURL();
    // Transforma a imagem base64 em um Hash numérico simples
    let hash = 0;
    if (dataURI.length === 0) return hash;
    for (let i = 0; i < dataURI.length; i++) {
      const char = dataURI.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString() + "-" + navigator.hardwareConcurrency + "-" + navigator.deviceMemory;
  }