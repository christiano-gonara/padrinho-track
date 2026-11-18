import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, BookOpen, Mail, Phone, ShieldAlert, Smile, UserCheck, XCircle } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { MetricCard } from "../components/ui/MetricCard";
import { StatusACGBadge, ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { formatarDataBr } from "../data/scenarios";
import { apiFetch } from "../services/api";
import { Advertencia, Calouro, Padrinho } from "../types/domain";

interface LiveDetail {
  padrinho: Padrinho;
  status: { status: Padrinho["status"]; amarelos: number; vermelhos: number };
  historico: {
    presencas: { data: string; tema: string; presente: number; justificada: number }[];
    temas: { titulo: string; data_limite: string; situacao: string }[];
  };
  advertencias: Advertencia[];
  calouros_match: Calouro[];
}

export function PadrinhoDetalhePage() {
  const { id } = useParams();
  const padrinhoId = Number(id);
  const { mode, scenario } = useApp();
  const [live, setLive] = useState<LiveDetail | null>(null);

  useEffect(() => {
    if (mode !== "live") {
      setLive(null);
      return;
    }
    apiFetch<LiveDetail>(`/api/padrinhos/${padrinhoId}`)
      .then(setLive)
      .catch(() => setLive(null));
  }, [mode, padrinhoId]);

  const demoPadrinho = scenario.padrinhos.find((p) => p.id === padrinhoId) || scenario.padrinhos[0];
  const padrinho = live?.padrinho ?? demoPadrinho;

  if (!padrinho) {
    return (
      <AppShell title="Detalhe do padrinho">
        <div className="pt-card">Padrinho não encontrado.</div>
      </AppShell>
    );
  }

  const amarelos = live ? live.status.amarelos : padrinho.amarelos;
  const vermelhos = live ? live.status.vermelhos : padrinho.vermelhos;
  const status = live ? live.status.status : padrinho.status;

  const presencasHist = live
    ? live.historico.presencas
    : scenario.reunioes.map((r) => {
        const reg = (scenario.presencasPorReuniao[r.id] || []).find((x) => x.id === padrinho.id);
        return {
          data: r.data,
          tema: r.tema,
          presente: reg?.presente ?? 0,
          justificada: reg?.justificada ?? 0,
        };
      });

  const temasHist = live
    ? live.historico.temas
    : scenario.temas.filter((t) => t.responsaveis.some((r) => r.id === padrinho.id));

  const advertencias = live
    ? live.advertencias
    : scenario.advertencias.filter((a) => a.padrinho_id === padrinho.id);

  const calouros = live
    ? live.calouros_match
    : scenario.matches.find((m) => m.padrinho.id === padrinho.id)?.calouros || [];

  return (
    <AppShell title="Detalhe do padrinho">
      <div className="pt-page-head">
        <div>
          <Link to="/padrinhos" className="pt-back-link">
            <ArrowLeft size={14} /> voltar para padrinhos
          </Link>
          <h1 className="pt-page-title">{padrinho.nome}</h1>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 16px", marginTop: 8, fontSize: 13.5, color: "var(--pt-muted)" }}>
            <span className="pt-mono">Mat. {padrinho.matricula}</span>
            {padrinho.email && (
              <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                <Mail size={14} /> {padrinho.email}
              </span>
            )}
            {padrinho.telefone && (
              <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                <Phone size={14} /> {padrinho.telefone}
              </span>
            )}
            {padrinho.turno && <ToneBadge tone={padrinho.turno === "Manhã" ? "amber" : "brand"}>{padrinho.turno}</ToneBadge>}
          </div>
        </div>
        <div className="pt-page-actions">
          <StatusACGBadge status={status} />
        </div>
      </div>

      <div className="pt-grid-2" style={{ marginBottom: 22 }}>
        <MetricCard label="Cartões Amarelos" value={amarelos} hint="faltas / atrasos" tone="amber" icon={<AlertTriangle size={16} />} />
        <MetricCard label="Cartões Vermelhos" value={vermelhos} hint="ocorrências graves" tone="red" icon={<XCircle size={16} />} />
      </div>

      <div className="pt-grid-2" style={{ marginBottom: 22 }}>
        <div className="pt-card pt-card-flat">
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><UserCheck size={16} /></div>
              <h2 className="pt-card-title">Presenças</h2>
            </div>
          </div>
          <div className="pt-table-wrap">
            <table className="pt-table pt-table-compact">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Tema</th>
                  <th style={{ textAlign: "center" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {presencasHist.map((pr, idx) => (
                  <tr key={idx}>
                    <td className="pt-mono pt-muted">{formatarDataBr(pr.data)}</td>
                    <td className="pt-muted">{pr.tema || "—"}</td>
                    <td className="pt-td-center">
                      {pr.presente ? (
                        <ToneBadge tone="green">Presente</ToneBadge>
                      ) : pr.justificada ? (
                        <ToneBadge tone="brand">Justificada</ToneBadge>
                      ) : (
                        <ToneBadge tone="red">Ausente</ToneBadge>
                      )}
                    </td>
                  </tr>
                ))}
                {presencasHist.length === 0 && (
                  <tr>
                    <td colSpan={3} style={{ textAlign: "center", padding: 24, color: "var(--pt-muted)" }}>
                      Nenhuma presença registrada.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="pt-card pt-card-flat">
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><BookOpen size={16} /></div>
              <h2 className="pt-card-title">Temas atribuídos</h2>
            </div>
          </div>
          <div className="pt-table-wrap">
            <table className="pt-table pt-table-compact">
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Prazo</th>
                  <th style={{ textAlign: "center" }}>Situação</th>
                </tr>
              </thead>
              <tbody>
                {temasHist.map((t, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 500 }}>{t.titulo}</td>
                    <td className="pt-mono pt-muted">{formatarDataBr(t.data_limite)}</td>
                    <td className="pt-td-center">
                      {t.situacao === "entregue" ? (
                        <ToneBadge tone="green">Entregue</ToneBadge>
                      ) : t.situacao === "atraso" ? (
                        <ToneBadge tone="amber">Atraso</ToneBadge>
                      ) : t.situacao === "nao_entregue" ? (
                        <ToneBadge tone="red">Não entregue</ToneBadge>
                      ) : (
                        <ToneBadge tone="neutral">Pendente</ToneBadge>
                      )}
                    </td>
                  </tr>
                ))}
                {temasHist.length === 0 && (
                  <tr>
                    <td colSpan={3} style={{ textAlign: "center", padding: 24, color: "var(--pt-muted)" }}>
                      Nenhum tema atribuído.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {calouros.length > 0 && (
        <div className="pt-card pt-card-flat" style={{ marginBottom: 22 }}>
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><Smile size={16} /></div>
              <h2 className="pt-card-title">Calouros vinculados</h2>
            </div>
            <span className="pt-muted" style={{ fontSize: 12.5 }}>{calouros.length} calouro(s)</span>
          </div>
          <div className="pt-card-body" style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {calouros.map((c) => (
              <span key={c.id} className="pt-tag" style={{ padding: "6px 12px", fontSize: 13 }}>
                <Smile size={13} /> <strong>{c.nome}</strong> {c.telefone ? `· ${c.telefone}` : ""}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon" style={{ background: "var(--pt-red-tint)", color: "var(--pt-red-deep)" }}>
              <ShieldAlert size={16} />
            </div>
            <h2 className="pt-card-title">Advertências</h2>
          </div>
        </div>
        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th style={{ textAlign: "center" }}>Tipo</th>
                <th>Origem</th>
                <th>Motivo</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {advertencias.map((a) => (
                <tr key={a.id}>
                  <td className="pt-td-center">
                    <ToneBadge tone={a.tipo === "amarelo" ? "amber" : "red"}>
                      {a.tipo === "amarelo" ? "Advertência" : "Advertência Grave"}
                    </ToneBadge>
                  </td>
                  <td className="pt-muted">{a.origem}</td>
                  <td className="pt-muted">{a.motivo}</td>
                  <td className="pt-mono pt-muted">{formatarDataBr(a.data)}</td>
                </tr>
              ))}
              {advertencias.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: "center", padding: 24, color: "var(--pt-muted)" }}>
                    Nenhuma advertência registrada.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
