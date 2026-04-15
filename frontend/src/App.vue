<template>
  <div class="app-layout">
    <header class="top-nav">
      <div class="nav-left"></div>
      <div class="nav-center">
        <router-link to="/" class="nav-btn">GENEROWANIE</router-link>
        <router-link to="/postacie" class="nav-btn">POSTACIE</router-link>
        <router-link to="/tlumaczenie" class="nav-btn">TŁUMACZENIE</router-link>
      </div>
      <div class="nav-right">
        <button class="settings-btn">⚙️</button>
      </div>
    </header>

    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style>
/* Bazowe style pod Twój design */
:root {
  --bg-color: #efe4d0; /* Beżowy z Twoich screenów */
  --border-color: #3e2723; /* Ciemny brąz */
  --btn-bg: #e3d5ba;
}

body {
  margin: 0;
  background-color: var(--bg-color);
  font-family: "Courier New", Courier, monospace; /* Zmień na swój retro font */
  color: var(--border-color);
}

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 3px solid var(--border-color);
  background-color: var(--bg-color);
}

.nav-center {
  display: flex;
  gap: 10px;
}

.nav-btn {
  padding: 5px 15px;
  border: 2px solid var(--border-color);
  background-color: var(--btn-bg);
  text-decoration: none;
  color: var(--border-color);
  font-weight: bold;
  cursor: pointer;
}

.nav-btn.router-link-active {
  background-color: #fff; /* Wyróżnienie aktywnej zakładki */
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>
