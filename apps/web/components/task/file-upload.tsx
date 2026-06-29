"use client";

import { useState, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { uploadFile, uploadZip, deleteProjectFile, getFileDownloadUrl } from "@/lib/api";
import type { ProjectFile } from "@/lib/types";
import {
  Upload, FileText, FolderOpen, Loader2, Download, Trash2, Archive,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  projectId: string;
  files: ProjectFile[];
  onFilesChange: () => void;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function FileUpload({ projectId, files, onFilesChange }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const zipInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadProgress(`Uploading ${file.name}...`);
    try {
      await uploadFile(projectId, file);
      onFilesChange();
    } catch (err) {
      setUploadProgress(err instanceof Error ? err.message : "Upload failed");
      setTimeout(() => setUploadProgress(null), 3000);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, [projectId, onFilesChange]);

  const handleZipSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadProgress(`Extracting ${file.name}...`);
    try {
      const result = await uploadZip(projectId, file);
      setUploadProgress(`${result.files_extracted} files extracted`);
      setTimeout(() => setUploadProgress(null), 2000);
      onFilesChange();
    } catch (err) {
      setUploadProgress(err instanceof Error ? err.message : "Extraction failed");
      setTimeout(() => setUploadProgress(null), 3000);
    } finally {
      setUploading(false);
      if (zipInputRef.current) zipInputRef.current.value = "";
    }
  }, [projectId, onFilesChange]);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(`Uploading ${file.name}...`);
    try {
      if (file.name.endsWith(".zip") || file.name.endsWith(".tar.gz")) {
        const result = await uploadZip(projectId, file);
        setUploadProgress(`${result.files_extracted} files extracted`);
      } else {
        await uploadFile(projectId, file);
        setUploadProgress("Upload complete");
      }
      setTimeout(() => setUploadProgress(null), 2000);
      onFilesChange();
    } catch (err) {
      setUploadProgress(err instanceof Error ? err.message : "Upload failed");
      setTimeout(() => setUploadProgress(null), 3000);
    } finally {
      setUploading(false);
    }
  }, [projectId, onFilesChange]);

  const handleDelete = useCallback(async (fileId: string) => {
    try {
      await deleteProjectFile(projectId, fileId);
      onFilesChange();
    } catch (err) {
      console.error("Delete failed", err);
    }
  }, [projectId, onFilesChange]);

  return (
    <div className="space-y-4">
      {/* Upload area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "rounded-xl border-2 border-dashed p-8 text-center transition-all cursor-pointer",
          dragOver
            ? "border-primary bg-primary-muted"
            : "border-border hover:border-border-hover bg-surface/30",
        )}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
        />
        <input
          ref={zipInputRef}
          type="file"
          accept=".zip,.tar.gz,.tgz"
          className="hidden"
          onChange={handleZipSelect}
        />

        {uploading ? (
          <div className="space-y-2">
            <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">{uploadProgress}</p>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
            <p className="text-sm font-medium">Drop files here or click to upload</p>
            <p className="text-xs text-muted-foreground">
              Supports individual files or ZIP archives. Max 100MB.
            </p>
            <div className="flex items-center justify-center gap-2 mt-3">
              <Button size="sm" variant="secondary" type="button" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>
                <FileText className="h-3.5 w-3.5" />
                Select File
              </Button>
              <Button size="sm" variant="secondary" type="button" onClick={(e) => { e.stopPropagation(); zipInputRef.current?.click(); }}>
                <Archive className="h-3.5 w-3.5" />
                Upload ZIP
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* File list */}
      {files.length === 0 && !uploading ? (
        <div className="text-center py-8 text-sm text-muted-foreground">
          No files uploaded yet. Upload source code, documentation, or any project assets.
        </div>
      ) : (
        <div className="space-y-1">
          {files.map((file, i) => (
            <motion.div
              key={file.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: i * 0.03 }}
              className="flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5 hover:border-border-hover transition-all group"
            >
              {file.is_directory ? (
                <FolderOpen className="h-4 w-4 text-muted-foreground shrink-0" />
              ) : (
                <FileText className="h-4 w-4 text-primary shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{file.filename}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] font-mono text-muted-foreground">
                    {formatFileSize(file.size_bytes)}
                  </span>
                  <Badge variant="secondary" className="text-[9px] px-1 py-0">
                    {file.mime_type.split("/").pop()}
                  </Badge>
                  {file.file_hash && (
                    <span className="text-[9px] font-mono text-muted-foreground/50">
                      {file.file_hash.slice(0, 8)}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  type="button"
                  onClick={() => window.open(getFileDownloadUrl(projectId, file.id), "_blank")}
                  className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-surface transition-colors cursor-pointer"
                >
                  <Download className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(file.id)}
                  className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-colors cursor-pointer"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
