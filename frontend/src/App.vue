<template>
  <div class="app-layout">
    <header class="top-nav">
      <div class="nav-left">
        <router-link to="/" class="nav-btn">GENEROWANIE</router-link>
        <router-link to="/postacie" class="nav-btn">POSTACIE</router-link>
        <router-link to="/tlumaczenie" class="nav-btn">TŁUMACZENIE</router-link>
      </div>
      <div class="v-line"></div>
    </header>

    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style>
@font-face {
  font-family: "Bitroad Mono";
  src: url(/fonts/BitroadMono-RegularMono.ttf) format("truetype");
}

@font-face {
  font-family: "Breite Regular";
  src: url(/fonts/BreiteRegular.otf) format("opentype");
}

@font-face {
  font-family: "Clash Display";
  src: url(/fonts/ClashDisplay-Variable.ttf) format("truetype");
}

* {
  box-sizing: border-box;
}

:root {
  --col-orange: #d36b00;
  --col-dark: #1a120b;
  --col-brown: #3c2a21;
  --col-lbrown: #d5cea3;
  --col-light: #e5e5cb;

  --font-bitroad: "Bitroad Mono", Courier, monospace;
  --font-breite: "Breite Regular", sans-serif;
  --font-clash: "Clash Display", sans-serif;
}

html {
  overflow-x: hidden;
}

body {
  margin: 0;
  background-color: var(--col-light);
  font-family: "Bitroad Mono", Courier, monospace;
  color: var(--col-dark);
}

.app-layout {
  height: 100vh;
  overflow: hidden;
}

button {
  font-family: var(--font-bitroad);
  cursor: pointer;
}

.top-nav {
  display: grid;
  grid-template-columns: 1fr 4px 1fr;
  justify-content: space-between;
  align-items: center;
  padding: 20px 20px;
  border-bottom: 3px solid var(--border-color);
  background-color: var(--col-lbrown);
  border-bottom: 4px solid var(--col-brown);
}

.nav-btn {
  padding: 5px 15px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  text-decoration: none;
  color: var(--border-color);
  font-weight: bold;
  cursor: pointer;
}

.v-line {
  width: 4px;
  background-color: var(--col-brown);
  align-self: stretch;
  margin: -20px 0;
}

.nav-left {
  display: flex;
}

.nav-right {
  display: flex;
  justify-content: flex-end;
}

.space-r {
  margin-right: 10px;
}

.nav-btn.router-link-active {
  background-color: #fff;
}

.main-content {
  flex: 1;

  height: 100%;
}
</style>
