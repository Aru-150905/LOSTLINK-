"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Package, RefreshCw } from "lucide-react";
import { ItemCard } from "@/components/matches/match-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getMyItems, markResolved, searchMatches } from "@/lib/api";
import type { Item } from "@/types";

export default function MyItemsPage() {
  const router = useRouter();
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);

  const loadItems = async () => {
    setLoading(true);
    try {
      const data = await getMyItems();
      setItems(data);
    } catch {
      toast.error("Please sign in to view your items");
      router.push("/auth");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, []);

  const handleRefreshMatches = async (itemId: string) => {
    try {
      const matches = await searchMatches(itemId);
      toast.success(`Found ${matches.length} matches`);
      router.push(`/matches/${itemId}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Search failed");
    }
  };

  const handleMarkResolved = async (itemId: string) => {
    try {
      await markResolved(itemId);
      toast.success("Item marked as returned");
      loadItems();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update");
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">My Uploaded Items</h1>
          <p className="mt-2 text-muted-foreground">
            Track your lost and found reports
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadItems}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button asChild size="sm">
            <Link href="/upload/lost">Report Lost</Link>
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-16 text-center">
          <Package className="mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="text-xl font-semibold">No items yet</h2>
          <p className="mt-2 text-muted-foreground">
            Report a lost or found item to get started
          </p>
          <div className="mt-6 flex gap-3">
            <Button asChild>
              <Link href="/upload/lost">Report Lost</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/upload/found">Report Found</Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <ItemCard
              key={item.id}
              item={item}
              actions={
                <div className="flex w-full flex-wrap gap-2">
                  <Button asChild variant="outline" size="sm" className="flex-1">
                    <Link href={`/matches/${item.id}`}>View matches</Link>
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleRefreshMatches(item.id)}
                  >
                    Re-scan
                  </Button>
                  {item.status !== "returned" && item.status !== "resolved" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleMarkResolved(item.id)}
                    >
                      Mark returned
                    </Button>
                  )}
                </div>
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
