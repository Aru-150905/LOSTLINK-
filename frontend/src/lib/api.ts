import { createClient } from "@/lib/supabase/client";
import type {
  AdminStats,
  Claim,
  Item,
  MatchResult,
  Notification,
  UploadItemResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getAuthToken(): Promise<string | null> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      error.detail || error.message || "Request failed",
      response.status
    );
  }

  return response.json();
}

export async function uploadItem(
  formData: FormData
): Promise<UploadItemResponse> {
  const token = await getAuthToken();
  const response = await fetch(`${API_BASE}/upload-item`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(error.detail || "Upload failed", response.status);
  }

  return response.json();
}

export async function getMyItems(): Promise<Item[]> {
  const data = await apiFetch<{ items: Item[] }>("/my-items");
  return data.items;
}

// Read-only: fetch already-computed matches (used when opening the results page).
export async function getStoredMatches(itemId: string): Promise<MatchResult[]> {
  const data = await apiFetch<{ matches: MatchResult[] }>(
    `/matches/${itemId}`
  );
  return data.matches;
}

// Re-runs the matching search and persists results (used by the "Re-scan" button).
export async function searchMatches(itemId: string): Promise<MatchResult[]> {
  const data = await apiFetch<{ matches: MatchResult[] }>("/search-matches", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: itemId }),
  });
  return data.matches;
}

export async function claimItem(
  itemId: string,
  message?: string
): Promise<Claim> {
  return apiFetch<Claim>("/claim-item", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: itemId, message }),
  });
}

export async function markResolved(itemId: string): Promise<Item> {
  const data = await apiFetch<{ item: Item }>("/mark-resolved", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: itemId }),
  });
  return data.item;
}

export async function getNotifications(): Promise<{
  notifications: Notification[];
  unread_count: number;
}> {
  return apiFetch("/notifications");
}

export async function markNotificationRead(
  notificationId: string
): Promise<void> {
  await apiFetch(`/notifications/${notificationId}/read`, { method: "POST" });
}

export async function getAdminStats(): Promise<AdminStats> {
  return apiFetch("/admin/stats");
}

export async function getPendingClaims(): Promise<Claim[]> {
  const data = await apiFetch<{ claims: Claim[] }>("/admin/claims");
  return data.claims;
}

export async function reviewClaim(
  claimId: string,
  action: "approved" | "rejected",
  adminNotes?: string
): Promise<Claim> {
  return apiFetch<Claim>("/admin/claims/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      claim_id: claimId,
      action,
      admin_notes: adminNotes,
    }),
  });
}

export { ApiError };
