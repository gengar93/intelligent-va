import { useState } from "react";

import { BoxIcon } from "../icons";

export function StatusPill({ tone, label }: { tone: "ok" | "info" | "warn" | "stop"; label: string }) {
  return (
    <span className={`pill ${tone}`}>
      <span className="dot" aria-hidden="true" />
      {label}
    </span>
  );
}

/**
 * Product thumbnail: renders the item's image when available, otherwise a
 * neutral box glyph placeholder (also used when the image fails to load).
 */
export function ProductThumb({
  imageUrl,
  alt,
  size = 17,
}: {
  imageUrl: string | null;
  alt: string;
  size?: number;
}) {
  const [failed, setFailed] = useState(false);
  if (!imageUrl || failed) {
    return <BoxIcon size={size} />;
  }
  return (
    <img
      src={imageUrl}
      alt={alt}
      width={size + 9}
      height={size + 9}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
