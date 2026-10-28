import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A stray lockfile in the home folder otherwise makes Next guess the wrong root.
  // The dev badge sits on top of the phone total bar.
  devIndicators: false,
  turbopack: { root: __dirname },
};

export default nextConfig;
