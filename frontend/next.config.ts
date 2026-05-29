import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle for the Docker image (see frontend/Dockerfile).
  output: "standalone",
};

export default nextConfig;
