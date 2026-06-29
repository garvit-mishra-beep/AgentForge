import fs from "fs";
import path from "path";
import { notFound } from "next/navigation";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";

export default function DocsPage() {
  // Resolve docs absolute path root
  const docsRoot = path.resolve(process.cwd(), "../../docs");
  const targetPath = path.resolve(docsRoot, "DOCUMENTATION_INDEX.md");

  // Traversal & existence guards
  if (!targetPath.startsWith(docsRoot) || !fs.existsSync(targetPath)) {
    return notFound();
  }

  const content = fs.readFileSync(targetPath, "utf-8");

  return (
    <div className="prose dark:prose-invert max-w-none">
      <MarkdownRenderer content={content} />
    </div>
  );
}
