import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for production Docker builds only
  ...(process.env.NODE_ENV === 'production' && {
    output: "standalone",
  }),

  // Enable strict mode in development for better debugging
  reactStrictMode: process.env.NODE_ENV === 'development',

  // Bundle analyzer for development
  ...(process.env.ANALYZE === 'true' && {
    bundleAnalyzer: {
      enabled: true,
      openAnalyzer: true,
    },
  }),

  // Enable experimental features
  experimental: {
    // Enable server actions
    serverActions: {
      bodySizeLimit: "2mb",
    },
  },

  // Environment variables available on client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // Optimize bundle
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Optimize images
  images: {
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Turbopack config (silence warning about webpack config)
  turbopack: {},

  // Webpack optimizations (used in production builds)
  webpack: (config, { dev, isServer }) => {
    // Optimize bundle splitting
    if (!dev && !isServer) {
      config.optimization.splitChunks.chunks = 'all';
      config.optimization.splitChunks.cacheGroups = {
        ...config.optimization.splitChunks.cacheGroups,
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        api: {
          test: /[\\/]src[\\/]lib[\\/]/,
          name: 'api',
          chunks: 'all',
        },
      };
    }

    return config;
  },
};

export default nextConfig;
