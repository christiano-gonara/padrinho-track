import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  Eye,
  GitBranch,
  Users,
  Video,
  XCircle,
} from "lucide-react";
import { AttendanceBarChart } from "../components/charts/AttendanceBarChart";
import { SemesterFlowDiagram } from "../components/charts/SemesterFlowDiagram";
import { StatusBarChart } from "../components/charts/StatusBarChart";
import { AppShell } from "../components/layout/AppShell";
import { MetricCard } from "../components/ui/MetricCard";
import { StatusACGBadge, ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { abreviarNome, formatarDataBr } from "../data/scenarios";
import { apiFetch } from "../services/api";
import { Padrinho, Reuniao } from "../types/domain";
import "./DashboardPage.css";

interface LiveDashboardResponse {
  dados: { padrinho: Padrinho; status: Padrinho["status"]; amarelos: number; vermelhos: number }[];
  presencas_por_reuniao: { id: number; label: string; tema: string; presentes: number; ausentes: number }[];
  proxima_reuniao: { data?: string; tema?: string } | null;
  proximo_tema: { titulo?: string; data_limite?: string } | null;
}

export function DashboardPage() {
  const { mode, scenario } = useApp();
  const navigate = useNavigate();
  const [liveData, setLiveData] = useState<LiveDashboardResponse | null>(null);

  useEffect(() => {
    if (mode !== "live") {
      setLiveData(null);
      return;
    }
    apiFetch<LiveDashboardResponse>("/api/dashboard")
      .then(setLiveData)
      .catch(() => setLiveData(null));
  }, [mode]);

  const padrinhos: Padrinho[] = liveData
    ? liveData.dados.map((d) => ({
        ...d.padrinho,
        status: d.status,
        amarelos: d.amarelos,
        vermelhos: d.vermelhos,
      }))
    : scenario.padrinhos;

  const reunioes: Reuniao[] = liveData
    ? liveData.presencas_por_reuniao.map((r) => ({
        id: r.id,
        data: r.label,
        tema: r.tema,
        descricao: "",
        presentes: r.presentes,
        justificadas: 0,
        ausentes: r.ausentes,
      }))
    : scenario.reunioes;

  const counts = {
    aptos: padrinhos.filter((p) => p.status === "apto").length,
    alertas: padrinhos.filter((p) => p.status === "alerta").length,
    reprovados: padrinhos.filter((p) => p.status === "inapto_amarelo").length,
    reportados: padrinhos.filter((p) => p.status === "inapto_vermelho").length,
  };

  const ultimaReuniao = liveData
    ? liveData.proxima_reuniao
    : scenario.reunioes[scenario.reunioes.length - 1];
  const proximoTema = liveData
    ? liveData.proximo_tema
    : scenario.temas.find((t) => t.situacao === "pendente");

  return (
    <AppShell title="Dashboard">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Visão geral</h1>
          <p className="pt-page-subtitle">Acompanhamento do programa de mentoria · {scenario.config.semestre}</p>
        </div>
        <div className="pt-page-actions">
          {ultimaReuniao && (
            <span className="pt-info-pill is-brand">
              <Video size={15} />
              <span>
                <strong>Última reunião:</strong>{" "}
                {ultimaReuniao.data?.includes("-") ? formatarDataBr(ultimaReuniao.data) : ultimaReuniao.data} —{" "}
                {ultimaReuniao.tema || "sem tema"}
              </span>
            </span>
          )}
          {proximoTema && (
            <span className="pt-info-pill is-amber">
              <Clock size={15} />
              <span>
                <strong>Próximo prazo:</strong> {proximoTema.titulo} ({formatarDataBr(proximoTema.data_limite)})
              </span>
            </span>
          )}
        </div>
      </div>

      <div className="pt-grid-4" style={{ marginBottom: 22 }}>
        <MetricCard label="Aptos" value={counts.aptos} hint="elegíveis ACG" tone="green" icon={<CheckCircle2 size={16} />} />
        <MetricCard label="Em alerta" value={counts.alertas} hint="aviso preventivo" tone="amber" icon={<AlertTriangle size={16} />} />
        <MetricCard label="Reprovados" value={counts.reprovados} hint="limite de faltas" tone="orange" icon={<Clock size={16} />} />
        <MetricCard label="Reportados" value={counts.reportados} hint="ação coordenação" tone="red" icon={<XCircle size={16} />} />
      </div>

      {/* Gráficos em barras (sem pizza/rosca) */}
      <div className="pt-dash-charts">
        <div className="pt-card">
          <div className="pt-card-header" style={{ padding: "0 0 14px", marginBottom: 14 }}>
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><BarChart3 size={16} /></div>
              <h2 className="pt-card-title">Distribuição de status ACG</h2>
            </div>
            <span className="pt-muted" style={{ fontSize: 12 }}>{padrinhos.length} no total</span>
          </div>
          <StatusBarChart counts={counts} />
        </div>

        <div className="pt-card">
          <div className="pt-card-header" style={{ padding: "0 0 14px", marginBottom: 14 }}>
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><Video size={16} /></div>
              <h2 className="pt-card-title">Presenças por reunião</h2>
            </div>
            <span className="pt-muted" style={{ fontSize: 12 }}>{reunioes.length} reuniões</span>
          </div>
          <AttendanceBarChart reunioes={reunioes} />
        </div>
      </div>

      {/* Diagrama do Fluxo do Semestre */}
      <div className="pt-card" style={{ marginBottom: 22 }}>
        <div className="pt-card-header" style={{ padding: "0 0 14px", marginBottom: 14 }}>
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon"><GitBranch size={16} /></div>
            <h2 className="pt-card-title">Diagrama do fluxo semestral</h2>
          </div>
          <span className="pt-muted" style={{ fontSize: 12 }}>Clique em uma etapa para navegar</span>
        </div>
        <SemesterFlowDiagram
          padrinhosCount={padrinhos.length}
          matchesCount={scenario.matches.length}
          reunioesCount={reunioes.length}
          temasCount={scenario.temas.length}
          aptosCount={counts.aptos + counts.alertas}
        />
      </div>

      {/* Tabela de padrinhos */}
      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon"><Users size={16} /></div>
            <h2 className="pt-card-title">Padrinhos</h2>
          </div>
          <span className="pt-muted" style={{ fontSize: 12.5 }}>{padrinhos.length} cadastrados</span>
        </div>
        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Padrinho</th>
                <th>Matrícula</th>
                <th style={{ textAlign: "center" }}>Amarelos</th>
                <th style={{ textAlign: "center" }}>Vermelhos</th>
                <th style={{ textAlign: "center" }}>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {padrinhos.map((p) => {
                const parts = p.nome.split(" ");
                const ini = ((parts[0]?.[0] || "") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
                return (
                  <tr key={p.id} className="is-clickable" onClick={() => navigate(`/padrinhos/${p.id}`)}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 600 }}>
                        <span className="pt-avatar">{ini}</span>
                        <span>{abreviarNome(p.nome)}</span>
                      </div>
                    </td>
                    <td className="pt-mono pt-muted">{p.matricula}</td>
                    <td className="pt-td-center">
                      {p.amarelos > 0 ? <ToneBadge tone="amber">{p.amarelos}</ToneBadge> : <span className="pt-muted">—</span>}
                    </td>
                    <td className="pt-td-center">
                      {p.vermelhos > 0 ? <ToneBadge tone="red">{p.vermelhos}</ToneBadge> : <span className="pt-muted">—</span>}
                    </td>
                    <td className="pt-td-center">
                      <StatusACGBadge status={p.status} />
                    </td>
                    <td className="pt-td-right">
                      <button
                        type="button"
                        className="pt-btn pt-btn-ghost pt-btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/padrinhos/${p.id}`);
                        }}
                      >
                        <Eye size={13} /> Detalhes
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
