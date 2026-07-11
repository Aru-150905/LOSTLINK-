import { ItemUploadForm } from "@/components/items/item-upload-form";

export default function UploadFoundPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Report a Found Item</h1>
        <p className="mt-2 text-muted-foreground">
          Upload a clear photo of the item you found. A photo is required so our
          AI can match it against lost item reports.
        </p>
      </div>
      <ItemUploadForm type="found" />
    </div>
  );
}
