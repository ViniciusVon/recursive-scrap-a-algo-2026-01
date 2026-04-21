/**
 * Placeholders animados para estados de carregamento.
 *
 * Preferimos skeletons a um texto "Carregando..." porque dão ao usuário
 * uma ideia imediata do layout que vai aparecer — a tela não "pula"
 * quando os dados chegam.
 */

interface SkeletonProps {
  className?: string;
}

/** Bloco genérico com shimmer via Tailwind `animate-pulse`. */
export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded bg-gray-200 ${className}`}
      aria-hidden="true"
    />
  );
}

/** Skeleton tipificado para uma linha de lista (usuário, sessão, etc). */
export function SkeletonRow() {
  return (
    <div className="border border-gray-200 rounded px-4 py-2 space-y-2">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}

/** Vários SkeletonRow com key automática — evita clutter no consumidor. */
export function SkeletonList({ linhas = 3 }: { linhas?: number }) {
  return (
    <ul className="space-y-2">
      {Array.from({ length: linhas }).map((_, i) => (
        <li key={i}>
          <SkeletonRow />
        </li>
      ))}
    </ul>
  );
}
