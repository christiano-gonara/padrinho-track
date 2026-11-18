import { AlertTriangle, CheckCircle2, Clock, Info, XCircle } from "lucide-react";
import { StatusACG } from "../../types/domain";
import "./StatusBadge.css";

export function StatusACGBadge({ status }: { status: StatusACG }) {
  if (status === "apto") {
    return (
      <span className="pt-badge pt-badge-apto">
        <CheckCircle2 size={13} /> Apto
      </span>
    );
  }
  if (status === "alerta") {
    return (
      <span className="pt-badge pt-badge-alerta">
        <AlertTriangle size={13} /> Alerta
      </span>
    );
  }
  if (status === "inapto_amarelo") {
    return (
      <span className="pt-badge pt-badge-inapto">
        <Clock size={13} /> Reprovado
      </span>
    );
  }
  return (
    <span className="pt-badge pt-badge-grave">
      <XCircle size={13} /> Reportado
    </span>
  );
}

export function ToneBadge({
  tone,
  children,
}: {
  tone: "green" | "amber" | "orange" | "red" | "brand" | "neutral";
  children: React.ReactNode;
}) {
  return (
    <span className={`pt-badge pt-badge-${tone}`}>
      {tone === "brand" && <Info size={12} />}
      {children}
    </span>
  );
}
