import { AlertTriangle, Info, Moon, Sun } from "lucide-react";
import { Turno } from "../../types/domain";
import "../../styles/components/Kit.css";

/** Iniciais do nome (primeiro + último) */
export function iniciais(nome: string): string {
  const partes = nome.trim().split(/\s+/);
  const primeira = partes[0]?.[0] ?? "";
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : "";
  return (primeira + ultima).toUpperCase();
}

export function Avatar({
  nome,
  size = 36,
  tone = "brand",
}: {
  nome: string;
  size?: number;
  tone?: "brand" | "neutral" | "white" | "amber" | "red";
}) {
  return (
    <span
      className={`pt-avt pt-avt-${tone}`}
      style={{ width: size, height: size, fontSize: Math.round(size * 0.36) }}
      aria-hidden="true"
    >
      {iniciais(nome)}
    </span>
  );
}

export function TurnoTag({ turno }: { turno: Turno }) {
  if (!turno) return <span className="pt-muted">—</span>;
  return (
    <span className="pt-turno">
      {turno === "Manhã" ? <Sun size={14} color="#b45309" /> : <Moon size={14} color="#4338ca" />}
      {turno}
    </span>
  );
}

/** Quadradinhos de presença: azul = foi */
export function PresencaDots({ feitas, total }: { feitas: number; total: number }) {
  return (
    <span className="pt-dots" aria-label={`${feitas} de ${total} reuniões`}>
      <span className="pt-dots-row">
        {Array.from({ length: total }).map((_, i) => (
          <span key={i} className={i < feitas ? "is-on" : ""} />
        ))}
      </span>
      <span>
        {feitas} de {total}
      </span>
    </span>
  );
}

/** Cartões desenhados: amarelos e vermelhos */
export function CartoesMini({ amarelos, vermelhos }: { amarelos: number; vermelhos: number }) {
  if (!amarelos && !vermelhos) return <span className="pt-muted">Nenhum</span>;
  const partes: string[] = [];
  if (amarelos) partes.push(`${amarelos} amarelo${amarelos > 1 ? "s" : ""}`);
  if (vermelhos) partes.push(`${vermelhos} vermelho${vermelhos > 1 ? "s" : ""}`);
  return (
    <span className="pt-cartoes">
      <span className="pt-cartoes-row" aria-hidden="true">
        {Array.from({ length: amarelos }).map((_, i) => (
          <span key={`a${i}`} className="is-amarelo" />
        ))}
        {Array.from({ length: vermelhos }).map((_, i) => (
          <span key={`v${i}`} className="is-vermelho" />
        ))}
      </span>
      <span>{partes.join(", ")}</span>
    </span>
  );
}

/** Linha de números separados por risquinhos */
export function StatsRow({
  items,
}: {
  items: { valor: string | number; texto: string; cor?: string }[];
}) {
  return (
    <section className="pt-card pt-stats">
      {items.map((it) => (
        <div key={it.texto}>
          <div className="pt-stats-num" style={it.cor ? { color: it.cor } : undefined}>
            {it.valor}
          </div>
          <div className="pt-stats-txt">{it.texto}</div>
        </div>
      ))}
    </section>
  );
}

/** Meia-rosca tipo velocímetro */
export function Gauge({ pct, legenda }: { pct: number; legenda: string }) {
  const total = 258;
  const traco = Math.round((total * Math.max(0, Math.min(100, pct))) / 100);
  return (
    <div className="pt-gauge">
      <svg role="img" aria-label={`${pct}% ${legenda}`} width="240" height="134" viewBox="0 0 200 112">
        <path d="M18 100 A82 82 0 0 1 182 100" fill="none" stroke="#e2e8f0" strokeWidth="18" strokeLinecap="round" />
        <path
          d="M18 100 A82 82 0 0 1 182 100"
          fill="none"
          stroke="#10b981"
          strokeWidth="18"
          strokeLinecap="round"
          strokeDasharray={`${traco} ${total}`}
        />
        <text x="100" y="90" textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fontSize="38" fontWeight="800" fill="#0f172a">
          {pct}%
        </text>
      </svg>
      <div className="pt-gauge-label">{legenda}</div>
    </div>
  );
}

/** Barra dividida: foi / justificou / faltou */
export function PresencaBar({ foi, justificou, faltou }: { foi: number; justificou: number; faltou: number }) {
  return (
    <div
      className="pt-pbar"
      role="img"
      aria-label={`${foi} foram, ${justificou} justificaram, ${faltou} faltaram`}
    >
      {foi > 0 && <span style={{ flex: foi, background: "#1d4ed8" }} />}
      {justificou > 0 && <span style={{ flex: justificou, background: "#93c5fd" }} />}
      {faltou > 0 && <span style={{ flex: faltou, background: "#f59e0b" }} />}
    </div>
  );
}

export function PresencaLegenda() {
  return (
    <div className="pt-legend">
      <span><i style={{ background: "#1d4ed8" }} />Foi</span>
      <span><i style={{ background: "#93c5fd" }} />Justificou</span>
      <span><i style={{ background: "#f59e0b" }} />Faltou</span>
    </div>
  );
}

export function Aviso({ tipo = "info", children }: { tipo?: "info" | "warn" | "bad"; children: React.ReactNode }) {
  return (
    <div className={`pt-aviso pt-aviso-${tipo}`}>
      {tipo === "info" ? <Info size={20} /> : <AlertTriangle size={20} />}
      <div>{children}</div>
    </div>
  );
}
