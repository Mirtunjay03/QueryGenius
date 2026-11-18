declare module "lucide-react" {
  import type { ComponentType, SVGProps } from "react";

  export type LucideProps = SVGProps<SVGSVGElement> & {
    size?: string | number;
  };

  export const ArrowUpRight: ComponentType<LucideProps>;
  export const Database: ComponentType<LucideProps>;
  export const ShieldCheck: ComponentType<LucideProps>;
  export const Sparkles: ComponentType<LucideProps>;
}
