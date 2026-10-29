import type { NextConfig } from "next";

// A static export: the site is plain files, so GitHub Pages can serve it. The workflow sets
// NEXT_PUBLIC_BASE_PATH to the repository name; locally both are empty.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  output: "export",
  basePath,
  trailingSlash: true,
  images: { unoptimized: true },
  // The dev badge sits on top of the phone total bar.
  devIndicators: false,
  // A stray lockfile in the home folder otherwise makes Next guess the wrong root.
  turbopack: { root: __dirname },
};

export default nextConfig;
