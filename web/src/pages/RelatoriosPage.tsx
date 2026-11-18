import { Link } from "react-router-dom";
import { AlertTriangle, Award, BarChart3, CheckCircle2, Clock, ExternalLink, FileBarChart2, FolderDown, Printer, XCircle } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { MetricCard } from "../components/ui/MetricCard";
import { StatusACGBadge, ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { abreviarNome } from "../data/scenarios";
import { useLiveData } from "../hooks/useLiveData";
import { Padrinho } from "../types/domain";

interface RelatorioRow {
  padrinho: Padrinho;
  total_reunioes: number;
  total_presentes: number;
  amarelos: number;
  vermelhos: number;
  status: Padrinho["status"];
}

interface LiveRelatorioResp {
  dados: RelatorioRow[];
  stats: {
    por_turno: Record<string, number>;
    pct_feminino: number;
    pct_masculino: number;
    pct_bolsista: number;
    pct_bh: number;
    pct_trabalha: number;
    total: number;
  };
}

export function RelatoriosPage() {
  const { mode, scenario } = useApp();
  const { live } = useLiveData<LiveRelatorioResp>("/api/relatorio");
  const base = import.meta.env.BASE_URL;

  const rows: RelatorioRow[] = live
    ? live.dados
    : scenario.padrinhos.map((p) => {
        const presCount = scenario.reunioes.filter((r) =>
          (scenario.presencasPorReuniao[r.id] || []).some((x) => x.id === p.id && x.presente === 1)
        ).length;
        return {
          padrinho: p,
          total_reunioes: scenario.reunioes.length,
          total_presentes: presCount,
          amarelos: p.amarelos,
          vermelhos: p.vermelhos,
          status: p.status,
        };
      });

  const porTurno = live
    ? live.stats.por_turno
    : scenario.padrinhos.reduce<Record<string, number>>((acc, p) => {
        const t = p.turno || "—";
        acc[t] = (acc[t] || 0) + 1;
        return acc;
      }, {});

  const total = rows.length || 1;
  const aptos = rows.filter((r) => r.status === "apto").length;
  const alertas = rows.filter((r) => r.status === "alerta").length;
  const reprovados = rows.filter((r) => r.status === "inapto_amarelo").length;
  const reportados = rows.filter((r) => r.status === "inapto_vermelho").length;

  const aptidaoUrl = mode === "live" ? "/relatorio/aptidao" : `${base}exemplos/relatorio-aptidao.html`;
  const resumoUrl = mode === "live" ? "/relatorio/resumo" : `${base}exemplos/resumo-semestre.html`;
  const certUrl = mode === "live" ? "/relatorio/certificados/zip" : `${base}exemplos/certificado.html`;

  return (
    <AppShell title="Relatório">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Relatório geral e certificados</h1>
          <p className="pt-page-subtitle">Aptidão para ACG — resultado final e emissão</p>
        </div>
        <div className="pt-page-actions">
          <a href={aptidaoUrl} target="_blank" rel="noopener noreferrer" className="pt-btn pt-btn-primary">
            <Printer size={15} /> Aptidão ACG {mode === "demo" && <ExternalLink size={13} />}
          </a>
          <a href={resumoUrl} target="_blank" rel="noopener noreferrer" className="pt-btn pt-btn-soft">
            <FileBarChart2 size={15} /> Resumo do semestre
          </a>
          <a href={certUrl} target={mode === "demo" ? "_blank" : undefined} rel="noopener noreferrer" className="pt-btn pt-btn-ghost">
            {mode === "live" ? <FolderDown size={15} /> : <Award size={15} />}
            {mode === "live" ? "Baixar certificados (ZIP)" : "Ver certificado exemplo"}
          </a>
        </div>
      </div>

      <div className="pt-grid-4" style={{ marginBottom: 22 }}>
        <MetricCard label="Aptos" value={aptos} tone="green" icon={<CheckCircle2 size={16} />} />
        <MetricCard label="Em alerta" value={alertas} tone="amber" icon={<AlertTriangle size={16} />} />
        <MetricCard label="Reprovados" value={reprovados} tone="orange" icon={<Clock size={16} />} />
        <MetricCard label="Reportados" value={reportados} tone="red" icon={<XCircle size={16} />} />
      </div>

      <div className="pt-grid-2" style={{ marginBottom: 22 }}>
        <div className="pt-card">
          <div className="pt-card-header" style={{ padding: "0 0 12px", marginBottom: 12 }}>
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><BarChart3 size={16} /></div>
              <h2 className="pt-card-title">Padrinhos por turno (barras)</h2>
            </div>
          </div>
          <div className="pt-stack-sm">
            {Object.entries(porTurno).map(([turno, qtd]) => (
              <div key={turno} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span className="pt-muted" style={{ width: 64, fontSize: 13 }}>{turno}</span>
                <div style={{ flex: 1, height: 10, borderRadius: 999, background: "var(--pt-bg-alt)", overflow: "hidden" }}>
                  <div style={{ width: `${Math.round((qtd / total) * 100)}%`, height: "100%", background: "var(--pt-brand)" }} />
                </div>
                <span className="pt-mono" style={{ width: 32, textAlign: "right", fontSize: 13, fontWeight: 700 }}>{qtd}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="pt-card">
          <div className="pt-card-header" style={{ padding: "0 0 12px", marginBottom: 12 }}>
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><Award size={16} /></div>
              <h2 className="pt-card-title">Emissão de certificados</h2>
            </div>
          </div>
          <p className="pt-muted" style={{ fontSize: 13.5, margin: "0 0 14px", lineHeight: 1.55 }}>
            Padrinhos com status <strong>Apto</strong> ou <strong>Em alerta</strong> ({aptos + alertas} no cenário atual)
            recebem certificado de <strong>04 horas ACG</strong>, e a coordenação recebe de <strong>05 horas</strong>.
          </p>
          <a href={`${base}exemplos/certificado.html`} target="_blank" rel="noopener noreferrer" className="pt-btn pt-btn-soft pt-btn-sm">
            <Award size={14} /> Visualizar certificado modelo A4
          </a>
        </div>
      </div>

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon"><FileBarChart2 size={16} /></div>
            <h2 className="pt-card-title">Resultado por padrinho</h2>
          </div>
          <span className="pt-muted" style={{ fontSize: 12.5 }}>{rows.length} padrinhos</span>
        </div>
        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Padrinho</th>
                <th>Matrícula</th>
                <th style={{ textAlign: "center" }}>Reuniões</th>
                <th style={{ textAlign: "center" }}>Presenças</th>
                <th style={{ textAlign: "center" }}>Amarelos</th>
                <th style={{ textAlign: "center" }}>Vermelhos</th>
                <th style={{ textAlign: "center" }}>Status ACG</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.padrinho.id}>
                  <td style={{ fontWeight: 600 }}>
                    <Link to={`/padrinhos/${r.padrinho.id}`}>{abreviarNome(r.padrinho.nome)}</Link>
                  </td>
                  <td className="pt-mono pt-muted">{r.padrinho.matricula}</td>
                  <td className="pt-td-center pt-muted">{r.total_reunioes}</td>
                  <td className="pt-td-center pt-muted">{r.total_presentes}</td>
                  <td className="pt-td-center">
                    {r.amarelos > 0 ? <ToneBadge tone="amber">{r.amarelos}</ToneBadge> : "—"}
                  </td>
                  <td className="pt-td-center">
                    {r.vermelhos > 0 ? <ToneBadge tone="red">{r.vermelhos}</ToneBadge> : "—"}
                  </td>
                  <td className="pt-td-center"><StatusACGBadge status={r.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
