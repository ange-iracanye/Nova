import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.novaai.tutor",
  appName: "Nova AI",
  webDir: "../frontend/dist",
  bundledWebRuntime: false,
  android: { allowMixedContent: false },
  ios: { contentInset: "automatic" },
  server: { cleartext: false },
};

export default config;
