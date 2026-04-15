import { createRouter, createWebHistory } from "vue-router";
import GenerateView from "./views/GenerateView.vue";
import CharactersView from "./views/CharacterView.vue";
import TranslateView from "./views/TranslateView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "generowanie",
      component: GenerateView,
    },
    {
      path: "/postacie",
      name: "postacie",
      component: CharactersView,
    },
    {
      path: "/tlumaczenie",
      name: "tlumaczenie",
      component: TranslateView,
    },
  ],
});

export default router;
