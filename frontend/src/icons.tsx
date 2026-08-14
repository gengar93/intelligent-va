import type { ReactNode } from "react";

function Icon({
  children,
  size = 16,
  strokeWidth = 1.7,
  className,
}: {
  children: ReactNode;
  size?: number;
  strokeWidth?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {children}
    </svg>
  );
}

export function LogoIcon({ size = 18 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={1.8}>
      <path d="M4 7h16M4 12h16M4 17h10" />
    </Icon>
  );
}

export function MenuIcon({ size = 19 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={1.8}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </Icon>
  );
}

export function CloseIcon({ size = 19 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={1.8}>
      <path d="m6 6 12 12M18 6 6 18" />
    </Icon>
  );
}

export function OrdersIcon() {
  return (
    <Icon>
      <path d="M3 6h18M3 6l1.5 12.5A2 2 0 0 0 6.5 20h11a2 2 0 0 0 2-1.5L21 6M9 10v6M15 10v6" />
    </Icon>
  );
}

export function TicketsIcon() {
  return (
    <Icon>
      <path d="M3 9a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2 2 2 0 0 0 0 6 2 2 0 0 1-2 2H5a2 2 0 0 1-2-2 2 2 0 0 0 0-6z" />
      <path d="M13 7v10" />
    </Icon>
  );
}

export function ChatIcon() {
  return (
    <Icon>
      <path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2z" />
      <path d="M12 8v.01M9 12h6" />
    </Icon>
  );
}

export function SunIcon({ size = 17 }: { size?: number }) {
  return (
    <Icon size={size}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </Icon>
  );
}

export function MoonIcon({ size = 17 }: { size?: number }) {
  return (
    <Icon size={size}>
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </Icon>
  );
}

export function ChevronDownIcon({ size = 15 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={1.8}>
      <path d="m6 9 6 6 6-6" />
    </Icon>
  );
}

export function ChevronRightIcon({ size = 16 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={1.9}>
      <path d="m9 6 6 6-6 6" />
    </Icon>
  );
}

export function CheckIcon({ size = 16, strokeWidth = 2.2 }: { size?: number; strokeWidth?: number }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth}>
      <path d="m20 6-11 11-5-5" />
    </Icon>
  );
}

export function SendIcon({ size = 18 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={1.8}>
      <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
    </Icon>
  );
}

export function SparkIcon({ size = 16 }: { size?: number }) {
  return (
    <Icon size={size}>
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
    </Icon>
  );
}

export function ArrowRightIcon({ size = 8 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={3}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </Icon>
  );
}

export function ReceiptIcon({ size = 15 }: { size?: number }) {
  return (
    <Icon size={size}>
      <path d="M6 2h9l3 3v17l-3-2-3 2-3-2-3 2V2z" />
      <path d="M9 7h6M9 11h6M9 15h4" />
    </Icon>
  );
}

export function InvoiceDocIcon({ size = 14, strokeWidth = 1.9 }: { size?: number; strokeWidth?: number }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth}>
      <path d="M6 2h9l3 3v17l-3-2-3 2-3-2-3 2V2z" />
    </Icon>
  );
}

export function TruckIcon({ size = 13 }: { size?: number }) {
  return (
    <Icon size={size}>
      <path d="M3 7h13v10H3zM16 10h3l2 3v4h-5" />
      <circle cx="7" cy="18" r="1.6" />
      <circle cx="18" cy="18" r="1.6" />
    </Icon>
  );
}

export function ClockIcon({ size = 14, strokeWidth = 1.9 }: { size?: number; strokeWidth?: number }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v4l3 2" />
    </Icon>
  );
}

export function CancelIcon({ size = 16, strokeWidth = 1.8 }: { size?: number; strokeWidth?: number }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth}>
      <circle cx="12" cy="12" r="9" />
      <path d="M15 9l-6 6M9 9l6 6" />
    </Icon>
  );
}

export function BotIcon({ size = 18 }: { size?: number }) {
  return (
    <Icon size={size}>
      <rect x="4" y="7" width="16" height="12" rx="3" />
      <path d="M12 7V4M8 13h.01M16 13h.01M9 17h6" />
    </Icon>
  );
}

export function BotSmallIcon({ size = 16 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={1.8}>
      <rect x="4" y="7" width="16" height="12" rx="3" />
      <path d="M12 7V4" />
    </Icon>
  );
}

export function BoxIcon({ size = 17, strokeWidth = 1.5 }: { size?: number; strokeWidth?: number }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth}>
      <path d="M21 8v8a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 16V8a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8z" />
      <path d="M3.3 7 12 12l8.7-5M12 22V12" />
    </Icon>
  );
}

export function DownloadIcon({ size = 15, strokeWidth = 1.8 }: { size?: number; strokeWidth?: number }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth}>
      <path d="M12 3v12m0 0 4.5-4.5M12 15l-4.5-4.5M4 19h16" />
    </Icon>
  );
}

export function PlusIcon({ size = 17, strokeWidth = 1.9 }: { size?: number; strokeWidth?: number }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth}>
      <path d="M12 5v14M5 12h14" />
    </Icon>
  );
}

export function CircleCheckIcon({ size = 24 }: { size?: number }) {
  return (
    <Icon size={size} strokeWidth={1.5}>
      <path d="M9 12l2 2 4-4" />
      <circle cx="12" cy="12" r="9" />
    </Icon>
  );
}
