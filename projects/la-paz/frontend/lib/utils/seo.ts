import type { Metadata } from "next";

const SITE_NAME = "La Paz";
const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lapaz.ai";

/**
 * 공통 메타데이터 생성 유틸리티
 */
export function createMetadata({
  title,
  description,
  path = "",
  type = "website",
}: {
  title: string;
  description: string;
  path?: string;
  type?: "website" | "article";
}): Metadata {
  const url = `${BASE_URL}${path}`;

  return {
    title,
    description,
    openGraph: {
      title: `${title} | ${SITE_NAME}`,
      description,
      url,
      siteName: SITE_NAME,
      type,
      locale: "ko_KR",
    },
    twitter: {
      card: "summary_large_image",
      title: `${title} | ${SITE_NAME}`,
      description,
    },
    alternates: {
      canonical: url,
    },
  };
}
