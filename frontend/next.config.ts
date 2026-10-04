import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Use Webpack instead of Turbopack for Windows compatibility
  turbopack: {},
  webpack: (config) => {
    return config;
  },
};

export default nextConfig;
