/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

declare module "@meforma/vue-toaster" {
  import type { Plugin } from "vue";

  interface ToasterApi {
    show(message: string, options?: Record<string, unknown>): unknown;
    clear(): void;
    success(message: string, options?: Record<string, unknown>): unknown;
    error(message: string, options?: Record<string, unknown>): unknown;
    info(message: string, options?: Record<string, unknown>): unknown;
    warning(message: string, options?: Record<string, unknown>): unknown;
  }

  export function createToaster(options?: Record<string, unknown>): ToasterApi;
  export const Toaster: Plugin;
  export const Positions: Record<string, string>;
  const ToasterPlugin: Plugin;
  export default ToasterPlugin;
}
