import { useState } from "react";
import { Link } from "react-router-dom";
import { Phone, Search, Smile, UserCheck, Users } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { useLiveData } from "../hooks/useLiveData";
import { MatchGrupo } from "../types/domain";

export function CalourosPage() {
  const { scenario } = useApp();
  const { live } = useLiveData<{ grupos: MatchGrupo[] }>("/api/calouros");
  const [busca, setBusca] = useState("");

  const grupos = (live?.grupos ?? scenario.matches).filter((g) => g.calouros.length > 0);
  const q = busca.trim().toLowerCase();
  const filtrados = grupos.filter(
    (g) =>
      !q ||
      g.padrinho.nome.toLowerCase().includes(q) ||
      g.calouros.some((c) => c.nome.toLowerCase().includes(q))
  );

  const totalCalouros = grupos.reduce((acc, g) => acc + g.calouros.length, 0);

  return (
    <AppShell title="Calouros">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Calouros</h1>
          <p className="pt-page-subtitle">Distribuição de calouros por padrinho no semestre</p>
        </div>
        <div className="pt-page-actions">
          <div className="pt-input-wrap" style={{ width: 230 }}>
            <span className="pt-input-icon"><Search size={14} /></span>
            <input
              type="text"
              className="pt-input"
              placeholder="Buscar padrinho ou calouro..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
          <ToneBadge tone="brand"><UserCheck size={13} /> {filtrados.length} padrinhos</ToneBadge>
          <ToneBadge tone="neutral"><Users size={13} /> {totalCalouros} calouros</ToneBadge>
        </div>
      </div>

      <div className="pt-stack">
        {filtrados.map((g) => (
          <div key={g.padrinho.id} className="pt-card pt-card-flat">
            <div className="pt-card-header" style={{ background: "var(--pt-bg)" }}>
              <div className="pt-card-header-title">
                <div className="pt-card-header-icon"><UserCheck size={16} /></div>
                <Link to={`/padrinhos/${g.padrinho.id}`} style={{ fontWeight: 700, fontSize: 14.5 }}>
                  {g.padrinho.nome}
                </Link>
                {g.padrinho.turno && (
                  <ToneBadge tone={g.padrinho.turno === "Manhã" ? "amber" : "brand"}>{g.padrinho.turno}</ToneBadge>
                )}
              </div>
              <ToneBadge tone="neutral">{g.calouros.length} calouro(s)</ToneBadge>
            </div>
            <div className="pt-table-wrap">
              <table className="pt-table pt-table-compact">
                <tbody>
                  {g.calouros.map((c) => (
                    <tr key={c.id}>
                      <td style={{ width: "65%", fontWeight: 500 }}>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                          <Smile size={15} color="var(--pt-brand)" /> {c.nome}
                        </span>
                      </td>
                      <td className="pt-mono pt-muted">
                        {c.telefone ? (
                          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                            <Phone size={13} /> {c.telefone}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}

        {filtrados.length === 0 && (
          <div className="pt-card">
            <div className="pt-empty">
              <div className="pt-empty-icon"><Users size={20} /></div>
              <strong>Nenhum match gerado neste cenário ainda</strong>
              <p className="pt-muted" style={{ margin: 0, fontSize: 13 }}>
                No Cenário 1 (Pré-Match), os {scenario.calourosSoltos.length} calouros aguardam a execução do algoritmo na tela Match.
              </p>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
