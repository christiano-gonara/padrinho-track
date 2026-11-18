import { Link } from "react-router-dom";
import { CheckCircle2, Link2, Printer, RefreshCw, Sparkles, Users } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { abreviarNome } from "../data/scenarios";
import { useLiveData } from "../hooks/useLiveData";
import { apiFetch } from "../services/api";
import { MatchGrupo } from "../types/domain";

interface LiveMatchResp {
  dados: MatchGrupo[];
  total_matches: number;
  total_calouros: number;
  total_padrinhos: number;
}

export function MatchPage() {
  const { mode, scenario, runMatchDemo, notify } = useApp();
  const { live, reload: loadLive } = useLiveData<LiveMatchResp>("/api/match");

  const grupos = (live ? live.dados : scenario.matches).filter((g) => g.calouros.length > 0);
  const totalPadrinhos = live ? live.total_padrinhos : scenario.padrinhos.length;
  const totalCalouros = live ? live.total_calouros : scenario.calourosSoltos.length;
  const totalMatches = live ? live.total_matches : grupos.reduce((acc, g) => acc + g.calouros.length, 0);

  async function handleRunMatch() {
    if (mode === "live") {
      try {
        const res = await apiFetch<{ total: number }>("/api/match/rodar", { method: "POST" });
        notify(`${res.total} matches gerados.`, "success");
        loadLive();
      } catch (err) {
        notify(err instanceof Error ? err.message : "Erro ao rodar match.", "error");
      }
    } else {
      runMatchDemo();
    }
  }

  return (
    <AppShell title="Match">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Match Padrinho-Calouro</h1>
          <p className="pt-page-subtitle">Distribuição automática por turno, gênero e perfil</p>
        </div>
        <div className="pt-page-actions">
          <ToneBadge tone="brand"><Users size={13} /> {totalPadrinhos} padrinhos</ToneBadge>
          <ToneBadge tone="neutral">{totalCalouros} calouros</ToneBadge>
          {totalMatches > 0 && (
            <ToneBadge tone="green"><CheckCircle2 size={13} /> {totalMatches} matches</ToneBadge>
          )}
        </div>
      </div>

      {totalMatches === 0 ? (
        <div className="pt-card" style={{ padding: "52px 24px", textAlign: "center" }}>
          <div className="pt-empty-icon" style={{ margin: "0 auto 14px", width: 56, height: 56 }}>
            <Link2 size={24} />
          </div>
          <h2 style={{ margin: "0 0 8px", fontSize: 18 }}>Nenhum match gerado ainda</h2>
          <p className="pt-muted" style={{ maxWidth: 480, margin: "0 auto 22px", fontSize: 14 }}>
            O algoritmo distribui os {totalCalouros} calouros entre os {totalPadrinhos} padrinhos priorizando turno igual
            (200 pts), gênero (80 pts), proximidade de idade, cidade, bolsa e trabalho.
          </p>
          <button type="button" className="pt-btn pt-btn-primary pt-btn-lg" onClick={handleRunMatch}>
            <Sparkles size={16} /> Gerar matches automaticamente
          </button>
        </div>
      ) : (
        <div className="pt-card pt-card-flat">
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon" style={{ background: "var(--pt-green-tint)", color: "var(--pt-green-deep)" }}>
                <CheckCircle2 size={16} />
              </div>
              <h2 className="pt-card-title">Matches confirmados ({totalMatches})</h2>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {mode === "live" && (
                <a href="/match/lista-contatos" target="_blank" rel="noopener noreferrer" className="pt-btn pt-btn-soft-green pt-btn-sm">
                  <Printer size={13} /> Lista de contatos
                </a>
              )}
              <button type="button" className="pt-btn pt-btn-soft pt-btn-sm" onClick={handleRunMatch}>
                <RefreshCw size={13} /> Regerar match
              </button>
            </div>
          </div>

          <div className="pt-table-wrap">
            <table className="pt-table">
              <thead>
                <tr>
                  <th>Padrinho</th>
                  <th>Turno</th>
                  <th>Calouros vinculados</th>
                  <th style={{ textAlign: "right" }}>Qtd.</th>
                </tr>
              </thead>
              <tbody>
                {grupos.map((g) => (
                  <tr key={g.padrinho.id}>
                    <td style={{ fontWeight: 600 }}>
                      <Link to={`/padrinhos/${g.padrinho.id}`}>{abreviarNome(g.padrinho.nome)}</Link>
                    </td>
                    <td>
                      {g.padrinho.turno ? (
                        <ToneBadge tone={g.padrinho.turno === "Manhã" ? "amber" : "brand"}>{g.padrinho.turno}</ToneBadge>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                        {g.calouros.map((c) => (
                          <span key={c.id} className="pt-tag">
                            {abreviarNome(c.nome)}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="pt-td-right pt-mono pt-muted">{g.calouros.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </AppShell>
  );
}
