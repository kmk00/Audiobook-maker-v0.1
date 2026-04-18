<script setup>
defineProps({
  text: {
    type: String,
    default: "Ładowanie...",
  },
});
</script>

<template>
  <div class="loading-overlay">
    <div class="loading-content">
      <div class="spinning-diamond"></div>
      <p class="loading-text">{{ text }}</p>
    </div>
  </div>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(
    26,
    18,
    11,
    0.6
  ); /* var(--col-dark) z przezroczystością */
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.spinning-diamond {
  width: 50px;
  height: 50px;
  background-color: transparent;
  border: 4px solid var(--col-light);
  transform: rotate(45deg);
  animation: spin 1.5s infinite ease-in-out;
}

.loading-text {
  font-family: var(--font-bitroad), monospace;
  color: var(--col-light);
  font-size: 1.2rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin: 0;
}

@keyframes spin {
  0% {
    transform: rotate(45deg) scale(1);
  }
  50% {
    transform: rotate(225deg) scale(1.2);
    border-color: var(--col-orange);
  }
  100% {
    transform: rotate(405deg) scale(1);
  }
}
</style>
