import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ['@novnc/novnc'],
  experimental: {
    esmExternals: 'loose',
  },
  webpack: (config) => {
    // Top-level await is needed for some ESM features
    config.experiments = { ...config.experiments, topLevelAwait: true };
    
    return config;
  },
};

export default nextConfig;
