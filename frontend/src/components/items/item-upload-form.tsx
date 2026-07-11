"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ImageUpload } from "@/components/items/image-upload";
import { LoadingOverlay } from "@/components/items/loading-overlay";
import { uploadItem } from "@/lib/api";
import type { ItemType } from "@/types";

const categories = [
  "Electronics",
  "Clothing",
  "Accessories",
  "Documents",
  "Keys",
  "Bags",
  "Sports",
  "Other",
];

interface ItemUploadFormProps {
  type: ItemType;
}

export function ItemUploadForm({ type }: ItemUploadFormProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [form, setForm] = useState({
    title: "",
    description: "",
    location: "",
    timestamp: "",
    category: "",
    contact_phone: "",
    contact_email: "",
  });

  const isFound = type === "found";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isFound && !imageFile) {
      toast.error("Image is required for found items");
      return;
    }

    if (!form.title || !form.location || !form.timestamp) {
      toast.error("Please fill in all required fields");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("type", type);
      formData.append("title", form.title);
      formData.append("description", form.description);
      formData.append("location", form.location);
      formData.append("timestamp", new Date(form.timestamp).toISOString());
      if (form.category) formData.append("category", form.category);
      if (form.contact_phone) formData.append("contact_phone", form.contact_phone);
      if (form.contact_email) formData.append("contact_email", form.contact_email);
      if (imageFile) formData.append("image", imageFile);

      const result = await uploadItem(formData);
      toast.success(
        result.matches.length > 0
          ? `Found ${result.matches.length} possible matches!`
          : "Item uploaded successfully"
      );
      router.push(`/matches/${result.item.id}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {loading && <LoadingOverlay />}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Item title *</Label>
              <Input
                id="title"
                placeholder="e.g. Black iPhone 15"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Detailed description — color, brand, distinguishing marks..."
                rows={4}
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select
                value={form.category}
                onValueChange={(value) =>
                  setForm({ ...form, category: value ?? "" })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-4">
            <ImageUpload
              onFileSelect={setImageFile}
              required={isFound}
              label={isFound ? "Item photo (required)" : "Item photo (optional)"}
            />

            <div className="space-y-2">
              <Label htmlFor="location">
                Location {isFound ? "found" : "last seen"} *
              </Label>
              <Input
                id="location"
                placeholder="e.g. Main Auditorium, Block B"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="timestamp">
                Date & time {isFound ? "found" : "lost"} *
              </Label>
              <Input
                id="timestamp"
                type="datetime-local"
                value={form.timestamp}
                onChange={(e) =>
                  setForm({ ...form, timestamp: e.target.value })
                }
                required
              />
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-muted/30 p-4">
          <h3 className="mb-4 font-medium">Contact details</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+91 98765 43210"
                value={form.contact_phone}
                onChange={(e) =>
                  setForm({ ...form, contact_phone: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@college.edu"
                value={form.contact_email}
                onChange={(e) =>
                  setForm({ ...form, contact_email: e.target.value })
                }
              />
            </div>
          </div>
        </div>

        <Button type="submit" size="lg" className="w-full sm:w-auto" disabled={loading}>
          Submit & find matches
        </Button>
      </form>
    </>
  );
}
