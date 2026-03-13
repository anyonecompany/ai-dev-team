import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/chat", "/simulate", "/login", "/callback"],
    },
    sitemap: `${process.env.NEXT_PUBLIC_SITE_URL || "https://lapaz.ai"}/sitemap.xml`,
  };
}
