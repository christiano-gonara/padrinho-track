import { StatusACG } from "../../types/domain";
import "../../styles/components/StatusBadge.css";

/** Nomes simples de cada situação, usados em todas as telas */
export const STATUS_LABEL: Record<StatusACG, string> = {
  apto: "Apto",
  alerta: "Atenção",
  inapto_amarelo: "Sem ACG",
  inapto_vermelho: "Com o professor",
};

const STATUS_CLASS: Record<StatusACG, string> = {
  apto: "pt-badge-apto",
  alerta: "pt-badge-alerta",
  inapto_amarelo: "pt-badge-inapto",
  inapto_vermelho: "pt-badge-grave",
};

export function StatusACGBadge({ status }: { status: StatusACG }) {
  return <span className={`pt-badge pt-badge-dot ${STATUS_CLASS[status]}`}>{STATUS_LABEL[status]}</span>;
}

export function ToneBadge({
  tone,
  children,
}: {
  tone: "green" | "amber" | "orange" | "red" | "brand" | "neutral";
  children: React.ReactNode;
}) {
  return <span className={`pt-badge pt-badge-${tone}`}>{children}</span>;
}
