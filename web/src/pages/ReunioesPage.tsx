import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Calendar, Check, Plus, Trash2, Upload } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { useApp } from "../context/AppContext";
import { PresencaBar } from "../components/ui/Kit";
import "../styles/pages/Reunioes.css";
import { useLiveData } from "../hooks/useLiveData";
import { apiFetch } from "../services/api";
import { Reuniao } from "../types/domain";

interface LiveReunioesResp {
  reunioes: { id: number; data: string; tema: string; descricao: string }[];
  sheets_presenca_url: string;
}

export function ReunioesPage() {
  const { mode, scenario, addReuniaoDemo, notify } = useApp();
  const navigate = useNavigate();
  const { live, reload: loadLive } = useLiveData<LiveReunioesResp>("/api/reunioes");
  const [modalOpen, setModalOpen] = useState(false);
  const [data, setData] = useState("");
  const [tema, setTema] = useState("");
  const [descricao, setDescricao] = useState("");
  const [sheetsUrl, setSheetsUrl] = useState("");

  useEffect(() => {
    if (live) setSheetsUrl(live.sheets_presenca_url || "");
  }, [live]);

  const reunioes: Partial<Reuniao>[] = live ? live.reunioes : scenario.reunioes;
  const totalPrevisto = scenario.config.total_reunioes || reunioes.length;
  const MESES = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"];

  function diaMes(data?: string): { dia: string; mes: string } {
    const partes = (data || "").split("-");
    if (partes.length !== 3) return { dia: data || "—", mes: "" };
    return { dia: partes[2], mes: MESES[Number(partes[1]) - 1] ?? "" };
  }

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
      notify("Nos dados de exemplo não dá pra apagar reunião. Troque o momento do semestre no topo.", "info");
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
    notify("Link da planilha salvo.", "success");
  }

  return (
    <AppShell title="Reuniões">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Reuniões</h1>
          <p className="pt-page-subtitle">
            {reunioes.length} de {totalPrevisto} reuniões feitas. Quem faltar sem justificar ganha um cartão amarelo.
          </p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={17} /> Nova reunião
          </button>
        </div>
      </div>

      {reunioes.length === 0 && (
        <div className="pt-card" style={{ marginBottom: 20 }}>
          <div className="pt-empty">
            <div className="pt-empty-icon"><Calendar size={20} /></div>
            <strong style={{ color: "var(--pt-ink)", fontSize: 16 }}>Nenhuma reunião ainda</strong>
            <p style={{ margin: 0, fontSize: 15 }}>Crie a primeira reunião do semestre pra começar a marcar presença.</p>
          </div>
        </div>
      )}

      {reunioes.map((r) => {
        const { dia, mes } = diaMes(r.data);
        const temNumeros = typeof r.presentes === "number";
        return (
          <section key={r.id} className="pt-card pt-reuniao">
            <div className="pt-reuniao-data">
              <strong>{dia}</strong>
              <span>{mes}</span>
            </div>
            <div className="pt-reuniao-info">
              <h2>{r.tema || "Reunião"}</h2>
              {r.descricao && <p>{r.descricao}</p>}
            </div>
            {temNumeros && (
              <div className="pt-reuniao-pres">
                <PresencaBar foi={r.presentes ?? 0} justificou={r.justificadas ?? 0} faltou={r.ausentes ?? 0} />
                <div>
                  <span><strong>{r.presentes}</strong> foram</span>
                  <span><strong>{r.justificadas ?? 0}</strong> justificaram</span>
                  <span className="is-falta"><strong>{r.ausentes ?? 0}</strong> faltaram</span>
                </div>
              </div>
            )}
            <div className="pt-reuniao-acoes">
              <button type="button" className="pt-btn pt-btn-ghost" onClick={() => navigate(`/presencas/${r.id}`)}>
                <Check size={17} /> {temNumeros ? "Ver presença" : "Lançar presença"}
              </button>
              {mode === "live" && r.id && (
                <button
                  type="button"
                  className="pt-btn pt-btn-danger"
                  onClick={() => onDelete(r.id!)}
                  aria-label={`Apagar reunião ${r.tema || ""}`}
                >
                  <Trash2 size={17} />
                </button>
              )}
            </div>
          </section>
        );
      })}

      <section className="pt-card" style={{ marginTop: 26 }}>
        <h2 className="pt-card-title">Lançar presença pelo formulário</h2>
        <p style={{ margin: "6px 0 16px", fontSize: 15, color: "#475569", lineHeight: 1.55 }}>
          Se a presença foi feita num Google Forms, cole aqui o link da planilha de respostas.
        </p>
        <form onSubmit={onSaveSheets} className="pt-stack">
          <div className="pt-field">
            <label className="pt-label" htmlFor="sheets-presenca">Link da planilha de presença</label>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <input
                id="sheets-presenca"
                className="pt-input"
                style={{ flex: "1 1 280px", width: "auto" }}
                placeholder="https://docs.google.com/spreadsheets/d/..."
                value={sheetsUrl}
                onChange={(e) => setSheetsUrl(e.target.value)}
              />
              <button type="submit" className="pt-btn pt-btn-primary">
                <Upload size={17} /> Salvar link
              </button>
            </div>
          </div>
          <div className="pt-alert pt-alert-info">
            <span>
              A planilha precisa estar compartilhada com <strong>padrinho-track@padrinho-track.iam.gserviceaccount.com</strong> como Editor.
            </span>
          </div>
        </form>
      </section>

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
