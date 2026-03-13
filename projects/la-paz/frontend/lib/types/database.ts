/**
 * Supabase 생성 타입 정의
 *
 * 실제 타입은 `supabase gen types typescript` 명령으로 생성합니다.
 * 생성된 타입으로 이 파일을 교체하세요.
 *
 * 사용법:
 *   npx supabase gen types typescript --project-id <project-ref> > lib/types/database.ts
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      [key: string]: {
        Row: Record<string, unknown>;
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
  };
}
