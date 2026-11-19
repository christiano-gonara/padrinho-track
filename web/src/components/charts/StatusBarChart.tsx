import "../../styles/components/Charts.css";

interface StatusCounts {
  aptos: number;
  alertas: number;
  reprovados: number;
  reportados: number;
}

export function StatusBarChart({ counts }: { counts: StatusCounts }) {
  const total = counts.aptos + counts.alertas + counts.reprovados + counts.reportados;
  const denom = total || 1;

  const rows = [
    { key: "green", label: "Aptos", value: counts.aptos, color: "var(--pt-green)" },
    { key: "amber", label: "Em alerta", value: counts.alertas, color: "var(--pt-amber)" },
    { key: "orange", label: "Reprovados", value: counts.reprovados, color: "var(--pt-orange)" },
    { key: "red", label: "Reportados", value: counts.reportados, color: "var(--pt-red)" },
  ];

  return (
    <div>
      <div className="pt-stacked-track" role="img" aria-label="Proporção de status ACG em barra">
        {rows.map((r) => {
          const pct = (r.value / denom) * 100;
          if (pct <= 0) return null;
          return (
            <div
              key={r.key}
              className={`pt-stacked-seg is-${r.key}`}
              style={{ width: `${pct}%` }}
              title={`${r.label}: ${r.value} (${Math.round(pct)}%)`}
            />
          );
        })}
      </div>

      <div className="pt-hbar-list">
        {rows.map((r) => {
          const pct = Math.round((r.value / denom) * 100);
          return (
            <div key={r.key} className="pt-hbar-row">
              <span className="pt-hbar-label">
                <span className="pt-hbar-dot" style={{ background: r.color }} />
                {r.label}
              </span>
              <div className="pt-hbar-track">
                <div
                  className="pt-hbar-fill"
                  style={{ width: `${pct}%`, background: r.color }}
                />
              </div>
              <span className="pt-hbar-val">
                {r.value} <span className="pt-muted">({pct}%)</span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
