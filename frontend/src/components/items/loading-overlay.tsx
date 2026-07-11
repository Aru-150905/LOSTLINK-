"use client";

import { Loader2, Sparkles } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface LoadingOverlayProps {
  message?: string;
  progress?: number;
}

export function LoadingOverlay({
  message = "Processing with AI...",
  progress,
}: LoadingOverlayProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md rounded-2xl border bg-card p-8 shadow-lg">
        <div className="flex flex-col items-center text-center">
          <div className="relative mb-6">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <Sparkles className="absolute -right-1 -top-1 h-5 w-5 text-amber-500" />
          </div>
          <h3 className="text-lg font-semibold">{message}</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Generating embeddings and searching for matches...
          </p>
          {progress !== undefined && (
            <Progress value={progress} className="mt-6 w-full" />
          )}
        </div>
      </div>
    </div>
  );
}
