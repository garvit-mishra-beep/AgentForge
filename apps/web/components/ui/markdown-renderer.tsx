"use client";

import React from "react";

export function MarkdownRenderer({ content }: { content: string }) {
  const lines = content.split("\n");
  const rendered: React.ReactNode[] = [];
  
  let inCodeBlock = false;
  let codeBlockLang = "";
  let codeBlockLines: string[] = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] || "";
    
    // Code block detection
    if (line.trim().startsWith("```")) {
      if (inCodeBlock) {
        inCodeBlock = false;
        rendered.push(
          <pre key={`code-${i}`} className="bg-muted p-4 rounded-lg overflow-x-auto my-4 border border-border text-xs font-mono leading-relaxed text-foreground select-all">
            <code className={codeBlockLang ? `language-${codeBlockLang}` : ""}>
              {codeBlockLines.join("\n")}
            </code>
          </pre>
        );
        codeBlockLines = [];
        codeBlockLang = "";
      } else {
        inCodeBlock = true;
        codeBlockLang = line.trim().slice(3);
      }
      continue;
    }
    
    if (inCodeBlock) {
      codeBlockLines.push(line);
      continue;
    }
    
    // Header level check
    if (line.startsWith("# ")) {
      rendered.push(
        <h1 key={i} className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground mt-8 mb-4 border-b border-border pb-2">
          {parseInline(line.slice(2))}
        </h1>
      );
      continue;
    }
    if (line.startsWith("## ")) {
      rendered.push(
        <h2 key={i} className="text-xl sm:text-2xl font-bold tracking-tight text-foreground mt-6 mb-3 border-b border-border pb-1">
          {parseInline(line.slice(3))}
        </h2>
      );
      continue;
    }
    if (line.startsWith("### ")) {
      rendered.push(
        <h3 key={i} className="text-lg sm:text-xl font-semibold tracking-tight text-foreground mt-5 mb-2">
          {parseInline(line.slice(4))}
        </h3>
      );
      continue;
    }
    if (line.startsWith("#### ")) {
      rendered.push(
        <h4 key={i} className="text-base sm:text-lg font-medium tracking-tight text-foreground mt-4 mb-2">
          {parseInline(line.slice(5))}
        </h4>
      );
      continue;
    }
    
    // Horizontal Rule
    if (line.trim() === "---" || line.trim() === "___" || line.trim() === "***") {
      rendered.push(<hr key={i} className="my-6 border-border" />);
      continue;
    }
    
    // Bullet list checks
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      const listContent = line.trim().slice(2);
      rendered.push(
        <ul key={i} className="list-disc list-inside ml-4 my-1 text-sm text-muted-foreground space-y-1">
          <li>{parseInline(listContent)}</li>
        </ul>
      );
      continue;
    }
    
    // Blockquotes
    if (line.startsWith("> ")) {
      rendered.push(
        <blockquote key={i} className="border-l-4 border-primary pl-4 py-1.5 my-4 italic text-muted-foreground bg-muted/40 rounded-r-md">
          {parseInline(line.slice(2))}
        </blockquote>
      );
      continue;
    }
    
    // Ignore pure empty lines
    if (!line.trim()) {
      continue;
    }
    
    // Standard paragraph fallback
    rendered.push(
      <p key={i} className="text-sm leading-relaxed text-muted-foreground my-3">
        {parseInline(line)}
      </p>
    );
  }
  
  return <div className="space-y-1">{rendered}</div>;
}

// Scans text for bolding, inline code, and dynamic documentation links
function parseInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let currentText = text;
  let keyIdx = 0;
  
  while (currentText) {
    const boldMatch = currentText.match(/\*\*(.*?)\*\*/);
    const codeMatch = currentText.match(/`(.*?)`/);
    const linkMatch = currentText.match(/\[(.*?)\]\((.*?)\)/);
    
    const matches = [
      ...(boldMatch ? [{ type: "bold", index: boldMatch.index!, length: boldMatch[0].length, text: boldMatch[1] }] : []),
      ...(codeMatch ? [{ type: "code", index: codeMatch.index!, length: codeMatch[0].length, text: codeMatch[1] }] : []),
      ...(linkMatch ? [{ type: "link", index: linkMatch.index!, length: linkMatch[0].length, text: linkMatch[1], href: linkMatch[2] }] : [])
    ];
    
    if (matches.length === 0) {
      parts.push(currentText);
      break;
    }
    
    matches.sort((a, b) => a.index - b.index);
    const firstMatch = matches[0]!;
    
    if (firstMatch.index > 0) {
      parts.push(currentText.slice(0, firstMatch.index));
    }
    
    if (firstMatch.type === "bold") {
      parts.push(
        <strong key={keyIdx++} className="font-bold text-foreground">
          {firstMatch.text}
        </strong>
      );
    } else if (firstMatch.type === "code") {
      parts.push(
        <code key={keyIdx++} className="bg-muted px-1.5 py-0.5 rounded font-mono text-[11px] text-foreground border border-border">
          {firstMatch.text}
        </code>
      );
    } else if (firstMatch.type === "link") {
      let href = firstMatch.href || "";
      const isExternal = href.startsWith("http") || href.startsWith("mailto");
      
      // Rewrite dynamic documentation routes
      if (!isExternal && href.endsWith(".md")) {
        href = "/docs/" + href.slice(0, -3);
      }
      
      parts.push(
        <a
          key={keyIdx++}
          href={href}
          target={isExternal ? "_blank" : undefined}
          rel={isExternal ? "noopener noreferrer" : undefined}
          className="text-primary hover:underline font-medium"
        >
          {firstMatch.text}
        </a>
      );
    }
    
    currentText = currentText.slice(firstMatch.index + firstMatch.length);
  }
  
  return parts;
}
