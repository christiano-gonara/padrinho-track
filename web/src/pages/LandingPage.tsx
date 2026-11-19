import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Check, ExternalLink, X } from "lucide-react";
import { useApp } from "../context/AppContext";
import { ScenarioId } from "../types/domain";
import "../styles/pages/LandingPage.css";

const REPO_URL = "https://github.com/christiano-gonara/padrinho-track";
const LACO = "M10 22 C5 22, 5 12, 10 12 C14 12, 16 20, 22 20 C27 20, 27 10, 22 10 C18 10, 16 18, 10 18";

const PARADAS: { id: ScenarioId; n: number; titulo: string; quando: string; texto: string }[] = [
  {
    id: "inicio",
    n: 1,
    titulo: "Começo",
    quando: "antes das duplas",
    texto: "Inscrições recém-chegadas do formulário, prontas pra formar as duplas de padrinho e calouro.",
  },
  {
    id: "andamento",
    n: 2,
    titulo: "Meio",
    quando: "reuniões rolando",
    texto: "Duplas formadas, 2 reuniões feitas e os primeiros cartões amarelos aparecendo no painel.",
  },
  {
    id: "fechamento",
    n: 3,
    titulo: "Fechamento",
    quando: "hora do certificado",
    texto: "As 3 reuniões encerradas, a lista de ACG calculada e os certificados prontos pra baixar.",
  },
];

const DOCS = [
  { id: "cert" as const, titulo: "Certificado A4", dica: "um por pessoa" },
  { id: "lista" as const, titulo: "Lista de ACG", dica: "pra secretaria" },
  { id: "resumo" as const, titulo: "Resumo do semestre", dica: "pro professor" },
];

const FAIXA = ["duplas pelo turno", "presença sem conta na mão", "cartão amarelo avisa antes", "certificado em PDF", "sem planilha solta"];

function Laco({ size, color, width = 3, className }: { size: number; color: string; width?: number; className?: string }) {
  return (
    <svg className={className} width={size} height={size} viewBox="2 2 28 28" fill="none" aria-hidden="true">
      <path d={LACO} stroke={color} strokeWidth={width} strokeLinecap="round" />
    </svg>
  );
}

