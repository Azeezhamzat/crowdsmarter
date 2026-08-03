type LogoTileVariant = "primary" | "inverse";

const TILE_PALETTE: Record<LogoTileVariant, { background: string; foreground: string }> = {
  primary: { background: "#0F2F35", foreground: "#DBF0E8" },
  inverse: { background: "#DBF0E8", foreground: "#0F2F35" },
};

export function LogoMark({
  size = 34,
  variant = "primary",
  className,
}: {
  size?: number;
  variant?: LogoTileVariant;
  className?: string;
}) {
  const { background, foreground } = TILE_PALETTE[variant];
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      role="img"
      aria-hidden="true"
      className={className}
    >
      <rect width="100" height="100" rx="29" fill={background} />
      <text
        x="50"
        y="54"
        textAnchor="middle"
        dominantBaseline="middle"
        fontFamily="Inter, 'Segoe UI', Arial, sans-serif"
        fontWeight="700"
        fontSize="44"
        letterSpacing="-2"
        fill={foreground}
      >
        CS
      </text>
    </svg>
  );
}
