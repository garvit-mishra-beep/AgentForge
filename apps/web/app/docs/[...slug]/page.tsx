import fs from "fs";
import path from "path";
import { notFound } from "next/navigation";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";

interface PageProps {
  params: Promise<{
    slug: string[];
  }>;
}

export default async function DocPage({ params }: PageProps) {
  const { slug } = await params;

  // Resolve master docs path root
  const docsRoot = path.resolve(process.cwd(), "../../docs");
  const relativePath = slug.join("/");

  // Traversal pattern check
  if (
    relativePath.includes("..") ||
    relativePath.includes("./") ||
    relativePath.includes(".\\") ||
    path.isAbsolute(relativePath)
  ) {
    return notFound();
  }

  // Form target path
  let targetPath = path.resolve(docsRoot, relativePath);

  // Append default markdown extension if none is provided
  if (!path.extname(targetPath)) {
    targetPath += ".md";
  }

  // Prefix check
  if (!targetPath.startsWith(docsRoot)) {
    return notFound();
  }

  // File existence check
  if (!fs.existsSync(targetPath)) {
    return notFound();
  }

  // Resolve symbolic links
  let realPath: string;
  try {
    realPath = fs.realpathSync(targetPath);
  } catch {
    return notFound();
  }

  // Final root boundaries check
  if (!realPath.startsWith(docsRoot)) {
    return notFound();
  }

  // Extension Whitelisting (.md or .mdx only)
  const ext = path.extname(realPath).toLowerCase();
  if (ext !== ".md" && ext !== ".mdx") {
    return notFound();
  }

  // Size limit validation (Max 1 MB)
  const stats = fs.statSync(realPath);
  if (stats.size > 1024 * 1024) {
    return notFound();
  }

  const content = fs.readFileSync(realPath, "utf-8");

  return (
    <div className="prose dark:prose-invert max-w-none">
      <MarkdownRenderer content={content} />
    </div>
  );
}
