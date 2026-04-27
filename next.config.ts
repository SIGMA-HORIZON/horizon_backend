import type { NextConfig } from "next";

const nextConfig: NextConfig = {
<<<<<<< HEAD
  transpilePackages: ['@novnc/novnc'],
  webpack: (config) => {
    config.experiments = { ...config.experiments, topLevelAwait: true };

    config.module.rules.push({
      test: /@novnc\/novnc\/.*\.js$/,
      parser: {
        topLevelAwait: true,
      },
    });

    return config;
=======
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
>>>>>>> 95157c8 (mes modifs)
  },
};

export default nextConfig;
