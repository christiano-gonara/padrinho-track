import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, Copy, Link2, RefreshCw, Upload } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { useApp } from "../context/AppContext";
import "../styles/pages/InicioSemestre.css";

const EMAIL_COMPARTILHAR = "padrinho-track@padrinho-track.iam.gserviceaccount.com";

export function InicioSemestrePage() {
  const { scenario, runMatchDemo, notify } = useApp();
  const navigate = useNavigate();
  const [urlPad, setUrlPad] = useState("");
  const [urlCal, setUrlCal] = useState("");

  const nPad = scenario.padrinhos.length;
  const nCal = scenario.calourosSoltos.length;
  const temDuplas = scenario.matches.some((g) => g.calouros.length > 0);

  function copiarEmail() {
    navigator.clipboard?.writeText(EMAIL_COMPARTILHAR).then(
      () => notify("E-mail copiado.", "success"),
      () => notify("Não deu pra copiar. Selecione o texto e copie.", "error")
    );
  }

  const passos = [
    {
      n: 1,
      titulo: "Trazer os padrinhos",
      texto: "Cole o link da planilha com as respostas do formulário de inscrição dos padrinhos.",
      label: "Link da planilha dos padrinhos",
      id: "url-padrinhos",
      valor: urlPad,
      setValor: setUrlPad,
      feito: nPad > 0,
      feitoTexto: `${nPad} padrinhos importados`,
      acao: () => notify("Padrinhos importados.", "success"),
    },
    {
      n: 2,
      titulo: "Trazer os calouros",
      texto: "Agora a planilha com as respostas dos calouros.",
      label: "Link da planilha dos calouros",
      id: "url-calouros",
      valor: urlCal,
      setValor: setUrlCal,
      feito: nCal > 0,
      feitoTexto: `${nCal} calouros importados`,
      acao: () => notify("Calouros importados.", "success"),
    },
  ];

  return (
    <AppShell title="Começar o semestre">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Começar o semestre</h1>
          <p className="pt-page-subtitle">Três passos pra deixar tudo pronto antes da primeira reunião.</p>
        </div>
      </div>

      <div className="pt-split">
        <div className="pt-stack" style={{ gap: 16 }}>
          {passos.map((p) => (
            <section key={p.n} className="pt-card pt-passo">
              <span className={`pt-passo-num ${p.feito ? "is-feito" : ""}`}>
                {p.feito ? <Check size={20} strokeWidth={2.8} /> : p.n}
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h2>{p.titulo}</h2>
                <p>{p.texto}</p>
                <label className="pt-label" htmlFor={p.id}>{p.label}</label>
                <div className="pt-passo-linha">
                  <input
                    id={p.id}
                    type="url"
                    className="pt-input"
                    placeholder="https://docs.google.com/spreadsheets/d/..."
                    value={p.valor}
                    onChange={(e) => p.setValor(e.target.value)}
                  />
                  <button type="button" className={`pt-btn ${p.feito ? "pt-btn-ghost" : "pt-btn-primary"}`} onClick={p.acao}>
                    {p.feito ? <RefreshCw size={17} /> : <Upload size={17} />}
                    {p.feito ? "Importar de novo" : "Importar"}
                  </button>
                </div>
                {p.feito && (
                  <div className="pt-passo-ok">
                    <Check size={16} strokeWidth={2.6} /> {p.feitoTexto}
                  </div>
                )}
              </div>
            </section>
          ))}

          <section className="pt-card pt-passo">
            <span className={`pt-passo-num ${temDuplas ? "is-feito" : ""}`}>
              {temDuplas ? <Check size={20} strokeWidth={2.8} /> : 3}
            </span>
            <div style={{ flex: 1 }}>
              <h2>Formar as duplas</h2>
              <p>
                O sistema junta cada calouro com um padrinho do mesmo turno, olhando também o perfil de cada um. Você pode
                ajustar depois.
              </p>
              <button
                type="button"
                className="pt-btn pt-btn-primary"
                onClick={() => {
                  runMatchDemo();
                  navigate("/match");
                }}
              >
                <Link2 size={17} /> {temDuplas ? "Refazer duplas" : "Formar duplas agora"}
              </button>
            </div>
          </section>
        </div>

        <section className="pt-card" style={{ alignSelf: "start" }}>
          <h2 className="pt-card-title">Antes de importar</h2>
          <ul className="pt-dicas">
            <li>
              A planilha precisa estar compartilhada com <strong>{EMAIL_COMPARTILHAR}</strong> como leitor.
            </li>
            <li>Importar de novo não duplica ninguém: quem já está no sistema é atualizado.</li>
            <li>Errou alguma coisa? Dá pra editar cada pessoa depois, na tela de Padrinhos.</li>
          </ul>
          <button type="button" className="pt-btn pt-btn-ghost" onClick={copiarEmail}>
            <Copy size={17} /> Copiar e-mail de compartilhamento
          </button>
        </section>
      </div>
    </AppShell>
  );
}
