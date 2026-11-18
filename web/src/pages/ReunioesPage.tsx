import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Calendar, Plus, Trash2, UserCheck, Video } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { useApp } from "../context/AppContext";
import { formatarDataBr } from "../data/scenarios";
import { apiFetch } from "../services/api";
import { Reuniao } from "../types/domain";

interface LiveReunioesResp {
  reunioes: { id: number; data: string; tema: string; descricao: string }[];
  sheets_presenca_url: string;
}

export function ReunioesPage() {
  const { mode, scenario, addReuniaoDemo, notify } = useApp();
  const navigate = useNavigate();
  const [live, setLive] = useState<LiveReunioesResp | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [data, setData] = useState("");
  const [tema, setTema] = useState("");
  const [descricao, setDescricao] = useState("");
  const [sheetsUrl, setSheetsUrl] = useState("");

  function loadLive() {
    if (mode !== "live") return;
    apiFetch<LiveReunioesResp>("/api/reunioes")
      .then((res) => {
        setLive(res);
        setSheetsUrl(res.sheets_presenca_url || "");
      })
      .catch(() => setLive(null));
  }

  useEffect(() => {
    if (mode === "live") loadLive();
    else setLive(null);
  }, [mode]);

  const reunioes: Partial<Reuniao>[] = live ? live.reunioes : scenario.reunioes;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (mode === "live") {
      try {
        await apiFetch("/api/reunioes", { method: "POST", body: JSON.stringify({ data, tema, descricao }) });
        notify("Reunião criada.", "success");
        loadLive();
      } catch (err) {
        notify(err instanceof Error ? err.message : "Erro ao criar reunião.", "error");
        return;
      }
    } else {
      addReuniaoDemo({ data, tema, descricao });
    }
    setData("");
    setTema("");
    setDescricao("");
    setModalOpen(false);
  }

  async function onDelete(id: number) {
    if (mode !== "live") {
      notify("No modo de cenários use os botões de cenário para alternar estados.", "info");
      return;
    }
    await apiFetch(`/api/reunioes/${id}`, { method: "DELETE" });
    notify("Reunião removida.", "success");
    loadLive();
  }

  async function onSaveSheets(e: FormEvent) {
    e.preventDefault();
    if (mode === "live") {
      await apiFetch("/api/reunioes/configurar-forms", {
        method: "POST",
        body: JSON.stringify({ sheets_presenca_url: sheetsUrl }),
      });
    }
    notify("Link da planilha de presença salvo.", "success");
  }

  return (
    <AppShell title="Reuniões">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Reuniões</h1>
          <p className="pt-page-subtitle">Histórico e controle de presenças</p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={15} /> Nova reunião
          </button>
        </div>
      </div>

      <div className="pt-card pt-card-flat" style={{ marginBottom: 22 }}>
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon"><Video size={16} /></div>
            <h2 className="pt-card-title">Lista de reuniões</h2>
          </div>
          <span className="pt-muted" style={{ fontSize: 12.5 }}>{reunioes.length} no total</span>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Tema</th>
                <th>Descrição</th>
                <th style={{ textAlign: "right" }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {reunioes.map((r) => (
                <tr key={r.id}>
                  <td>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 8, fontWeight: 600 }}>
                      <Calendar size={15} color="var(--pt-brand)" />
                      {formatarDataBr(r.data)}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500 }}>{r.tema || "—"}</td>
                  <td className="pt-muted">{r.descricao || "—"}</td>
                  <td className="pt-td-right">
                    <div style={{ display: "inline-flex", gap: 8 }}>
                      <button
                        type="button"
                        className="pt-btn pt-btn-soft pt-btn-sm"
                        onClick={() => navigate(`/presencas/${r.id}`)}
                      >
                        <UserCheck size={13} /> Presenças
                      </button>
                      {mode === "live" && r.id && (
                        <button
                          type="button"
                          className="pt-btn pt-btn-soft-red pt-btn-sm"
                          onClick={() => onDelete(r.id!)}
                          aria-label="Excluir reunião"
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon"><Video size={16} /></div>
            <h2 className="pt-card-title">Google Forms — Presença</h2>
          </div>
        </div>
        <form onSubmit={onSaveSheets} className="pt-card-body pt-stack">
          <div className="pt-field">
            <label className="pt-label">Link da planilha de respostas</label>
            <input
              className="pt-input"
              placeholder="https://docs.google.com/spreadsheets/d/..."
              value={sheetsUrl}
              onChange={(e) => setSheetsUrl(e.target.value)}
            />
          </div>
          <div className="pt-alert pt-alert-info">
            <span>Compartilhe a planilha com <strong>padrinho-track@padrinho-track.iam.gserviceaccount.com</strong> como Editor.</span>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button type="submit" className="pt-btn pt-btn-primary">Salvar link</button>
          </div>
        </form>
      </div>

      {modalOpen && (
        <div className="pt-modal-backdrop" onClick={() => setModalOpen(false)}>
          <div className="pt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="pt-modal-header">
              <Calendar size={16} />
              <span className="pt-modal-title">Nova reunião</span>
              <button type="button" className="pt-modal-close" onClick={() => setModalOpen(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={onSubmit} className="pt-modal-body">
              <div className="pt-field">
                <label className="pt-label">Data</label>
                <input type="date" className="pt-input" required value={data} onChange={(e) => setData(e.target.value)} />
              </div>
              <div className="pt-field">
                <label className="pt-label">Tema</label>
                <input className="pt-input" value={tema} onChange={(e) => setTema(e.target.value)} />
              </div>
              <div className="pt-field">
                <label className="pt-label">Descrição</label>
                <textarea className="pt-textarea" rows={3} value={descricao} onChange={(e) => setDescricao(e.target.value)} />
              </div>
              <div className="pt-modal-actions">
                <button type="button" className="pt-btn pt-btn-ghost" onClick={() => setModalOpen(false)}>Cancelar</button>
                <button type="submit" className="pt-btn pt-btn-primary">Criar reunião</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
