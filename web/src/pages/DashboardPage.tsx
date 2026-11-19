import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Check, FileText, Plus } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { Avatar, Gauge, PresencaBar, PresencaLegenda, StatsRow } from "../components/ui/Kit";
import { STATUS_LABEL, StatusACGBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { formatarDataBr } from "../data/scenarios";
import { useLiveData } from "../hooks/useLiveData";
import { Padrinho, Reuniao, StatusACG } from "../types/domain";
import "../styles/pages/DashboardPage.css";

interface LiveDashboardResponse {
  dados: { padrinho: Padrinho; status: Padrinho["status"]; amarelos: number; vermelhos: number }[];
  presencas_por_reuniao: { id: number; label: string; tema: string; presentes: number; ausentes: number }[];
  proxima_reuniao: { data?: string; tema?: string } | null;
  proximo_tema: { titulo?: string; data_limite?: string } | null;
}

function motivoAtencao(p: Padrinho): string {
  if (p.status === "inapto_vermelho") return "Levou cartão vermelho. O caso precisa ir pro professor.";
  if (p.status === "inapto_amarelo") return `Chegou a ${p.amarelos} cartões amarelos e perdeu a ACG.`;
  return `Tem ${p.amarelos} cartão${p.amarelos === 1 ? "" : "ões"} amarelo${p.amarelos === 1 ? "" : "s"}. Mais um e perde a ACG.`;
}

const ORDEM_ATENCAO: StatusACG[] = ["inapto_vermelho", "inapto_amarelo", "alerta"];

export function DashboardPage() {
  const { scenario } = useApp();
  const navigate = useNavigate();
  const { live: liveData } = useLiveData<LiveDashboardResponse>("/api/dashboard");

  const padrinhos: Padrinho[] = liveData
    ? liveData.dados.map((d) => ({ ...d.padrinho, status: d.status, amarelos: d.amarelos, vermelhos: d.vermelhos }))
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

  const contar = (s: StatusACG) => padrinhos.filter((p) => p.status === s).length;
  const counts: Record<StatusACG, number> = {
    apto: contar("apto"),
    alerta: contar("alerta"),
    inapto_amarelo: contar("inapto_amarelo"),
    inapto_vermelho: contar("inapto_vermelho"),
  };
  const recebem = counts.apto + counts.alerta;
  const pct = padrinhos.length ? Math.round((recebem / padrinhos.length) * 100) : 0;

  const atencao = padrinhos
    .filter((p) => p.status !== "apto")
    .sort((a, b) => ORDEM_ATENCAO.indexOf(a.status) - ORDEM_ATENCAO.indexOf(b.status));

  const totalCalouros = scenario.matches.reduce((acc, g) => acc + g.calouros.length, 0) || scenario.calourosSoltos.length;
  const totalReunioes = scenario.config.total_reunioes || reunioes.length;
  const temDuplas = scenario.matches.some((g) => g.calouros.length > 0);
  const reunioesFeitas = reunioes.length;

  const etapas = [
    { titulo: "Inscrições", texto: `${padrinhos.length} padrinhos e ${scenario.calourosSoltos.length} calouros`, feito: padrinhos.length > 0, to: "/inicio" },
    { titulo: "Duplas formadas", texto: temDuplas ? `${totalCalouros} calouros com padrinho` : "Ainda não formadas", feito: temDuplas, to: "/match" },
    { titulo: "Reuniões", texto: `${reunioesFeitas} de ${totalReunioes} feitas`, feito: reunioesFeitas >= totalReunioes && totalReunioes > 0, to: "/reunioes" },
    { titulo: "Fechamento", texto: "Gerar lista e certificados", feito: false, to: "/relatorio" },
  ];
  const atual = etapas.findIndex((e) => !e.feito);

  return (
    <AppShell title="Painel">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Painel do semestre</h1>
          <p className="pt-page-subtitle">Tudo o que está acontecendo no apadrinhamento, num lugar só.</p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-ghost" onClick={() => navigate("/reunioes")}>
            <Plus size={17} /> Nova reunião
          </button>
          <button type="button" className="pt-btn pt-btn-primary" onClick={() => navigate("/relatorio")}>
            <FileText size={17} /> Gerar certificados
          </button>
        </div>
      </div>

      <StatsRow
        items={[
          { valor: padrinhos.length, texto: "padrinhos e madrinhas" },
          { valor: totalCalouros, texto: "calouros acompanhados" },
          { valor: `${reunioesFeitas} de ${totalReunioes}`, texto: "reuniões feitas" },
          { valor: scenario.temas.length, texto: "temas no cronograma" },
        ]}
      />

      <section className="pt-card" style={{ marginBottom: 20 }}>
        <h2 className="pt-card-title" style={{ marginBottom: 18 }}>Onde o semestre está</h2>
        <ol className="pt-etapas">
          {etapas.map((e, i) => (
            <li key={e.titulo}>
              <Link to={e.to} className="pt-etapa">
                <span className={`pt-etapa-dot ${e.feito ? "is-feito" : i === atual ? "is-atual" : ""}`}>
                  {e.feito ? <Check size={17} strokeWidth={2.8} /> : i + 1}
                </span>
                <span>
                  <strong>{e.titulo}</strong>
                  <span>{e.texto}</span>
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </section>

      <div className="pt-split">
        <section className="pt-card">
          <div className="pt-dash-head">
            <div>
              <h2 className="pt-card-title">Precisa da sua atenção</h2>
              <p className="pt-dash-sub">Quem está perto de perder a ACG ou já perdeu.</p>
            </div>
            {atencao.length > 0 && <span className="pt-dash-count">{atencao.length} pessoa{atencao.length > 1 ? "s" : ""}</span>}
          </div>
          {atencao.length === 0 ? (
            <p className="pt-dash-vazio">Ninguém em risco por enquanto. Tudo certo!</p>
          ) : (
            atencao.map((p) => (
              <div key={p.id} className="pt-row">
                <Avatar nome={p.nome} size={40} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="pt-dash-nome">
                    <strong>{p.nome}</strong>
                    <StatusACGBadge status={p.status} />
                  </div>
                  <div className="pt-dash-motivo">{motivoAtencao(p)}</div>
                </div>
                <Link to={`/padrinhos/${p.id}`} className="pt-dash-link">
                  Ver <ArrowRight size={15} />
                </Link>
              </div>
            ))
          )}
        </section>

        <section className="pt-card">
          <h2 className="pt-card-title" style={{ marginBottom: 12 }}>Quem recebe ACG</h2>
          <Gauge pct={pct} legenda={`${recebem} de ${padrinhos.length} recebem`} />
          <div style={{ marginTop: 16 }}>
            {(Object.keys(counts) as StatusACG[]).map((s) => (
              <div key={s} className="pt-dash-leg">
                <span>
                  <i className={`is-${s}`} />
                  {STATUS_LABEL[s]}
                </span>
                <strong>{counts[s]}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="pt-card">
        <div className="pt-dash-head">
          <h2 className="pt-card-title">Presença nas reuniões</h2>
          <PresencaLegenda />
        </div>
        {reunioes.length === 0 && <p className="pt-dash-vazio">Nenhuma reunião ainda.</p>}
        {reunioes.map((r) => {
          const total = r.presentes + r.justificadas + r.ausentes;
          return (
            <div key={r.id} className="pt-dash-reuniao">
              <span className="pt-dash-data">{r.data?.includes("-") ? formatarDataBr(r.data) : r.data}</span>
              <span className="pt-dash-tema">{r.tema || "Reunião"}</span>
              <PresencaBar foi={r.presentes} justificou={r.justificadas} faltou={r.ausentes} />
              <span className="pt-dash-total">
                <strong>{r.presentes}</strong> de {total}
              </span>
            </div>
          );
        })}
      </section>
    </AppShell>
  );
}
