"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import Image from "next/image";
import { ImagePlus, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageUploadProps {
  onFileSelect: (file: File | null) => void;
  required?: boolean;
  label?: string;
}

export function ImageUpload({
  onFileSelect,
  required = false,
  label = "Upload image",
}: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const selected = acceptedFiles[0] ?? null;
      setFile(selected);
      onFileSelect(selected);

      if (selected) {
        const url = URL.createObjectURL(selected);
        setPreview(url);
      } else {
        setPreview(null);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".jpeg", ".jpg", ".png", ".webp", ".gif"] },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
  });

  const clearImage = () => {
    setFile(null);
    setPreview(null);
    onFileSelect(null);
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </label>

      {preview ? (
        <div className="relative overflow-hidden rounded-xl border">
          <div className="relative aspect-video w-full">
            <Image
              src={preview}
              alt="Preview"
              fill
              className="object-cover"
              unoptimized
            />
          </div>
          <button
            type="button"
            onClick={clearImage}
            className="absolute right-2 top-2 rounded-full bg-background/80 p-1.5 shadow-sm hover:bg-background"
          >
            <X className="h-4 w-4" />
          </button>
          <p className="px-3 py-2 text-xs text-muted-foreground truncate">
            {file?.name}
          </p>
        </div>
      ) : (
        <div
          {...getRootProps()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 transition-colors",
            isDragActive
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50"
          )}
        >
          <input {...getInputProps()} />
          <ImagePlus className="mb-3 h-10 w-10 text-muted-foreground" />
          <p className="text-sm font-medium">
            {isDragActive ? "Drop the image here" : "Drag & drop an image here"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            or click to browse (max 5MB)
          </p>
        </div>
      )}
    </div>
  );
}
