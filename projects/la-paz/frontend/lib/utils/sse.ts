export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export async function* parseSSE(response: Response): AsyncGenerator<SSEEvent> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop()!;

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7);
      } else if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield { event: currentEvent, data } as SSEEvent;
        } catch {
          // skip malformed JSON
        }
      }
    }
  }
}
