import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A stray lockfile in the home folder otherwise makes Next guess the wrong root.
  turbopack: { root: __dirname },
};

export default nextConfig;
