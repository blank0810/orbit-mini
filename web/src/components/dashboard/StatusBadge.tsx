import type { SubscriberStatus } from "@/lib/types";

// Every status carries an icon AND a word. Colour alone never conveys the meaning,
// which WCAG 1.4.1 requires and which also survives a greyscale demo video.
const STATUS: Record<
  SubscriberStatus,
  { label: string; tone: string; icon: "check" | "clock" | "alert" | "cross" }
> = {
  active: { label: "Active", tone: "text-accent border-accent/40", icon: "check" },
  incomplete: { label: "Incomplete", tone: "text-text-3 border-border", icon: "clock" },
  past_due: { label: "Past due", tone: "text-warn border-warn/40", icon: "alert" },
  canceled: { label: "Canceled", tone: "text-danger border-danger/40", icon: "cross" },
};

export function StatusBadge({ status }: { status: SubscriberStatus }) {
  const { label, tone, icon } = STATUS[status];
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border bg-surface-2 px-3 py-1.5 text-sm font-semibold ${tone}`}
    >
      <Icon name={icon} />
      {label}
    </span>
  );
}

function Icon({ name }: { name: "check" | "clock" | "alert" | "cross" }) {
  const common = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" className="size-4 shrink-0">
      {name === "check" && <path d="M3 8.5 6.2 11.7 13 5" {...common} />}
      {name === "clock" && (
        <>
          <circle cx="8" cy="8" r="6" {...common} />
          <path d="M8 4.5V8l2.5 1.5" {...common} />
        </>
      )}
      {name === "alert" && (
        <>
          <path d="M8 2 15 14H1L8 2Z" {...common} />
          <path d="M8 6.5v3M8 12h.01" {...common} />
        </>
      )}
      {name === "cross" && <path d="M4 4l8 8M12 4l-8 8" {...common} />}
    </svg>
  );
}
