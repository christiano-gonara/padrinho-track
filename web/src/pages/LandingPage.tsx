import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Award,
  BarChart3,
  ExternalLink,
  FileCheck2,
  Github,
  Layers,
  LogIn,
  Play,
} from "lucide-react";
import { SemesterFlowDiagram } from "../components/charts/SemesterFlowDiagram";
import { StatusBarChart } from "../components/charts/StatusBarChart";
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

  const counts = {
    aptos: scenario.padrinhos.filter((p) => p.status === "apto").length,
    alertas: scenario.padrinhos.filter((p) => p.status === "alerta").length,
    reprovados: scenario.padrinhos.filter((p) => p.status === "inapto_amarelo").length,
    reportados: scenario.padrinhos.filter((p) => p.status === "inapto_vermelho").length,
  };

  const docLinks = {
    certificado: `${base}exemplos/certificado.html`,
    aptidao: `${base}exemplos/relatorio-aptidao.html`,
    resumo: `${base}exemplos/resumo-semestre.html`,
  };

  return (
    <div className="lp-wrap">
      {/* Barra superior informativa */}
      <div className="lp-notice">
        <div className="lp-notice-inner">
          <span className="lp-notice-badge">
            <Layers size={12} /> Demo interativa + Exemplos reais
          </span>
          <span>
            Explore todas as telas em React + TypeScript com cenários prontos ou abra os relatórios e certificados em A4.
          </span>
          <div className="lp-notice-links">
            <a href={docLinks.aptidao} target="_blank" rel="noopener noreferrer">
              Relatório ACG <ExternalLink size={12} />
            </a>
            <a href={docLinks.certificado} target="_blank" rel="noopener noreferrer">
              Certificado <ExternalLink size={12} />
            </a>
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
              GitHub <Github size={12} />
            </a>
          </div>
        </div>
      </div>

      {/* Header */}
      <header className="lp-header">
        <div className="lp-header-inner">
          <a href="#topo">
            <img className="lp-logo" src={`${base}brand/padrinho-track-lockup.svg`} alt="Padrinho Track" />
          </a>
          <nav className="lp-nav" aria-label="Navegação da apresentação">
            <a href="#cenarios">Cenários de uso</a>
            <a href="#fluxo">Fluxo &amp; Regras</a>
            <a href="#documentos">Relatórios &amp; Certificados</a>
          </nav>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" className="pt-btn pt-btn-soft pt-btn-sm" onClick={() => navigate("/dashboard")}>
              <Play size={13} /> Abrir painel
            </button>
            <button type="button" className="pt-btn pt-btn-primary pt-btn-sm" onClick={() => navigate("/login")}>
              <LogIn size={13} /> Entrar
            </button>
          </div>
        </div>
      </header>

      <main id="topo">
        {/* Hero */}
        <section className="lp-hero-band">
          <div className="lp-hero">
            <div>
              <p className="lp-eyebrow">
                <span className="lp-dot" /> Engenharia de Software · PUC Minas
              </p>
              <h1>
                Apadrinhamento de calouros, <span className="lp-highlight">do match ao certificado</span>.
              </h1>
              <p className="lp-lede">
                Centralize padrinhos, calouros, reuniões, presenças, entregas de temas, advertências e a emissão de
                relatórios de ACG e certificados em PDF — em tema claro, com gráficos de barras e cenários de uso prontos para testar.
              </p>
              <div className="lp-hero-actions">
                <button
                  type="button"
                  className="pt-btn pt-btn-primary pt-btn-lg"
                  onClick={() => abrirCenario("fechamento", "/dashboard")}
                >
                  Explorar telas com dados <ArrowRight size={16} />
                </button>
                <a className="pt-btn pt-btn-ghost pt-btn-lg" href="#documentos">
                  Ver relatórios e certificados
                </a>
              </div>
            </div>

            {/* Card resumo no Hero com gráfico em barras (sem pizza/rosca) */}
            <div className="lp-mockup">
              <div className="lp-mockup-bar">
                <span className="lp-mockup-dots">
                  <i />
                  <i />
                  <i />
                </span>
                <span className="pt-mono" style={{ fontSize: 11.5, color: "var(--pt-muted)" }}>
                  {scenario.titulo}
                </span>
                <ToneBadge tone="brand">{scenario.config.semestre}</ToneBadge>
              </div>
              <div className="lp-mockup-body">
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <strong style={{ fontSize: 14, color: "var(--pt-ink)" }}>Distribuição ACG (barras)</strong>
                  <span className="pt-muted" style={{ fontSize: 12 }}>
                    {scenario.padrinhos.length} padrinhos
                  </span>
                </div>
                <StatusBarChart counts={counts} />
              </div>
            </div>
          </div>
        </section>

        {/* Cenários de Uso clicáveis */}
        <section id="cenarios" className="lp-section">
          <div className="lp-container">
            <header className="lp-section-head">
              <p className="lp-eyebrow">Cenários de Uso</p>
              <h2>Teste as telas sem aparecer tudo vazio.</h2>
              <p>
                Escolha um momento real do semestre para carregar dados completos de demonstração no painel React + TypeScript.
              </p>
            </header>

            <div className="lp-scenarios-grid">
              {scenarios.map((sc) => (
                <article key={sc.id} className="lp-scenario-card">
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                    <ToneBadge tone="brand">{sc.badge}</ToneBadge>
                    <span className="pt-mono pt-muted" style={{ fontSize: 11.5 }}>
                      {sc.padrinhos.length} padrinhos
                    </span>
                  </div>
                  <h3>{sc.titulo}</h3>
                  <p>{sc.resumo}</p>
                  <div className="lp-scenario-metrics">
                    <span>{sc.matches.length} grupos match</span>
                    <span>·</span>
                    <span>{sc.reunioes.length} reuniões</span>
                    <span>·</span>
                    <span>{sc.temas.length} temas</span>
                  </div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", paddingTop: 6 }}>
                    <button
                      type="button"
                      className="pt-btn pt-btn-primary pt-btn-sm"
                      onClick={() => abrirCenario(sc.id, "/dashboard")}
                    >
                      <Play size={13} /> Ver cenário no painel
                    </button>
                    <button
                      type="button"
                      className="pt-btn pt-btn-ghost pt-btn-sm"
                      onClick={() =>
                        abrirCenario(sc.id, sc.id === "inicio" ? "/match" : sc.id === "fechamento" ? "/relatorio" : "/reunioes")
                      }
                    >
                      Tela principal
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Diagrama de Fluxo */}
        <section id="fluxo" className="lp-section lp-section-white">
          <div className="lp-container">
            <header className="lp-section-head">
              <p className="lp-eyebrow">Diagrama do Ciclo Semestral</p>
              <h2>Quatro etapas conectadas às regras de ACG.</h2>
              <p>Clique em qualquer etapa do diagrama para abrir diretamente a tela correspondente no cenário atual.</p>
            </header>

            <SemesterFlowDiagram
              padrinhosCount={scenario.padrinhos.length}
              matchesCount={scenario.matches.length}
              reunioesCount={scenario.reunioes.length}
              temasCount={scenario.temas.length}
              aptosCount={counts.aptos + counts.alertas}
            />
          </div>
        </section>

        {/* Relatórios & Certificados */}
        <section id="documentos" className="lp-section">
          <div className="lp-container">
            <header className="lp-section-head">
              <p className="lp-eyebrow">Relatórios e Certificados no GitHub Pages</p>
              <h2>Documentos reais prontos para impressão e PDF.</h2>
              <p>
                Visualize as prévias abaixo ou abra os documentos completos gerados a partir dos templates oficiais do sistema.
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
                  className="pt-btn pt-btn-primary pt-btn-sm"
                >
                  Abrir documento completo <ExternalLink size={13} />
                </a>
              </div>

              <div className="pt-card-body" style={{ background: "var(--pt-bg)" }}>
                {docTab === "certificado" && (
                  <div className="lp-cert-sheet">
                    <div className="lp-cert-band top" />
                    <div className="lp-cert-band bottom" />
                    <div
                      style={{
                        fontSize: 11,
                        fontWeight: 800,
                        letterSpacing: "0.24em",
                        textTransform: "uppercase",
                        color: "var(--pt-brand)",
                      }}
                    >
                      Certificado de Participação
                    </div>
                    <p style={{ margin: "6px 0 0", fontSize: 12.5, color: "var(--pt-muted)" }}>
                      Este certificado é concedido a
                    </p>
                    <div style={{ marginTop: 10, fontFamily: "Georgia, serif", fontSize: 34, fontWeight: 600 }}>
                      Alice Mendonça
                    </div>
                    <div style={{ margin: "12px 0 16px" }}>
                      <ToneBadge tone="brand">Madrinha · 04 horas ACG</ToneBadge>
                    </div>
                    <p style={{ maxWidth: 600, margin: "0 auto", fontSize: 13.5, color: "var(--pt-text)", lineHeight: 1.7 }}>
                      em reconhecimento à sua valiosa participação no <strong>Projeto de Apadrinhamento de Calouros</strong>{" "}
                      ({scenario.config.semestre}), Departamento de Engenharia de Software da <strong>PUC Minas</strong>.
                    </p>
                  </div>
                )}

                {docTab === "aptidao" && (
                  <div className="pt-card pt-card-flat" style={{ maxWidth: 840, margin: "0 auto" }}>
                    <div className="pt-card-header" style={{ background: "var(--pt-brand-gradient)", color: "#fff" }}>
                      <strong>Aptidão ACG — {scenario.config.semestre}</strong>
                      <span className="pt-mono" style={{ fontSize: 11.5 }}>RELATÓRIO-001</span>
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
                      <span className="pt-mono" style={{ fontSize: 11.5 }}>3 PÁGINAS A4</span>
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
              <h2>Pronto para explorar cada tela em funcionamento?</h2>
              <p>
                Navegue pelo Dashboard, Padrinhos, Match, Reuniões, Temas, Advertências e Relatórios com os cenários interativos.
              </p>
              <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="pt-btn pt-btn-ghost pt-btn-lg"
                  onClick={() => abrirCenario("fechamento", "/dashboard")}
                >
                  Abrir Dashboard <ArrowRight size={16} />
                </button>
                <a
                  className="pt-btn pt-btn-soft pt-btn-lg"
                  href={docLinks.certificado}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Abrir Certificado A4 <ExternalLink size={15} />
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
            <a href={docLinks.aptidao} target="_blank" rel="noopener noreferrer">Exemplo Relatório ACG</a>
            <a href={docLinks.certificado} target="_blank" rel="noopener noreferrer">Exemplo Certificado</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
