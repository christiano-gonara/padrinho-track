import { Link, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen, Check, Copy, Mail, Phone, X } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { Avatar, Aviso, TurnoTag } from "../components/ui/Kit";
import { StatusACGBadge, ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import "../styles/pages/Pessoas.css";
import { formatarDataBr } from "../data/scenarios";
import { useLiveData } from "../hooks/useLiveData";
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
  const { scenario, notify } = useApp();
  const { live } = useLiveData<LiveDetail>(`/api/padrinhos/${padrinhoId}`, [padrinhoId]);

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

  const limite = scenario.config.total_reunioes || 3;
  const primeiroNome = padrinho.nome.split(" ")[0];
  const foi = presencasHist.filter((x) => x.presente).length;

  function copiar(texto: string) {
    navigator.clipboard?.writeText(texto).then(
      () => notify("Contato copiado.", "success"),
      () => notify("Não deu pra copiar. Selecione o texto e copie.", "error")
    );
  }

  const SIT_TEMA: Record<string, [string, "green" | "amber" | "red" | "neutral"]> = {
    entregue: ["Entregue", "green"],
    atraso: ["Atrasou", "amber"],
    nao_entregue: ["Não entregue", "red"],
    pendente: ["No prazo", "neutral"],
  };

  return (
    <AppShell title={padrinho.nome}>
      <Link to="/padrinhos" className="pt-back-link">
        <ArrowLeft size={16} /> Voltar pra lista
      </Link>

      <section className="pt-card" style={{ margin: "8px 0 20px" }}>
        <div className="pt-perfil">
          <Avatar nome={padrinho.nome} size={72} />
          <div style={{ flex: 1, minWidth: 240 }}>
            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10 }}>
              <h1 className="pt-perfil-nome">{padrinho.nome}</h1>
              <StatusACGBadge status={status} />
            </div>
            <div className="pt-perfil-meta">
              <TurnoTag turno={padrinho.turno} />
              <span>Matrícula {padrinho.matricula}</span>
              {padrinho.email && (
                <span>
                  <Mail size={15} /> {padrinho.email}
                </span>
              )}
              {padrinho.telefone && (
                <span>
                  <Phone size={15} /> {padrinho.telefone}
                </span>
              )}
            </div>
          </div>
        </div>
      </section>

      {status === "alerta" && (
        <Aviso tipo="warn">
          <strong>Falta 1 cartão amarelo pro limite.</strong> Se {primeiroNome} faltar de novo sem justificar, perde as
          horas de ACG. Vale mandar uma mensagem antes da próxima reunião.
        </Aviso>
      )}
      {status === "inapto_amarelo" && (
        <Aviso tipo="bad">
          <strong>{primeiroNome} chegou ao limite de cartões amarelos</strong> e não vai receber a ACG neste semestre.
        </Aviso>
      )}
      {status === "inapto_vermelho" && (
        <Aviso tipo="bad">
          <strong>{primeiroNome} levou cartão vermelho.</strong> Não recebe a ACG e o caso precisa ir pro professor.
        </Aviso>
      )}

      <div className="pt-grid-2" style={{ gap: 20 }}>
        <div className="pt-stack" style={{ gap: 20 }}>
          <section className="pt-card">
            <div className="pt-cartoes-head" style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <h2 className="pt-card-title">Presença</h2>
              <strong style={{ fontSize: 15, color: "var(--pt-ink)" }}>
                {foi} de {presencasHist.length}
              </strong>
            </div>
            {presencasHist.length === 0 && <p style={{ margin: 0, color: "#475569" }}>Nenhuma reunião ainda.</p>}
            {presencasHist.map((pr, idx) => (
              <div key={idx} className="pt-row">
                <span style={{ width: 56, fontSize: 16, fontWeight: 800, color: "var(--pt-brand-deep)" }}>
                  {formatarDataBr(pr.data)}
                </span>
                <span style={{ flex: 1, fontSize: 15, color: "var(--pt-ink)" }}>{pr.tema || "Reunião"}</span>
                {pr.presente ? (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 14, fontWeight: 600, color: "var(--pt-green-deep)" }}>
                    <Check size={16} strokeWidth={2.6} /> Foi
                  </span>
                ) : pr.justificada ? (
                  <span style={{ fontSize: 14, fontWeight: 600, color: "var(--pt-brand-deep)" }}>Justificou</span>
                ) : (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 14, fontWeight: 600, color: "var(--pt-amber-deep)" }}>
                    <X size={16} strokeWidth={2.6} /> Faltou sem justificar
                  </span>
                )}
              </div>
            ))}
          </section>

          <section className="pt-card">
            <h2 className="pt-card-title" style={{ marginBottom: 10 }}>
              {temasHist.length > 1 ? "Temas que apresenta" : "Tema que apresenta"}
            </h2>
            {temasHist.length === 0 && <p style={{ margin: 0, color: "#475569" }}>Nenhum tema ainda.</p>}
            {temasHist.map((t, idx) => {
              const [label, tone] = SIT_TEMA[t.situacao] ?? (["—", "neutral"] as [string, "neutral"]);
              return (
                <div key={idx} className="pt-row">
                  <span className="pt-empty-icon" style={{ width: 44, height: 44 }}>
                    <BookOpen size={20} />
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: "var(--pt-ink)" }}>{t.titulo}</div>
                    <div style={{ fontSize: 14, color: "#475569" }}>Prazo {formatarDataBr(t.data_limite)}</div>
                  </div>
                  <ToneBadge tone={tone}>{label}</ToneBadge>
                </div>
              );
            })}
          </section>
        </div>

        <div className="pt-stack" style={{ gap: 20 }}>
          <section className="pt-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <h2 className="pt-card-title">Cartões amarelos</h2>
              <strong style={{ fontSize: 15, color: amarelos >= limite - 1 && amarelos > 0 ? "var(--pt-amber-deep)" : "var(--pt-ink)" }}>
                {amarelos} de {limite}
              </strong>
            </div>
            <p style={{ margin: "4px 0 14px", fontSize: 14.5, color: "#475569" }}>Com {limite}, perde a ACG.</p>
            <div style={{ display: "flex", gap: 10 }} aria-label={`${amarelos} de ${limite} cartões amarelos`}>
              {Array.from({ length: Math.max(limite, amarelos) }).map((_, i) => (
                <span key={i} className={`pt-cartao-grande ${i < amarelos ? "is-amarelo" : ""}`} />
              ))}
              {Array.from({ length: vermelhos }).map((_, i) => (
                <span key={`v${i}`} className="pt-cartao-grande is-vermelho" />
              ))}
            </div>
            <p style={{ margin: "14px 0 0", fontSize: 14.5, color: "#475569" }}>
              {vermelhos > 0 ? `${vermelhos} cartão vermelho.` : "Nenhum cartão vermelho."}
            </p>
            {advertencias.length > 0 && (
              <ul style={{ margin: "12px 0 0", paddingLeft: 18, fontSize: 14.5, color: "var(--pt-text)", lineHeight: 1.6 }}>
                {advertencias.map((a) => (
                  <li key={a.id}>
                    {formatarDataBr(a.data)}: {a.motivo}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="pt-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <h2 className="pt-card-title">Calouros</h2>
              <strong style={{ fontSize: 15, color: "var(--pt-ink)" }}>{calouros.length}</strong>
            </div>
            {calouros.length === 0 && <p style={{ margin: "8px 0 0", color: "#475569" }}>Ainda sem calouro.</p>}
            {calouros.map((c) => (
              <div key={c.id} className="pt-row">
                <Avatar nome={c.nome} size={36} tone="neutral" />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 15, fontWeight: 600, color: "var(--pt-ink)" }}>{c.nome}</div>
                  <div style={{ fontSize: 14, color: "#475569" }}>{c.telefone || "sem telefone"}</div>
                </div>
                {c.telefone && (
                  <button type="button" className="pt-chip" onClick={() => copiar(`${c.nome} ${c.telefone}`)} aria-label={`Copiar contato de ${c.nome}`}>
                    <Copy size={15} /> Copiar
                  </button>
                )}
              </div>
            ))}
          </section>
        </div>
      </div>
    </AppShell>
  );
}
