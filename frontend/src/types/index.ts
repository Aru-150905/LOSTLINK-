export type ItemType = "lost" | "found";

export type ItemStatus =
  | "active"
  | "matched"
  | "claimed"
  | "returned"
  | "resolved";

export type ClaimStatus = "pending" | "approved" | "rejected";

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone?: string;
  is_admin?: boolean;
}

export interface Item {
  id: string;
  user_id: string;
  type: ItemType;
  title: string;
  description?: string;
  location: string;
  item_timestamp: string;
  image_url?: string;
  category?: string;
  contact_phone?: string;
  contact_email?: string;
  status: ItemStatus;
  created_at: string;
  updated_at: string;
}

export interface MatchResult {
  id?: string;
  item_id: string;
  matched_item_id: string;
  confidence_score: number;
  image_score: number;
  text_score: number;
  metadata_score: number;
  status: string;
  matched_item?: Item;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: string;
  read: boolean;
  related_item_id?: string;
  related_match_id?: string;
  created_at: string;
}

export interface Claim {
  id: string;
  item_id: string;
  claimer_id: string;
  message?: string;
  status: ClaimStatus;
  admin_notes?: string;
  created_at: string;
  items?: Item;
  users?: { name: string; email: string };
}

export interface UploadItemResponse {
  item: Item;
  matches: MatchResult[];
}

export interface AdminStats {
  total_items: number;
  lost_items: number;
  found_items: number;
  active_items: number;
  pending_claims: number;
  total_matches: number;
}

export interface ItemFormData {
  title: string;
  description: string;
  location: string;
  item_timestamp: string;
  category: string;
  contact_phone: string;
  contact_email: string;
}
