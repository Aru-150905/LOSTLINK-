"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { toast } from "sonner";
import {
  CheckCircle,
  LayoutDashboard,
  Package,
  Users,
  XCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getAdminStats, getPendingClaims, reviewClaim } from "@/lib/api";
import type { AdminStats, Claim } from "@/types";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsData, claimsData] = await Promise.all([
        getAdminStats(),
        getPendingClaims(),
      ]);
      setStats(statsData);
      setClaims(claimsData);
    } catch {
      toast.error("Admin access required");
      router.push("/auth");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleReview = async (claimId: string, action: "approved" | "rejected") => {
    try {
      await reviewClaim(claimId, action);
      toast.success(`Claim ${action}`);
      loadData();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Review failed");
    }
  };

  const statCards = stats
    ? [
        { label: "Total Items", value: stats.total_items, icon: Package },
        { label: "Lost Items", value: stats.lost_items, icon: Package },
        { label: "Found Items", value: stats.found_items, icon: Package },
        { label: "Pending Claims", value: stats.pending_claims, icon: Users },
      ]
    : [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <LayoutDashboard className="h-6 w-6" />
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        </div>
        <p className="mt-2 text-muted-foreground">
          Monitor platform activity and review claim requests
        </p>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {statCards.map(({ label, value, icon: Icon }) => (
              <Card key={label}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">{label}</CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{value}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Pending Claims</CardTitle>
              <CardDescription>
                Review and approve or reject item claim requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              {claims.length === 0 ? (
                <p className="py-8 text-center text-muted-foreground">
                  No pending claims
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item</TableHead>
                      <TableHead>Claimer</TableHead>
                      <TableHead>Message</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {claims.map((claim) => (
                      <TableRow key={claim.id}>
                        <TableCell className="font-medium">
                          {claim.items?.title ?? claim.item_id}
                          <Badge variant="outline" className="ml-2">
                            {claim.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {claim.users?.name ?? "Unknown"}
                          <br />
                          <span className="text-xs text-muted-foreground">
                            {claim.users?.email}
                          </span>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {claim.message || "—"}
                        </TableCell>
                        <TableCell>
                          {format(new Date(claim.created_at), "PP")}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="default"
                              onClick={() => handleReview(claim.id, "approved")}
                            >
                              <CheckCircle className="mr-1 h-4 w-4" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleReview(claim.id, "rejected")}
                            >
                              <XCircle className="mr-1 h-4 w-4" />
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
