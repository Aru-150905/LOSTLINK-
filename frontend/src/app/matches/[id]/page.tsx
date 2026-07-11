"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";
import { MatchCard } from "@/components/matches/match-card";
import { LoadingOverlay } from "@/components/items/loading-overlay";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { claimItem, getStoredMatches, searchMatches } from "@/lib/api";
import type { MatchResult } from "@/types";

export default function MatchResultsPage() {
  const params = useParams();
  const router = useRouter();
  const itemId = params.id as string;
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  const loadMatches = async () => {
    setLoading(true);
    try {
      // Read-only fetch: does not re-run the search or re-send notifications.
      const data = await getStoredMatches(itemId);
      setMatches(data);
    } catch {
      toast.error("Failed to load matches. Please sign in.");
      router.push("/auth");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMatches();
  }, [itemId]);

  const handleRescan = async () => {
    setScanning(true);
    try {
      const data = await searchMatches(itemId);
      setMatches(data);
      toast.success(`Found ${data.length} matches`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  const handleClaim = async (matchedItemId: string) => {
    try {
      await claimItem(matchedItemId, "I believe this is my item.");
      toast.success("Claim submitted! Awaiting review.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Claim failed");
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      {scanning && <LoadingOverlay message="Re-scanning for matches..." />}

      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-amber-500" />
            <h1 className="text-3xl font-bold">Match Results</h1>
          </div>
          <p className="text-muted-foreground">
            Top probable matches ranked by AI confidence score
          </p>
        </div>
        <Button onClick={handleRescan} disabled={scanning}>
          Re-scan matches
        </Button>
      </div>

      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-96 rounded-xl" />
          ))}
        </div>
      ) : matches.length === 0 ? (
        <div className="rounded-xl border border-dashed py-16 text-center">
          <Sparkles className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="text-xl font-semibold">No matches found yet</h2>
          <p className="mt-2 text-muted-foreground">
            We&apos;ll notify you when a potential match is discovered
          </p>
          <Button className="mt-6" onClick={handleRescan}>
            Scan again
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {matches.map((match) => (
            <MatchCard
              key={match.matched_item_id}
              match={match}
              onClaim={handleClaim}
            />
          ))}
        </div>
      )}
    </div>
  );
}
