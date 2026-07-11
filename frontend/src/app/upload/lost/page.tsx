import { ItemUploadForm } from "@/components/items/item-upload-form";

export default function UploadLostPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Report a Lost Item</h1>
        <p className="mt-2 text-muted-foreground">
          Describe what you lost and optionally upload a photo. Our AI will search
          against all found items for possible matches.
        </p>
      </div>
      <ItemUploadForm type="lost" />
    </div>
  );
}
