import path from 'path'
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  experimental: {
    // Next.js 15 specific features can be enabled here
  },
  webpack: (config, { isServer, defaultLoaders }) => {
    // Add alias for @ to resolve features folder
    config.resolve.alias['@/'] = path.join(__dirname)
    config.resolve.alias['@/'] = path.join(__dirname, '..')
    config.resolve.alias['@/'] = path.join(__dirname, '..', '..')
    return config
  },
}

export default nextConfig
