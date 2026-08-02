import type { ReactNode, SVGProps } from "react";

export type IconName =
  | "activity"
  | "analytics"
  | "arrow-right"
  | "bell"
  | "building"
  | "check"
  | "chevron-down"
  | "close"
  | "command"
  | "decision"
  | "external"
  | "home"
  | "layers"
  | "logout"
  | "menu"
  | "plus"
  | "search"
  | "shield"
  | "spark"
  | "users"
  | "warning";

type IconProps = SVGProps<SVGSVGElement> & {
  name: IconName;
  size?: number;
};

const paths: Record<IconName, ReactNode> = {
  activity: <path d="M4 12h3l2-6 4 12 2-6h5" />,
  analytics: <><path d="M4 19V9" /><path d="M10 19V5" /><path d="M16 19v-7" /><path d="M22 19H2" /></>,
  "arrow-right": <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" /><path d="M10 21h4" /></>,
  building: <><path d="M3 21h18" /><path d="M6 21V4h9v17" /><path d="M15 9h3v12" /><path d="M9 8h3" /><path d="M9 12h3" /><path d="M9 16h3" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  "chevron-down": <path d="m6 9 6 6 6-6" />,
  close: <><path d="m6 6 12 12" /><path d="m18 6-12 12" /></>,
  command: <><path d="M9 6V5a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v14a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3Z" /></>,
  decision: <><path d="M5 4h14v16H5z" /><path d="M8 8h8" /><path d="M8 12h5" /><path d="m14 16 1.5 1.5L19 14" /></>,
  external: <><path d="M14 5h5v5" /><path d="m10 14 9-9" /><path d="M19 13v6H5V5h6" /></>,
  home: <><path d="m3 11 9-8 9 8" /><path d="M5 10v10h14V10" /><path d="M9 20v-6h6v6" /></>,
  layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 12 9 5 9-5" /><path d="m3 16 9 5 9-5" /></>,
  logout: <><path d="M10 5H5v14h5" /><path d="M14 8l4 4-4 4" /><path d="M18 12H9" /></>,
  menu: <><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" /></>,
  plus: <><path d="M12 5v14" /><path d="M5 12h14" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  shield: <><path d="M12 3 5 6v5c0 4.5 2.7 8 7 10 4.3-2 7-5.5 7-10V6l-7-3Z" /><path d="m9 12 2 2 4-4" /></>,
  spark: <><path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3Z" /><path d="m18.5 14 .8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2Z" /></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></>,
  warning: <><path d="M12 3 2.5 20h19L12 3Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></>,
};

export function Icon({ name, size = 20, ...props }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      {...props}
    >
      {paths[name]}
    </svg>
  );
}
