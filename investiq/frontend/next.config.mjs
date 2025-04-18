/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Desabilitando o webpack para não fazer hot reload durante desenvolvimento
  webpack: (config, { isServer }) => {
    // Para evitar refresh constante em desenvolvimento
    if (!isServer) {
      config.watchOptions = {
        ...config.watchOptions,
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
};

export default nextConfig;
