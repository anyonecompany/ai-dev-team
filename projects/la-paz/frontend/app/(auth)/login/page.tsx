"use client";

import { Circle } from "lucide-react";
import { useAuth } from "@/lib/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

export default function LoginPage() {
  const { signInWithGoogle, signInWithGithub } = useAuth();

  return (
    <Card>
      <CardHeader className="text-center">
        <Circle className="mx-auto mb-2 h-8 w-8 fill-primary text-primary" aria-hidden="true" />
        <CardTitle>La Paz 로그인</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button className="w-full" variant="outline" onClick={signInWithGoogle}>
          Google로 로그인
        </Button>
        <Button className="w-full" variant="outline" onClick={signInWithGithub}>
          GitHub로 로그인
        </Button>
        <p className="text-center text-xs text-muted-foreground">
          로그인 없이도 서비스를 이용할 수 있습니다.
        </p>
      </CardContent>
    </Card>
  );
}