export function LandingPage() {
  const { setScenarioId } = useApp();
  const navigate = useNavigate();
  const [parada, setParada] = useState<ScenarioId>("andamento");
  const [doc, setDoc] = useState<"cert" | "lista" | "resumo">("cert");
  const base = import.meta.env.BASE_URL;

  const docLinks = {
    cert: `${base}exemplos/certificado.html`,
    lista: `${base}exemplos/relatorio-aptidao.html`,
    resumo: `${base}exemplos/resumo-semestre.html`,
  };

  function abrirPainel(id: ScenarioId = parada) {
    setScenarioId(id);
    navigate("/dashboard");
  }

  const paradaAtual = PARADAS.find((p) => p.id === parada) ?? PARADAS[1];

  return (
    <div className="lp">
      {/* Menu do topo */}
      <header className="lp-nav">
        <div className="lp-wrap lp-nav-in">
          <a href="#topo" className="lp-logo" aria-label="Padrinho Track, voltar ao topo">
            <span className="lp-logo-tile">
              <Laco size={26} color="#ffffff" width={3.2} />
            </span>
            <span className="lp-disp">
              padrinho<span>track</span>
            </span>
          </a>
          <nav className="lp-links" aria-label="Seções">
            <a href="#tirinha">Como funciona</a>
            <a href="#regras">Regras</a>
            <a href="#testar">Testar</a>
            <a href="#documentos">Certificado</a>
          </nav>
          <div className="lp-nav-acoes">
            <Link to="/login" className="lp-btn lp-btn-white lp-btn-sm lp-hide-sm">
              Entrar
            </Link>
            <a href="#testar" className="lp-btn lp-btn-blue lp-btn-sm">
              Abrir painel
            </a>
          </div>
        </div>
      </header>

      <main id="topo">
        {/* Abertura */}
        <section className="lp-hero">
          <div className="lp-wrap lp-hero-grid">
            <div>
              <p className="lp-hand lp-hero-oi">ei, coordenação!</p>
              <h1 className="lp-disp lp-hero-titulo">
                Todo calouro merece um{" "}
                <span className="lp-grifo">
                  padrinho
                  <svg viewBox="0 0 300 24" preserveAspectRatio="none" aria-hidden="true">
                    <path d="M4 16 C 60 4, 120 22, 180 10 S 270 6, 296 14" stroke="#fbbf24" strokeWidth="9" strokeLinecap="round" fill="none" />
                  </svg>
                </span>
                .
              </h1>
              <p className="lp-hero-texto">
                E toda coordenação merece não ter que fazer isso numa planilha. O Padrinho Track forma as duplas, conta as
                presenças e entrega os certificados de ACG pra você.
              </p>
              <div className="lp-hero-acoes">
                <a href="#testar" className="lp-btn lp-btn-blue">
                  Testar agora, sem cadastro <ArrowRight size={20} />
                </a>
                <a href="#tirinha" className="lp-btn lp-btn-white">
                  Ver como funciona
                </a>
              </div>
            </div>

            {/* Ilustração: o laço da marca ligando padrinho e calouro */}
            <div className="lp-arte" aria-hidden="true">
              <svg className="lp-arte-svg" viewBox="0 0 520 470">
                <path d="M150 330 C 40 330, 40 140, 150 140 C 240 140, 270 300, 370 300 C 480 300, 480 110, 370 110 C 280 110, 250 270, 150 270" stroke="#bfdbfe" strokeWidth="24" strokeLinecap="round" fill="none" />
                <path d="M150 330 C 40 330, 40 140, 150 140 C 240 140, 270 300, 370 300 C 480 300, 480 110, 370 110 C 280 110, 250 270, 150 270" stroke="#1d4ed8" strokeWidth="13" strokeLinecap="round" fill="none" />
                <g transform="translate(100 205)">
                  <circle r="58" fill="#60a5fa" stroke="#1e3a8a" strokeWidth="3" />
                  <circle cx="-20" cy="-6" r="14" fill="#ffffff" stroke="#1e3a8a" strokeWidth="3" />
                  <circle cx="20" cy="-6" r="14" fill="#ffffff" stroke="#1e3a8a" strokeWidth="3" />
                  <line x1="-6" y1="-6" x2="6" y2="-6" stroke="#1e3a8a" strokeWidth="3" />
                  <circle cx="-18" cy="-4" r="5" fill="#0f172a" />
                  <circle cx="22" cy="-4" r="5" fill="#0f172a" />
                  <path d="M-18 22 Q 0 38, 18 22" stroke="#1e3a8a" strokeWidth="3" strokeLinecap="round" fill="none" />
                </g>
                <g transform="translate(420 200)">
                  <circle r="52" fill="#fbbf24" stroke="#1e3a8a" strokeWidth="3" />
                  <path d="M-50 -14 C -48 -60, 48 -60, 50 -14 Z" fill="#ef4444" stroke="#1e3a8a" strokeWidth="3" strokeLinejoin="round" />
                  <circle cy="-58" r="9" fill="#ffffff" stroke="#1e3a8a" strokeWidth="3" />
                  <circle cx="-16" cy="6" r="6" fill="#0f172a" />
                  <circle cx="16" cy="6" r="6" fill="#0f172a" />
                  <ellipse cy="28" rx="9" ry="7" fill="#0f172a" />
                  <circle cx="-30" cy="20" r="7" fill="#f97316" opacity="0.55" />
                  <circle cx="30" cy="20" r="7" fill="#f97316" opacity="0.55" />
                </g>
              </svg>
              <div className="lp-balao lp-hand lp-balao-1">bem-vindo à PUC!</div>
              <div className="lp-balao lp-hand lp-balao-2">onde fica o prédio 34?</div>
              <div className="lp-adesivo lp-adesivo-1">
                <span className="lp-adesivo-ok">
                  <Check size={18} strokeWidth={3} color="#ffffff" />
                </span>
                <span>
                  <strong>3 de 3 reuniões</strong>
                  <small>presença em dia</small>
                </span>
              </div>
              <div className="lp-adesivo lp-adesivo-2">
                <strong className="lp-disp">4h</strong>
                <small>de ACG no certificado</small>
              </div>
            </div>
          </div>
        </section>

        {/* Faixa que corre */}
        <div className="lp-faixa" aria-hidden="true">
          <div className="lp-faixa-trilho lp-disp">
            {[0, 1].map((k) =>
              FAIXA.map((t) => (
                <span key={`${k}-${t}`}>
                  {t}
                  <i>✦</i>
                </span>
              ))
            )}
          </div>
        </div>

        {/* O semestre em 4 quadrinhos */}
        <section id="tirinha" className="lp-sec">
          <div className="lp-wrap">
            <div className="lp-sec-head">
              <h2 className="lp-disp lp-h2" style={{ maxWidth: "16ch" }}>O semestre inteiro em 4 quadrinhos.</h2>
              <p className="lp-hand lp-nota">(spoiler: termina com certificado)</p>
            </div>
            <ol className="lp-tirinha">
              <li className="lp-quadro">
                <div className="lp-quadro-top">
                  <span className="lp-disp">1</span>
                  <span className="lp-hand">março</span>
                </div>
                <div className="lp-quadro-arte" style={{ background: "#dbeafe", flexDirection: "column", gap: 8, padding: 14 }} aria-hidden="true">
                  <div className="lp-mini-arquivo"><i />inscrições.xlsx</div>
                  <div className="lp-mini-seta">↓</div>
                  <div className="lp-mini-total">10 padrinhos · 16 calouros</div>
                </div>
                <h3 className="lp-disp">Chegam as inscrições</h3>
                <p>Cole o link do Google Forms e todo mundo entra de uma vez.</p>
              </li>
              <li className="lp-quadro">
                <div className="lp-quadro-top">
                  <span className="lp-disp">2</span>
                  <span className="lp-hand">no mesmo dia</span>
                </div>
                <div className="lp-quadro-arte" style={{ background: "#fef3c7" }} aria-hidden="true">
                  <span className="lp-mini-av is-padrinho">AM</span>
                  <span className="lp-mini-fio" style={{ width: 40 }} />
                  <span className="lp-mini-av">LP</span>
                  <span className="lp-mini-fio" style={{ width: 14 }} />
                  <span className="lp-mini-av">FA</span>
                </div>
                <h3 className="lp-disp">Formam-se as duplas</h3>
                <p>Cada calouro ganha um padrinho do mesmo turno, com perfil parecido.</p>
              </li>
              <li className="lp-quadro">
                <div className="lp-quadro-top">
                  <span className="lp-disp">3</span>
                  <span className="lp-hand">abril a junho</span>
                </div>
                <div className="lp-quadro-arte" style={{ background: "#dcfce7", alignItems: "flex-end", gap: 14, padding: 14 }} aria-hidden="true">
                  <span className="lp-mini-barra" style={{ height: 100 }} />
                  <span className="lp-mini-barra" style={{ height: 82 }} />
                  <span className="lp-mini-barra" style={{ height: 100 }} />
                  <span className="lp-mini-cartao" />
                </div>
                <h3 className="lp-disp">Rolam as reuniões</h3>
                <p>Você marca a presença. Faltou sem justificar? Cartão amarelo, sozinho.</p>
              </li>
              <li className="lp-quadro is-azul">
                <div className="lp-quadro-top">
                  <span className="lp-disp">4</span>
                  <span className="lp-hand">julho</span>
                </div>
                <div className="lp-quadro-arte" style={{ background: "#ffffff" }} aria-hidden="true">
                  <div className="lp-mini-cert">
                    <span>CERTIFICADO</span>
                    <i />
                    <b />
                  </div>
                </div>
                <h3 className="lp-disp">Sai o certificado</h3>
                <p>Lista de ACG e todos os certificados em PDF, com um clique.</p>
              </li>
            </ol>
          </div>
        </section>

        {/* As regras do jogo */}
        <section id="regras" className="lp-sec lp-regras">
          <div className="lp-wrap">
            <div style={{ maxWidth: 720, marginBottom: 52 }}>
              <p className="lp-hand lp-nota" style={{ color: "#fbbf24" }}>as regras do jogo</p>
              <h2 className="lp-disp lp-h2" style={{ color: "#ffffff" }}>Cada padrinho sabe o placar dele.</h2>
              <p className="lp-regras-txt">
                Falta sem justificar vale cartão amarelo. Três amarelos, fica sem ACG. Falta justificada não conta.
              </p>
            </div>
            <div className="lp-cartoes">
              <div className="lp-cartao">
                <div className="lp-cartao-arte" style={{ background: "#10b981", transform: "rotate(-6deg)" }}>
                  <Check size={56} strokeWidth={3} color="#ffffff" />
                </div>
                <h3 className="lp-disp">Apto</h3>
                <p>Foi às reuniões ou justificou as faltas. Leva as horas e o certificado.</p>
              </div>
              <div className="lp-cartao">
                <div className="lp-cartao-arte" style={{ background: "#fbbf24", transform: "rotate(4deg)" }}>
                  <span className="lp-disp" style={{ fontSize: 54, fontWeight: 800, color: "#0f172a" }}>2/3</span>
                </div>
                <h3 className="lp-disp">Atenção</h3>
                <p>Falta um cartão pro limite. A coordenação vê o aviso e chama pra conversar antes.</p>
              </div>
              <div className="lp-cartao">
                <div className="lp-cartao-arte" style={{ background: "#ef4444", transform: "rotate(-3deg)" }}>
                  <X size={56} strokeWidth={3} color="#ffffff" />
                </div>
                <h3 className="lp-disp">Sem ACG</h3>
                <p>Chegou a três amarelos ou levou um vermelho. Aí o caso vai pro professor.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Escolher onde testar */}
        <section id="testar" className="lp-sec">
          <div className="lp-wrap">
            <div style={{ textAlign: "center", maxWidth: 720, margin: "0 auto 48px" }}>
              <h2 className="lp-disp lp-h2">Entra em qualquer ponto do semestre.</h2>
              <p className="lp-sub">Sem cadastro, com dados de exemplo. Escolhe uma parada:</p>
            </div>
            <div className="lp-caixa">
              <div className="lp-trilho">
                <div className="lp-trilho-linha lp-hide-sm" aria-hidden="true" />
                <div className="lp-paradas" role="group" aria-label="Momento do semestre">
                  {PARADAS.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      className={`lp-parada ${parada === p.id ? "is-on" : ""}`}
                      aria-pressed={parada === p.id}
                      onClick={() => setParada(p.id)}
                    >
                      <span className="lp-parada-dot">{p.n}</span>
                      <span className="lp-disp lp-parada-nome">{p.titulo}</span>
                      <span className="lp-hand lp-parada-quando">{p.quando}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="lp-parada-info">
                <p>{paradaAtual.texto}</p>
                <button type="button" className="lp-btn lp-btn-blue" onClick={() => abrirPainel()}>
                  Abrir o painel <ArrowRight size={20} />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Documentos */}
        <section id="documentos" className="lp-sec" style={{ paddingTop: 40 }}>
          <div className="lp-wrap lp-docs">
            <div>
              <p className="lp-hand lp-nota">o final feliz</p>
              <h2 className="lp-disp lp-h2">Sai tudo pronto pra imprimir.</h2>
              <div className="lp-abas" role="tablist" aria-label="Documentos">
                {DOCS.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    role="tab"
                    aria-selected={doc === d.id}
                    className={`lp-aba ${doc === d.id ? "is-on" : ""}`}
                    onClick={() => setDoc(d.id)}
                  >
                    <span>{d.titulo}</span>
                    <small>{d.dica}</small>
                  </button>
                ))}
              </div>
              <a href={docLinks[doc]} target="_blank" rel="noopener noreferrer" className="lp-abrir-doc">
                Abrir o exemplo de verdade <ExternalLink size={16} />
              </a>
            </div>

            <div className="lp-doc-palco" role="tabpanel">
              {doc === "cert" && (
                <div className="lp-cert">
                  <div className="lp-cert-faixa is-top" />
                  <div className="lp-cert-faixa is-bottom" />
                  <div className="lp-cert-moldura" />
                  <div className="lp-cert-moldura is-dentro" />
                  <span className="lp-cert-canto is-tl" />
                  <span className="lp-cert-canto is-tr" />
                  <span className="lp-cert-canto is-bl" />
                  <span className="lp-cert-canto is-br" />
                  <Laco size={260} color="#1e40af" width={2.2} className="lp-cert-marca" />
                  <img className="lp-cert-logos" src={`${base}images/certificado_icones.png`} alt="Engenharia de Software, ICEI e PUC Minas" />
                  <div className="lp-cert-conteudo">
                    <div className="lp-cert-rotulo">CERTIFICADO DE PARTICIPAÇÃO</div>
                    <div className="lp-cert-de">Este certificado é de</div>
                    <div className="lp-cert-nome">Alice Mendonça</div>
                    <div className="lp-cert-funcao">
                      Madrinha <span>|</span> 04 horas de ACG
                    </div>
                    <div className="lp-cert-div" aria-hidden="true">
                      <i />
                      <b />
                      <i />
                    </div>
                    <p className="lp-cert-texto">
                      Pela participação como <strong>madrinha</strong> no <strong>Projeto de Apadrinhamento de Calouros</strong>{" "}
                      da <strong>Engenharia de Software da PUC Minas</strong>, no semestre <strong>2026/1</strong>.
                    </p>
                    <div className="lp-cert-pe">
                      <span className="lp-cert-emissao">
                        Emitido em 20/07/2026
                        <br />
                        Belo Horizonte · MG
                      </span>
                      <span className="lp-cert-selo" aria-hidden="true">
                        <span>
                          <span>
                            <Laco size={16} color="#ffffff" />
                          </span>
                        </span>
                      </span>
                      <span className="lp-cert-assina">
                        <i />
                        <strong>Prof. Laerte Xavier</strong>
                        <small>Coordenador do Programa</small>
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {doc === "lista" && (
                <div className="lp-folha">
                  <div className="lp-folha-topo lp-disp">Lista de ACG · 2026/1</div>
                  <div className="lp-folha-corpo">
                    {[
                      ["Alice Mendonça", "recebe 4h", true],
                      ["Camila Rezende", "recebe 4h", true],
                      ["Elisa Drummond", "sem ACG", false],
                      ["João Vasconcelos", "com o professor", false],
                    ].map(([nome, sit, ok]) => (
                      <div key={String(nome)} className="lp-folha-linha">
                        <strong>{nome}</strong>
                        <span className={ok ? "is-ok" : "is-nao"}>{sit}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {doc === "resumo" && (
                <div className="lp-folha" style={{ padding: 24, textAlign: "center" }}>
                  <div className="lp-disp" style={{ fontSize: 24, fontWeight: 800, color: "#0f172a" }}>Como foi o semestre</div>
                  <svg role="img" aria-label="80% receberam ACG" width="240" height="134" viewBox="0 0 200 112" style={{ marginTop: 10, maxWidth: "100%" }}>
                    <path d="M18 100 A82 82 0 0 1 182 100" fill="none" stroke="#e2e8f0" strokeWidth="20" strokeLinecap="round" />
                    <path d="M18 100 A82 82 0 0 1 182 100" fill="none" stroke="#10b981" strokeWidth="20" strokeLinecap="round" strokeDasharray="206 258" />
                    <text x="100" y="90" textAnchor="middle" fontFamily="Sora, Inter, sans-serif" fontSize="40" fontWeight="800" fill="#0f172a">80%</text>
                  </svg>
                  <div className="lp-resumo-nums">
                    <span><strong>10</strong> padrinhos</span>
                    <span><strong>16</strong> calouros</span>
                    <span><strong>3</strong> reuniões</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Chamada final */}
        <section className="lp-sec" style={{ paddingTop: 0 }}>
          <div className="lp-wrap">
            <div className="lp-cta">
              <div className="lp-cta-brilho" aria-hidden="true" />
              <Laco size={420} color="#ffffff" width={2.4} className="lp-cta-laco" />
              <h2 className="lp-disp">Bora deixar a planilha de lado?</h2>
              <p>Abre o painel com dados de exemplo e vê o semestre inteiro funcionando. Leva menos de um minuto.</p>
              <div className="lp-cta-acoes">
                <button type="button" className="lp-btn lp-btn-white" onClick={() => abrirPainel("fechamento")}>
                  Abrir o painel
                </button>
                <Link to="/criar-conta" className="lp-btn lp-btn-vazado">
                  Criar conta da coordenação
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="lp-rodape">
        <div className="lp-wrap lp-rodape-in">
          <div className="lp-rodape-marca">
            <Laco size={30} color="#60a5fa" />
            <span>
              <strong className="lp-disp">padrinhotrack</strong>
              <small>Mentoria Acadêmica · Engenharia de Software · PUC Minas</small>
            </span>
          </div>
          <nav aria-label="Links do rodapé">
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer">GitHub</a>
            <a href={`${REPO_URL}/blob/main/docs/arquitetura.md`} target="_blank" rel="noopener noreferrer">Arquitetura</a>
            <Link to="/login">Entrar</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
