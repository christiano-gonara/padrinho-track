import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CalendarDays, Link2, Shuffle, UserCheck, Users } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";

export function InicioSemestrePage() {
  const { scenario, runMatchDemo, notify } = useApp();
  const navigate = useNavigate();
  const [urlPad, setUrlPad] = useState("");
  const [urlCal, setUrlCal] = useState("");

  return (
    <AppShell title="Início do Semestre">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Início do Semestre</h1>
          <p className="pt-page-subtitle">Importe padrinhos, calouros e gere os matches para o semestre</p>
        </div>
      </div>

      <div style={{ maxWidth: 760, margin: "0 auto" }} className="pt-stack">
        <div className="pt-alert pt-alert-info">
          <CalendarDays size={16} />
          <span>
            Siga as etapas em ordem: importe os padrinhos, depois os calouros, e por fim execute o algoritmo de match.
          </span>
        </div>

        <div className="pt-card pt-card-flat">
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><UserCheck size={16} /></div>
              <h2 className="pt-card-title">1. Importar Padrinhos</h2>
            </div>
            <ToneBadge tone="green">{scenario.padrinhos.length} cadastrados</ToneBadge>
          </div>
          <div className="pt-card-body pt-stack">
            <div className="pt-field">
              <label className="pt-label">Link da planilha Google Sheets (Padrinhos)</label>
              <input
                className="pt-input"
                placeholder="https://docs.google.com/spreadsheets/d/..."
                value={urlPad}
                onChange={(e) => setUrlPad(e.target.value)}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="pt-btn pt-btn-primary"
                onClick={() => notify("Padrinhos validados e sincronizados no cenário.", "success")}
              >
                Importar padrinhos
              </button>
            </div>
          </div>
        </div>

        <div className="pt-card pt-card-flat">
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><Users size={16} /></div>
              <h2 className="pt-card-title">2. Importar Calouros</h2>
            </div>
            <ToneBadge tone="green">{scenario.calourosSoltos.length} cadastrados</ToneBadge>
          </div>
          <div className="pt-card-body pt-stack">
            <div className="pt-field">
              <label className="pt-label">Link da planilha Google Sheets (Calouros)</label>
              <input
                className="pt-input"
                placeholder="https://docs.google.com/spreadsheets/d/..."
                value={urlCal}
                onChange={(e) => setUrlCal(e.target.value)}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="pt-btn pt-btn-primary"
                onClick={() => notify("Calouros validados e sincronizados no cenário.", "success")}
              >
                Importar calouros
              </button>
            </div>
          </div>
        </div>

        <div className="pt-card pt-card-flat">
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><Link2 size={16} /></div>
              <h2 className="pt-card-title">3. Gerar Match</h2>
            </div>
          </div>
          <div className="pt-card-body pt-stack">
            <p className="pt-muted" style={{ margin: 0, fontSize: 13.5 }}>
              <strong>{scenario.padrinhos.length}</strong> padrinhos e{" "}
              <strong>{scenario.calourosSoltos.length}</strong> calouros disponíveis para cruzamento automático.
            </p>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="pt-btn pt-btn-primary"
                onClick={() => {
                  runMatchDemo();
                  navigate("/match");
                }}
              >
                <Shuffle size={15} /> Gerar matches automaticamente
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
