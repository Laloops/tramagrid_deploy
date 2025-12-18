<script setup>
  import { ref, onMounted, onUnmounted } from 'vue'
  import gsap from 'gsap'
  
  const props = defineProps({
    color: { type: String, default: '#e67e22' },
    strokeWidth: { type: Number, default: 4 },
    tension: { type: Number, default: 50 } // Quanto a corda estica
  })
  
  const svgRef = ref(null)
  const pathRef = ref(null)
  const uid = Math.random().toString(36).substr(2, 9)
  
  let width = 0
  let height = 0
  const controlPoint = { x: 0, y: 0 }
  
  const updatePath = () => {
    if (!pathRef.value) return
    const w = width || 100 
    const h = height || 100
    // Curva quadrática: Início -> Ponto de Controle (Mouse) -> Fim
    const d = `M -20,${h / 2} Q ${controlPoint.x},${controlPoint.y} ${w + 20},${h / 2}`
    pathRef.value.setAttribute('d', d)
  }
  
  const handleMouseMove = (e) => {
    if (!svgRef.value) return
    const rect = svgRef.value.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    const centerY = height / 2
    
    // FÍSICA: A corda é mais rígida nas pontas (Math.sin)
    const xRatio = Math.max(0, Math.min(1, mouseX / width))
    const tensionFactor = Math.sin(xRatio * Math.PI) // 0 nas pontas, 1 no meio
    const distY = Math.abs(mouseY - centerY)
    const grabRadius = 80 // Distância para "pegar" a corda
  
    if (distY < grabRadius) {
      const deltaY = mouseY - centerY
      const dampedY = centerY + (deltaY * tensionFactor)
  
      gsap.to(controlPoint, {
        x: mouseX, 
        y: dampedY, 
        duration: 0.1, 
        overwrite: true, 
        ease: "power2.out",
        onUpdate: updatePath
      })
    } else {
      releaseString()
    }
  }
  
  const releaseString = () => {
    if (Math.abs(controlPoint.y - height / 2) < 2) return
    // Efeito Elástico ao soltar
    gsap.to(controlPoint, {
      y: height / 2, 
      duration: 1.5, 
      ease: "elastic.out(1.2, 0.1)", 
      onUpdate: updatePath
    })
  }
  
  const resize = () => {
    if (svgRef.value) {
      width = svgRef.value.clientWidth
      height = svgRef.value.clientHeight
      if (!gsap.isTweening(controlPoint)) {
          controlPoint.x = width / 2
          controlPoint.y = height / 2
          updatePath()
      }
    }
  }
  
  onMounted(() => {
    setTimeout(() => {
        resize()
        window.addEventListener('resize', resize)
        if (svgRef.value) {
          svgRef.value.addEventListener('mousemove', handleMouseMove)
          svgRef.value.addEventListener('mouseleave', releaseString)
        }
    }, 100)
  })
  
  onUnmounted(() => {
    window.removeEventListener('resize', resize)
  })
  </script>
  
  <template>
    <div class="yarn-container" ref="svgRef">
      <svg width="100%" height="100%">
        <defs>
          <filter :id="`filt-${uid}`" x="-20%" y="-50%" width="140%" height="200%">
            <feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="3" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="6" xChannelSelector="R" yChannelSelector="G" />
          </filter>
          <linearGradient :id="`grad-${uid}`" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" :stop-color="color" />
              <stop offset="100%" stop-color="#f1c40f" />
          </linearGradient>
        </defs>
        
        <path :d="pathRef?.getAttribute('d')" fill="none" stroke="rgba(0,0,0,0.3)" :stroke-width="strokeWidth+4" stroke-linecap="round" style="transform:translateY(8px);opacity:0.4;" />
        
        <path ref="pathRef" fill="none" :stroke="`url(#grad-${uid})`" :stroke-width="strokeWidth" stroke-linecap="round" :filter="`url(#filt-${uid})`" />
      </svg>
    </div>
  </template>
  
  <style scoped>
  .yarn-container { width: 100%; height: 100%; min-height: 200px; position: relative; overflow: visible; z-index: 10; cursor: crosshair; }
  svg { overflow: visible; display: block; width: 100%; height: 100%; }
  </style>