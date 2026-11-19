import { formatarDataBr } from "../../data/scenarios";
import { Reuniao } from "../../types/domain";
import "../../styles/components/Charts.css";

export function AttendanceBarChart({ reunioes }: { reunioes: Reuniao[] }) {
  const ordered = [...reunioes].sort((a, b) => a.data.localeCompare(b.data));
  const maxVal = Math.max(
    1,
    ...ordered.flatMap((r) => [r.presentes, r.justificadas, r.ausentes])
  );

  if (ordered.length === 0) {
    return (
      <div className="pt-empty" style={{ padding: "28px 16px" }}>
        <p style={{ margin: 0, fontSize: 13 }}>Nenhuma reunião registrada ainda neste cenário.</p>
      </div>
    );
  }

  return (
    <div className="pt-vchart-wrap">
      <div className="pt-vchart-legend">
        <span className="pt-vchart-legend-item">
          <span className="pt-hbar-dot" style={{ background: "var(--pt-brand)" }} />
          Presentes
        </span>
        <span className="pt-vchart-legend-item">
          <span className="pt-hbar-dot" style={{ background: "var(--pt-amber)" }} />
          Justificadas
        </span>
        <span className="pt-vchart-legend-item">
          <span className="pt-hbar-dot" style={{ background: "var(--pt-red)" }} />
          Ausentes
        </span>
      </div>

      <div className="pt-vchart-grid" role="img" aria-label="Presenças, justificativas e ausências por reunião">
        {ordered.map((r) => {
          const hPres = Math.max(6, Math.round((r.presentes / maxVal) * 114));
          const hJust = Math.max(r.justificadas > 0 ? 12 : 4, Math.round((r.justificadas / maxVal) * 114));
          const hAus = Math.max(r.ausentes > 0 ? 12 : 4, Math.round((r.ausentes / maxVal) * 114));
          return (
            <div key={r.id} className="pt-vchart-group">
              <div className="pt-vchart-bars">
                <div
                  className="pt-vchart-col is-present"
                  style={{ height: `${hPres}px` }}
                  title={`Presentes: ${r.presentes}`}
                >
                  <span className="pt-vchart-col-val">{r.presentes}</span>
                </div>
                <div
                  className="pt-vchart-col is-just"
                  style={{ height: `${hJust}px` }}
                  title={`Justificadas: ${r.justificadas}`}
                >
                  {r.justificadas > 0 && <span className="pt-vchart-col-val">{r.justificadas}</span>}
                </div>
                <div
                  className="pt-vchart-col is-absent"
                  style={{ height: `${hAus}px` }}
                  title={`Ausentes: ${r.ausentes}`}
                >
                  {r.ausentes > 0 && <span className="pt-vchart-col-val">{r.ausentes}</span>}
                </div>
              </div>
              <div className="pt-vchart-label">{formatarDataBr(r.data)}</div>
              <div className="pt-vchart-sub" title={r.tema}>
                {r.tema}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
