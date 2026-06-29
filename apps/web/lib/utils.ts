import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function to Tailwind classes
 * @param inputs - Classes to merge
 * @returns Merged className string
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a date to a relative time string (e.g., "2 minutes ago")
 * @param date - Date to format
 * @returns Relative time string
 */
export function formatRelativeDate(date: Date | string): string {
  const d = new Date(date);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000);

  if (diffInSeconds < 5) return "just now";
  if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
  if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;
  }
  if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours !== 1 ? "s" : ""} ago`;
  }
  if (diffInSeconds < 2592000) { // 30 days
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} day${days !== 1 ? "s" : ""} ago`;
  }
  if (diffInSeconds < 31536000) { // 365 days
    const months = Math.floor(diffInSeconds / 2592000);
    return `${months} month${months !== 1 ? "s" : ""} ago`;
  }
  const years = Math.floor(diffInSeconds / 31536000);
  return `${years} year${years !== 1 ? "s" : ""} ago`;
}

/**
 * Format a timestamp as HH:MM:SS
 * @param date - Date to format
 * @returns Formatted time string
 */
export function formatTime(date: Date | string): string {
  const d = new Date(date);
  return d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

/**
 * Deep clone an object
 * @param obj - Object to clone
 * @returns Deep copy of the object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj)) as T;
}

/**
 * Debounce a function
 * @param fn - Function to debounce
 * @param delay - Delay in milliseconds
 * @returns Debounced function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number
): ((this: ThisParameterType<T>, ...args: Parameters<T>) => void) {
  let timeoutId: ReturnType<typeof setTimeout>;
  return function (this: ThisParameterType<T>, ...args: Parameters<T>) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * Check if an object is empty
 * @param obj - Object to check
 * @returns True if object is empty
 */
export function isEmptyObject(obj: object): boolean {
  return Object.keys(obj).length === 0;
}

/**
 * Group an array by a key
 * @param array - Array to group
 * @param key - Key to group by
 * @returns Grouped object
 */
export function groupBy<T, K extends keyof T>(
  array: T[],
  key: K
): Record<string, T[]> {
  return array.reduce((result, item) => {
    const groupName = String(item[key]);
    if (!result[groupName]) {
      result[groupName] = [];
    }
    result[groupName].push(item);
    return result;
  }, {} as Record<string, T[]>);
}

/**
 * Extract unique values from an array based on a key
 * @param array - Array to process
 * @param key - Key to check for uniqueness
 * @returns Array with unique items
 */
export function uniqBy<T, K extends keyof T>(
  array: T[],
  key: K
): T[] {
  const seen = new Set();
  return array.filter((item) => {
    const k = item[key];
    if (typeof k === "string" || typeof k === "number") {
      if (!(seen as Set<string | number>).has(k)) {
        (seen as Set<string | number>).add(k);
        return true;
      }
      return false;
    }
    return false;
  });
}
