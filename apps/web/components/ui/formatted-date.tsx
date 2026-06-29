"use client";

import { useState, useEffect } from "react";

interface FormattedDateProps {
  date: string | Date | number;
  showTime?: boolean;
  type?: "time" | "date" | "datetime";
  options?: Intl.DateTimeFormatOptions;
  className?: string;
}

export function FormattedDate({ date, showTime = false, type, options, className }: FormattedDateProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    // Return skeleton placeholder during server rendering/hydration
    return <span className="inline-block w-16 h-3.5 bg-muted/30 animate-pulse rounded" />;
  }

  let formatted = "";
  let isValid = true;

  try {
    const d = new Date(date);
    if (isNaN(d.getTime())) {
      isValid = false;
    } else {
      if (type === "time") {
        formatted = d.toLocaleTimeString([], options || { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      } else if (type === "date") {
        formatted = d.toLocaleDateString([], options);
      } else {
        formatted = (showTime || type === "datetime")
          ? d.toLocaleString([], options)
          : d.toLocaleDateString([], options);
      }
    }
  } catch {
    isValid = false;
  }

  if (!isValid) {
    return <span className={className}>Invalid Date</span>;
  }

  return <span className={className}>{formatted}</span>;
}
