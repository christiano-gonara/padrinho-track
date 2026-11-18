import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Award,
  BarChart3,
  BookOpen,
  CheckCircle2,
  ExternalLink,
  FileCheck2,
  Github,
  GraduationCap,
  LogIn,
  Play,
  Users,
} from "lucide-react";
import { SemesterFlowDiagram } from "../components/charts/SemesterFlowDiagram";
import { ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { getScenarioList } from "../data/scenarios";
import { ScenarioId } from "../types/domain";
import "./LandingPage.css";

const REPO_URL = "https://github.com/christiano-gonara/padrinho-track";

export function LandingPage() {
  const { scenario, setScenarioId } = useApp();
  const navigate = useNavigate();
  const [docTab, setDocTab] = useState<"certificado" | "aptidao" | "resumo">("certificado");

  const base = import.meta.env.BASE_URL;
  const scenarios = getScenarioList();

  function abrirCenario(id: ScenarioId, rota = "/dashboard") {
    setScenarioId(id);
    navigate(rota);
  }

  const docLinks = {
    certificado: `${base}exemplos/certificado.html`,
    aptidao: `${base}exemplos/relatorio-aptidao.html`,
    resumo: `${base}exemplos/resumo-semestre.html`,
  };

  const counts = {
    aptos: scenario.padrinhos.filter((p) => p.status === "apto").length,
    alertas: scenario.padrinhos.filter((p) => p.status === "alerta").length,
  };

  return (
    <div className="lp-wrap">
      {/* Barra rápida para exemplos e repositório */}
      <div className="lp-notice">
        <div className="lp-notice-inner">
          <span>
            Quer ir direto aos documentos de fim de semestre? Abra os modelos reais abaixo:
          </span>
          <div className="lp-notice-links">
            <a href={docLinks.aptidao} target="_blank" rel="noopener noreferrer">
              Relatório ACG <ExternalLink size={13} />
            </a>
            <a href={docLinks.certificado} target="_blank" rel="noopener noreferrer">
              Certificado A4 <ExternalLink size={13} />
            </a>
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
              GitHub <Github size={13} />
            </a>
          </div>
        </div>
      </div>

      {/* Navbar flutuante em pílula */}
      <div className="lp-header-slot">
        <header className="lp-header-pill">
          <a href="#topo">
            <img className="lp-logo" src={`${base}brand/padrinho-track-lockup.svg`} alt="Padrinho Track" />
          </a>
          <nav className="lp-nav" aria-label="Navegação da apresentação">
            <a href="#cenarios">Cenários</a>
            <a href="#como-funciona">Como funciona</a>
            <a href="#documentos">Relatórios</a>
          </nav>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              className="pt-btn pt-btn-ghost pt-btn-sm lp-pill-btn"
              onClick={() => navigate("/login")}
            >
              <LogIn size={14} /> Entrar
            </button>
            <button
              type="button"
              className="pt-btn pt-btn-primary pt-btn-sm lp-pill-btn"
              onClick={() => abrirCenario("fechamento", "/dashboard")}
            >
              Abrir painel
            </button>
          </div>
        </header>
      </div>

      <main id="topo">
        {/* Hero editorial com letras grandes e composição visual */}
        <section className="lp-hero-band">
          <div className="lp-hero">
            <div>
              <p className="lp-eyebrow">
                <span className="lp-eyebrow-icons">
                  <GraduationCap size={15} />
                  <Users size={15} />
                  <Award size={15} />
                </span>
                Para coordenação e padrinhos · PUC Minas
              </p>

              <h1>
                Apadrinhamento de calouros,{" "}
                <span className="lp-highlight">sem planilha solta.</span>
              </h1>

              <p className="lp-lede">
                Você importa os inscritos, junta cada calouro com um padrinho do mesmo turno e acompanha reuniões, temas e certificados num lugar só.
              </p>

              <div className="lp-hero-actions">
                <button
                  type="button"
                  className="pt-btn pt-btn-primary lp-btn-hero"
                  onClick={() => abrirCenario("fechamento", "/dashboard")}
                >
                  Testar telas com dados <ArrowRight size={17} />
                </button>
                <a className="pt-btn pt-btn-ghost lp-btn-hero" href="#documentos">
                  Ver relatório e certificado
                </a>
              </div>

              <p className="lp-hero-note">
                Sem precisar instalar nada: clique acima e navegue pelos cenários reais do semestre.
              </p>
            </div>

            {/* Composição visual clara (cartão de acompanhamento + selo flutuante) */}
            <div className="lp-visual-stage">
              <div className="lp-visual-blob" />
              <div className="lp-visual-card">
                <div className="lp-visual-card-top">
                  <div>
                    <span className="lp-visual-kicker">Acompanhamento do semestre</span>
                    <h2 className="lp-visual-name">Alice Mendonça · Manhã</h2>
                  </div>
                  <ToneBadge tone="green">Apto ACG</ToneBadge>
                </div>

                <div className="lp-visual-steps">
                  <div className="lp-visual-step is-done">
                    <span className="lp-visual-num">1</span>
                    <div className="lp-visual-step-text">
                      <strong>Match feito por afinidade</strong>
                      <span>2 calouros do turno da manhã vinculados</span>
                    </div>
                  </div>
                  <div className="lp-visual-step is-done">
                    <span className="lp-visual-num">2</span>
                    <div className="lp-visual-step-text">
                      <strong>Reuniões e temas em dia</strong>
                      <span>3/3 presenças e material entregue no prazo</span>
                    </div>
                  </div>
                  <div className="lp-visual-step">
                    <span className="lp-visual-num" style={{ background: "var(--pt-green)" }}>
                      <CheckCircle2 size={15} />
                    </span>
                    <div className="lp-visual-step-text">
                      <strong>Certificado pronto para baixar</strong>
                      <span>04 horas de ACG emitidas em PDF</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="lp-floating-cert">
                <Award size={17} color="#93c5fd" />
                <span>Certificado A4 + Relatório ACG prontos</span>
              </div>
            </div>
          </div>

          {/* Frase-resumo grande */}
          <div className="lp-quote-band">
            <p className="lp-quote-text">
              “Um semestre inteiro vira <strong>um painel só</strong>: a coordenação acompanha as faltas, aplica as regras automaticamente e entrega os <strong>certificados no fim do prazo</strong>.”
            </p>
          </div>
        </section>

        {/* Cenários de uso prontos */}
        <section id="cenarios" className="lp-section">
          <div className="lp-container">
            <header className="lp-section-head">
              <span className="lp-section-kicker">Teste sem tela vazia</span>
              <h2>Escolha um momento do semestre para ver como funciona.</h2>
              <p>
                Cada botão abre o sistema já preenchido com dados de exemplo, para você explorar tudo na prática.
              </p>
            </header>

            <div className="lp-scenarios-grid">
              {scenarios.map((sc) => (
                <article key={sc.id} className="lp-scenario-card">
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                    <ToneBadge tone="brand">{sc.badge}</ToneBadge>
                    <span className="pt-mono pt-muted" style={{ fontSize: 12 }}>
                      {sc.padrinhos.length} padrinhos
                    </span>
                  </div>
                  <h3>{sc.titulo}</h3>
                  <p>{sc.resumo}</p>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", paddingTop: 4 }}>
                    <button
                      type="button"
                      className="pt-btn pt-btn-primary lp-pill-btn"
                      onClick={() => abrirCenario(sc.id, "/dashboard")}
                    >
                      <Play size={14} /> Abrir este cenário
                    </button>
                    <button
                      type="button"
                      className="pt-btn pt-btn-ghost lp-pill-btn"
                      onClick={() =>
                        abrirCenario(
                          sc.id,
                          sc.id === "inicio" ? "/match" : sc.id === "fechamento" ? "/relatorio" : "/reunioes"
                        )
                      }
                    >
                      Ir direto
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Como o semestre funciona + Regras simples */}
        <section id="como-funciona" className="lp-section lp-section-white">
          <div className="lp-container">
            <header className="lp-section-head">
              <span className="lp-section-kicker">Do início ao fim</span>
              <h2>Quatro passos simples que o sistema acompanha com você.</h2>
              <p>Clique em qualquer etapa abaixo para abrir a tela dela no painel.</p>
            </header>

            <SemesterFlowDiagram
              padrinhosCount={scenario.padrinhos.length}
              matchesCount={scenario.matches.length}
              reunioesCount={scenario.reunioes.length}
              temasCount={scenario.temas.length}
              aptosCount={counts.aptos + counts.alertas}
            />

            <div className="lp-rules-grid">
              <div className="lp-rule-item">
                <CheckCircle2 size={20} color="var(--pt-green)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Quem participa recebe ACG sem erro</strong>
                  <p>Faltas justificadas não prejudicam o padrinho e a presença fica registrada reunião por reunião.</p>
                </div>
              </div>
              <div className="lp-rule-item">
                <BookOpen size={20} color="var(--pt-brand)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Falta ou atraso avisa antes de reprovar</strong>
                  <p>Quando alguém chega perto do limite, o sistema marca em alerta para a coordenação agir cedo.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Relatórios e Certificados reais */}
        <section id="documentos" className="lp-section">
          <div className="lp-container">
            <header className="lp-section-head">
              <span className="lp-section-kicker">Prontos para imprimir ou salvar em PDF</span>
              <h2>Veja como saem o relatório final e o certificado.</h2>
              <p>
                No fim do semestre, você gera a lista oficial de ACG, o resumo executivo e baixa todos os certificados de uma vez.
              </p>
            </header>

            <div className="pt-card pt-card-flat">
              <div className="lp-tabs-bar">
                <div className="lp-tab-group">
                  <button
                    type="button"
                    className={`lp-tab-btn ${docTab === "certificado" ? "is-active" : ""}`}
                    onClick={() => setDocTab("certificado")}
                  >
                    <Award size={15} /> Certificado
                  </button>
                  <button
                    type="button"
                    className={`lp-tab-btn ${docTab === "aptidao" ? "is-active" : ""}`}
                    onClick={() => setDocTab("aptidao")}
                  >
                    <FileCheck2 size={15} /> Relatório Aptidão ACG
                  </button>
                  <button
                    type="button"
                    className={`lp-tab-btn ${docTab === "resumo" ? "is-active" : ""}`}
                    onClick={() => setDocTab("resumo")}
                  >
                    <BarChart3 size={15} /> Resumo do Semestre
                  </button>
                </div>

                <a
                  href={docLinks[docTab]}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="pt-btn pt-btn-primary lp-pill-btn"
                >
                  Abrir em tela cheia <ExternalLink size={14} />
                </a>
              </div>

              <div className="pt-card-body" style={{ background: "var(--pt-bg)" }}>
                {docTab === "certificado" && (
                  <div className="lp-cert-sheet">
                    <div className="lp-cert-band top" />
                    <div className="lp-cert-band bottom" />
                    <div
                      style={{
                        fontSize: 11.5,
                        fontWeight: 800,
                        letterSpacing: "0.24em",
                        textTransform: "uppercase",
                        color: "var(--pt-brand)",
                      }}
                    >
                      Certificado de Participação
                    </div>
                    <p style={{ margin: "6px 0 0", fontSize: 13.5, color: "var(--pt-muted)" }}>
                      Este certificado é concedido a
                    </p>
                    <div style={{ marginTop: 10, fontFamily: "Georgia, serif", fontSize: 36, fontWeight: 600 }}>
                      Alice Mendonça
                    </div>
                    <div style={{ margin: "12px 0 16px" }}>
                      <ToneBadge tone="brand">Madrinha · 04 horas ACG</ToneBadge>
                    </div>
                    <p style={{ maxWidth: 620, margin: "0 auto", fontSize: 14.5, color: "var(--pt-text)", lineHeight: 1.7 }}>
                      em reconhecimento à sua participação como <strong>Madrinha</strong> no{" "}
                      <strong>Projeto de Apadrinhamento de Calouros</strong> ({scenario.config.semestre}), Departamento de
                      Engenharia de Software da <strong>PUC Minas</strong>.
                    </p>
                  </div>
                )}

                {docTab === "aptidao" && (
                  <div className="pt-card pt-card-flat" style={{ maxWidth: 840, margin: "0 auto" }}>
                    <div className="pt-card-header" style={{ background: "var(--pt-brand-gradient)", color: "#fff" }}>
                      <strong>Aptidão ACG — {scenario.config.semestre}</strong>
                      <span className="pt-mono" style={{ fontSize: 12 }}>RELATÓRIO-001</span>
                    </div>
                    <div className="pt-table-wrap">
                      <table className="pt-table pt-table-compact">
                        <thead>
                          <tr>
                            <th>Nome</th>
                            <th>Matrícula</th>
                            <th>Turno</th>
                            <th>Situação</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td style={{ fontWeight: 600 }}>Alice Mendonça</td>
                            <td className="pt-mono">100001</td>
                            <td>Manhã</td>
                            <td><ToneBadge tone="green">Apto (04h)</ToneBadge></td>
                          </tr>
                          <tr>
                            <td style={{ fontWeight: 600 }}>Camila Rezende</td>
                            <td className="pt-mono">100003</td>
                            <td>Manhã</td>
                            <td><ToneBadge tone="amber">Apto c/ alerta</ToneBadge></td>
                          </tr>
                          <tr>
                            <td style={{ fontWeight: 600 }}>João Vasconcelos</td>
                            <td className="pt-mono">100010</td>
                            <td>Noite</td>
                            <td><ToneBadge tone="red">Reportado</ToneBadge></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {docTab === "resumo" && (
                  <div className="pt-card pt-card-flat" style={{ maxWidth: 840, margin: "0 auto" }}>
                    <div className="pt-card-header" style={{ background: "var(--pt-brand-gradient)", color: "#fff" }}>
                      <strong>Resumo do Semestre — {scenario.config.semestre}</strong>
                      <span className="pt-mono" style={{ fontSize: 12 }}>3 PÁGINAS A4</span>
                    </div>
                    <div className="pt-table-wrap">
                      <table className="pt-table pt-table-compact">
                        <thead>
                          <tr>
                            <th>Indicador</th>
                            <th>Resultado</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr><td>Padrinhos participantes</td><td className="pt-mono">10</td></tr>
                          <tr><td>Calouros acompanhados</td><td className="pt-mono">20</td></tr>
                          <tr><td>Reuniões realizadas</td><td className="pt-mono">3</td></tr>
                          <tr><td>Taxa de aptidão ACG</td><td><ToneBadge tone="green">80% aptos</ToneBadge></td></tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* CTA final */}
        <section className="lp-section" style={{ paddingTop: 12 }}>
          <div className="lp-container">
            <div className="lp-cta">
              <h2>Quer ver o sistema funcionando por dentro?</h2>
              <p>
                Abra o painel com um clique e navegue pelos cenários prontos de início, andamento e fechamento de semestre.
              </p>
              <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="pt-btn pt-btn-ghost lp-btn-hero"
                  onClick={() => abrirCenario("fechamento", "/dashboard")}
                >
                  Abrir painel agora <ArrowRight size={17} />
                </button>
                <a
                  className="pt-btn pt-btn-soft lp-btn-hero"
                  href={docLinks.certificado}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Ver certificado A4 <ExternalLink size={16} />
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="lp-footer">
        <div className="lp-footer-inner">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <img src={`${base}brand/padrinho-track-mark.svg`} alt="" style={{ width: 24, height: 24 }} />
            <span>Padrinho Track · Engenharia de Software, PUC Minas</span>
          </div>
          <div className="lp-footer-links">
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer">Repositório</a>
            <a href={`${REPO_URL}/blob/main/docs/arquitetura.md`} target="_blank" rel="noopener noreferrer">Arquitetura</a>
            <a href={docLinks.aptidao} target="_blank" rel="noopener noreferrer">Relatório ACG</a>
            <a href={docLinks.certificado} target="_blank" rel="noopener noreferrer">Certificado</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
