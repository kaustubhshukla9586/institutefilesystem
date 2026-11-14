import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs) => twMerge(clsx(inputs));

export const LEVEL_LABEL = { public: "Public", faculty: "Faculty", admin: "Admin" };
export const ROLE_LABEL = { student: "Student", faculty: "Faculty", admin: "Admin" };

export function fmtTime(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}
