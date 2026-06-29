import React from "react";

export function parseMarkdown(md: string): React.ReactNode {
  const lines = md.split("\n");
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeLines: string[] = [];
  let codeLang = "";
  let listItems: string[] = [];

  const flushList = (key: number) => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${key}`} className="list-disc pl-6 space-y-1.5 my-3 text-sm text-muted-foreground">
          {listItems.map((item, idx) => (
            <li key={idx}>{parseInline(item)}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  const parseInline = (text: string): React.ReactNode[] => {
    const tokens: React.ReactNode[] = [];
    let currentText = text;
    let index = 0;

    while (currentText.length > 0) {
      const boldMatch = currentText.match(/\*\*(.*?)\*\*/);
      const codeMatch = currentText.match(/`(.*?)`/);

      const boldIndex = boldMatch?.index ?? Infinity;
      const codeIndex = codeMatch?.index ?? Infinity;

      if (boldIndex === Infinity && codeIndex === Infinity) {
        tokens.push(<span key={index++}>{currentText}</span>);
        break;
      }

      if (boldIndex < codeIndex && boldMatch) {
        if (boldIndex > 0) {
          tokens.push(<span key={index++}>{currentText.slice(0, boldIndex)}</span>);
        }
        tokens.push(<strong key={index++} className="font-semibold text-foreground">{boldMatch[1]}</strong>);
        currentText = currentText.slice(boldIndex + boldMatch[0].length);
      } else if (codeMatch) {
        if (codeIndex > 0) {
          tokens.push(<span key={index++}>{currentText.slice(0, codeIndex)}</span>);
        }
        tokens.push(<code key={index++} className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs text-primary">{codeMatch[1]}</code>);
        currentText = currentText.slice(codeIndex + codeMatch[0].length);
      }
    }
    return tokens;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]!;

    if (line.startsWith("```")) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${i}`} className="p-4 rounded-lg bg-card font-mono text-xs overflow-x-auto border border-border my-4 text-foreground">
            <code className={`language-${codeLang}`}>{codeLines.join("\n")}</code>
          </pre>
        );
        codeLines = [];
        inCodeBlock = false;
      } else {
        codeLang = line.slice(3).trim();
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    if (line.startsWith("- ") || line.startsWith("* ")) {
      listItems.push(line.slice(2));
      continue;
    } else {
      flushList(i);
    }

    if (line.startsWith("# ")) {
      elements.push(<h1 key={i} className="text-3xl font-extrabold tracking-tight mt-6 mb-4 text-foreground border-b border-border pb-2">{parseInline(line.slice(2))}</h1>);
    } else if (line.startsWith("## ")) {
      elements.push(<h2 key={i} className="text-xl font-bold tracking-tight mt-6 mb-3 text-foreground border-b border-border pb-1.5">{parseInline(line.slice(3))}</h2>);
    } else if (line.startsWith("### ")) {
      elements.push(<h3 key={i} className="text-lg font-semibold mt-5 mb-2 text-foreground">{parseInline(line.slice(4))}</h3>);
    } else if (line.trim() === "") {
      continue;
    } else {
      elements.push(<p key={i} className="text-sm text-muted-foreground leading-relaxed my-3">{parseInline(line)}</p>);
    }
  }

  flushList(lines.length);
  return <div className="space-y-2">{elements}</div>;
}
