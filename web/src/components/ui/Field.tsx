"use client";

import type { InputHTMLAttributes } from "react";

interface FieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  id: string;
  label: string;
  error?: string;
  hint?: string;
}

export function Field({
  id,
  label,
  error,
  hint,
  className = "",
  ...rest
}: FieldProps) {
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  // Both ids are announced, so the rule and the failure are read together.
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      {/* A real label, not a placeholder standing in for one: placeholders vanish on
          focus and are invisible to most assistive tech. */}
      <label htmlFor={id} className="text-sm font-medium text-text-2">
        {label}
      </label>
      <input
        {...rest}
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`min-h-11 w-full rounded-xl border bg-surface-2 px-4 text-text outline-none placeholder:text-text-3 ${
          error ? "border-danger" : "border-border"
        } ${className}`}
      />
      {hint ? (
        <p id={hintId} className="text-sm text-text-3">
          {hint}
        </p>
      ) : null}
      {error ? (
        // role="alert" so the failure is announced at the moment it appears.
        <p id={errorId} role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}
