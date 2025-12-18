<script setup>
    import { ref, onMounted } from 'vue'
    
    const props = defineProps({
      beforeImage: String,
      afterImage: String
    })
    
    const sliderValue = ref(50)
    const isDragging = ref(false)
    
    function onMove(e) {
      if (!isDragging.value) return
      
      // Lógica para suportar tanto Mouse quanto Touch
      const clientX = e.touches ? e.touches[0].clientX : e.clientX
      const rect = e.currentTarget.getBoundingClientRect()
      const x = Math.max(0, Math.min(clientX - rect.left, rect.width))
      sliderValue.value = (x / rect.width) * 100
    }
    </script>
    
    <template>
      <div 
        class="compare-container" 
        @mousemove="onMove"
        @touchmove="onMove"
        @mousedown="isDragging = true"
        @mouseup="isDragging = false"
        @mouseleave="isDragging = false"
        @touchstart="isDragging = true"
        @touchend="isDragging = false"
      >
        <div class="img-wrapper after">
          <img :src="afterImage" alt="Resultado" />
          <span class="label">TramaGrid</span>
        </div>
    
        <div 
          class="img-wrapper before" 
          :style="{ clipPath: `inset(0 ${100 - sliderValue}% 0 0)` }"
        >
          <img :src="beforeImage" alt="Original" />
          <span class="label">Original</span>
        </div>
    
        <div 
          class="slider-handle" 
          :style="{ left: `${sliderValue}%` }"
        >
          <div class="handle-line"></div>
          <div class="handle-circle">↔</div>
        </div>
      </div>
    </template>
    
    <style scoped>
    .compare-container {
      position: relative;
      width: 100%;
      height: 100%;
      min-height: 400px;
      border-radius: 16px;
      overflow: hidden;
      cursor: col-resize;
      user-select: none;
      border: 1px solid #333;
      background: #000;
    }
    
    .img-wrapper {
      position: absolute;
      top: 0; left: 0; width: 100%; height: 100%;
    }
    
    .img-wrapper img {
      width: 100%; height: 100%;
      object-fit: cover;
      pointer-events: none;
    }
    
    .label {
      position: absolute; top: 20px;
      background: rgba(0,0,0,0.6); color: white;
      padding: 4px 12px; border-radius: 20px;
      font-size: 0.8rem; font-weight: bold;
      backdrop-filter: blur(4px);
      z-index: 10;
    }
    .before .label { left: 20px; }
    .after .label { right: 20px; }
    
    .slider-handle {
      position: absolute; top: 0; bottom: 0;
      width: 4px; background: #e67e22;
      transform: translateX(-50%);
      z-index: 20;
      pointer-events: none; /* Deixa o evento passar para o container */
      box-shadow: 0 0 10px rgba(230,126,34,0.5);
    }
    
    .handle-circle {
      position: absolute; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      width: 32px; height: 32px;
      background: #e67e22; color: #fff;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-weight: bold;
      box-shadow: 0 0 15px rgba(0,0,0,0.5);
    }
    </style>