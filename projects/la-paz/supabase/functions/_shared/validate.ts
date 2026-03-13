// ================================================================
// La Paz — Input Validation with Zod
// ================================================================

import { z } from "npm:zod@3";

export const ChatRequestSchema = z.object({
  message: z.string().min(1).max(2000),
  session_id: z.string().uuid().optional(),
  locale: z.enum(["ko", "en"]),
});

export const SearchRequestSchema = z.object({
  query: z.string().min(1).max(500),
  limit: z.number().int().min(1).max(50).optional().default(10),
  locale: z.enum(["ko", "en"]).optional().default("ko"),
});

export const ParseRumorsRequestSchema = z.object({
  article_ids: z.array(z.string().uuid()).optional(),
  max_articles: z.number().int().min(1).max(100).optional().default(20),
});

export const SimulateTransferRequestSchema = z.object({
  player_id: z.string().uuid(),
  target_team_id: z.string().uuid(),
});

export const SimulateMatchRequestSchema = z.object({
  home_team_id: z.string().uuid(),
  away_team_id: z.string().uuid(),
});

export function validateRequest<T>(
  schema: z.ZodSchema<T>,
  data: unknown,
): { success: true; data: T } | { success: false; error: string } {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }
  const messages = result.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`);
  return { success: false, error: messages.join("; ") };
}
