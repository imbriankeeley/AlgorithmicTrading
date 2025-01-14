/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "@": ".",
      "@/components": "./components",
      "@/lib": "./lib",
      "@/styles": "./styles",
      "@/types": "./types",
      "@/app": "./app",
      "@/hooks": "./hooks",
      "@/utils": "./utils",
    };
    return config;
  },
};

module.exports = nextConfig;
