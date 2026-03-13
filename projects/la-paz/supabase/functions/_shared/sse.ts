// ================================================================
// La Paz — SSE Response Utilities (SSE_FORMAT.md)
// ================================================================

import { corsHeaders } from "./cors.ts";
import type { SSEEventType } from "./types.ts";

export function sseHeaders(): Record<string, string> {
  return {
    ...corsHeaders,
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  };
}

export function formatSSE(event: SSEEventType, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

export function createSSEStream(
  handler: (writer: SSEWriter) => Promise<void>,
): Response {
  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      const writer: SSEWriter = {
        send(event: SSEEventType, data: unknown) {
          controller.enqueue(encoder.encode(formatSSE(event, data)));
        },
        close() {
          controller.close();
        },
      };

      try {
        await handler(writer);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "An unexpected error occurred";
        writer.send("error", {
          code: "internal_error",
          message,
          fallback: false,
        });
      } finally {
        try {
          writer.close();
        } catch {
          // already closed
        }
      }
    },
  });

  return new Response(stream, { headers: sseHeaders() });
}

export interface SSEWriter {
  send(event: SSEEventType, data: unknown): void;
  close(): void;
}
