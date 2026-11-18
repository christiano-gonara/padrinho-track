import { FormEvent, useEffect, useState } from "react";
import { Calendar, Download, Save, Settings, Trash2 } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { useApp } from "../context/AppContext";
import { apiFetch } from "../services/api";
import { ConfigSemestre } from "../types/domain";

export function ConfigPage() {
  const { mode, scenario, updateConfigDemo, clearLogsDemo, notify } = useApp();
  const [form, setForm] = useState<ConfigSemestre>(scenario.config);
  const [coordText, setCoordText] = useState(scenario.config.coordenadores.join("\n"));

  useEffect(() => {
    if (mode === "live") {
      apiFetch<{ config_semestre: ConfigSemestre }>("/api/config")
        .then((res) => {
          setForm(res.config_semestre);
          setCoordText((res.config_semestre.coordenadores || []).join("\n"));
        })
        .catch(() => {});
    } else {
      setForm(scenario.config);
      setCoordText(scenario.config.coordenadores.join("\n"));
    }
  }, [mode, scenario]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const payload: ConfigSemestre = {
      ...form,
      coordenadores: coordText
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
    };
    if (mode === "live") {
      await apiFetch("/api/config", { method: "POST", body: JSON.stringify(payload) });
      notify("Configurações salvas no servidor.", "success");
    } else {
      updateConfigDemo(payload);
    }
  }

  async function onClearLogs() {
    if (mode === "live") {
      await apiFetch("/api/logs", { method: "DELETE" });
      notify("Logs apagados.", "success");
    } else {
      clearLogsDemo();
    }
  }

  return (
    <AppShell title="Configurações">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Configurações</h1>
          <p className="pt-page-subtitle">Parâmetros do programa de mentoria</p>
        </div>
      </div>

      <div style={{ maxWidth: 760, margin: "0 auto" }} className="pt-stack">
        <div className="pt-card pt-card-flat">
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><Calendar size={16} /></div>
              <h2 className="pt-card-title">Configurações do semestre</h2>
            </div>
          </div>
          <form onSubmit={onSubmit} className="pt-card-body pt-stack">
            <div className="pt-grid-2">
              <div className="pt-field">
                <label className="pt-label">Semestre</label>
                <input className="pt-input" value={form.semestre} onChange={(e) => setForm({ ...form, semestre: e.target.value })} />
              </div>
              <div className="pt-field">
                <label className="pt-label">Instituição</label>
                <input className="pt-input" value={form.instituicao} onChange={(e) => setForm({ ...form, instituicao: e.target.value })} />
              </div>
            </div>

            <div className="pt-field">
              <label className="pt-label">Professor coordenador</label>
              <input className="pt-input" value={form.professor_coordenador} onChange={(e) => setForm({ ...form, professor_coordenador: e.target.value })} />
            </div>

            <div className="pt-field">
              <label className="pt-label">Programa</label>
              <input className="pt-input" value={form.programa} onChange={(e) => setForm({ ...form, programa: e.target.value })} />
            </div>

            <div className="pt-grid-3">
              <div className="pt-field">
                <label className="pt-label">Total de reuniões</label>
                <input
                  type="number"
                  className="pt-input"
                  value={form.total_reunioes}
                  onChange={(e) => setForm({ ...form, total_reunioes: Number(e.target.value) })}
                />
              </div>
              <div className="pt-field">
                <label className="pt-label">Data início</label>
                <input type="date" className="pt-input" value={form.data_inicio} onChange={(e) => setForm({ ...form, data_inicio: e.target.value })} />
              </div>
              <div className="pt-field">
                <label className="pt-label">Data fim</label>
                <input type="date" className="pt-input" value={form.data_fim} onChange={(e) => setForm({ ...form, data_fim: e.target.value })} />
              </div>
            </div>

            <div className="pt-grid-2">
              <div className="pt-field">
                <label className="pt-label">Coordenadora geral</label>
                <input className="pt-input" value={form.coordenadora_geral} onChange={(e) => setForm({ ...form, coordenadora_geral: e.target.value })} />
              </div>
              <div className="pt-field">
                <label className="pt-label">Coordenadores da monitoria (1 por linha)</label>
                <textarea className="pt-textarea" rows={3} value={coordText} onChange={(e) => setCoordText(e.target.value)} />
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button type="submit" className="pt-btn pt-btn-primary">
                <Save size={15} /> Salvar semestre
              </button>
            </div>
          </form>
        </div>

        <div className="pt-card pt-card-flat">
          <div className="pt-card-header">
            <div className="pt-card-header-title">
              <div className="pt-card-header-icon"><Settings size={16} /></div>
              <h2 className="pt-card-title">Handoff &amp; Auditoria</h2>
            </div>
          </div>
          <div className="pt-card-body" style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            {mode === "live" ? (
              <a href="/config/backup-db" className="pt-btn pt-btn-primary">
                <Download size={15} /> Exportar backup (.db)
              </a>
            ) : (
              <button type="button" className="pt-btn pt-btn-soft" onClick={() => notify("Backup disponível com servidor Python ativo.", "info")}>
                <Download size={15} /> Exportar backup (.db)
              </button>
            )}
            <button type="button" className="pt-btn pt-btn-danger" onClick={onClearLogs}>
              <Trash2 size={15} /> Limpar logs de auditoria
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
