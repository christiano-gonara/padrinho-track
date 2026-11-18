import { FormEvent, useEffect, useState } from "react";
import { BookOpen, Check, Plus, X } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { abreviarNome, formatarDataBr } from "../data/scenarios";
import { apiFetch } from "../services/api";
import { Padrinho, TemaItem } from "../types/domain";

interface LiveTemasResp {
  temas: {
    tema: { id: number; titulo: string; data_aviso: string; data_limite: string; data_entrega?: string; situacao: TemaItem["situacao"] };
    padrinhos: { id: number; nome: string }[];
  }[];
  padrinhos: Padrinho[];
}

export function TemasPage() {
  const { mode, scenario, addTemaDemo, markTemaDemo, notify } = useApp();
  const [live, setLive] = useState<LiveTemasResp | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [dataAviso, setDataAviso] = useState("");
  const [dataLimite, setDataLimite] = useState("");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  function loadLive() {
    if (mode !== "live") return;
    apiFetch<LiveTemasResp>("/api/temas").then(setLive).catch(() => setLive(null));
  }

  useEffect(() => {
    if (mode === "live") loadLive();
    else setLive(null);
  }, [mode]);

  const temas: TemaItem[] = live
    ? live.temas.map((x) => ({
        ...x.tema,
        responsaveis: x.padrinhos,
      }))
    : scenario.temas;

  const padrinhos = live ? live.padrinhos : scenario.padrinhos;

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (mode === "live") {
      await apiFetch("/api/temas", {
        method: "POST",
        body: JSON.stringify({ titulo, data_aviso: dataAviso, data_limite: dataLimite, padrinho_ids: selectedIds }),
      });
      notify("Tema criado.", "success");
      loadLive();
    } else {
      addTemaDemo({ titulo, data_aviso: dataAviso, data_limite: dataLimite, padrinho_ids: selectedIds });
    }
    setTitulo("");
    setDataAviso("");
    setDataLimite("");
    setSelectedIds([]);
    setModalOpen(false);
  }

  async function onMark(temaId: number, status: "entregue" | "nao_entregue") {
    if (mode === "live") {
      const endpoint = status === "entregue" ? `/api/temas/${temaId}/entregue` : `/api/temas/${temaId}/nao-entregue`;
      await apiFetch(endpoint, { method: "POST", body: JSON.stringify({}) });
      notify("Situação do tema atualizada.", "success");
      loadLive();
    } else {
      markTemaDemo(temaId, status);
    }
  }

  return (
    <AppShell title="Temas">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Temas</h1>
          <p className="pt-page-subtitle">Controle de entregas do cronograma</p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={15} /> Novo tema
          </button>
        </div>
      </div>

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon"><BookOpen size={16} /></div>
            <h2 className="pt-card-title">Cronograma de temas</h2>
          </div>
          <span className="pt-muted" style={{ fontSize: 12.5 }}>{temas.length} temas</span>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Título</th>
                <th>Responsáveis</th>
                <th style={{ textAlign: "center" }}>Aviso</th>
                <th style={{ textAlign: "center" }}>Prazo</th>
                <th style={{ textAlign: "center" }}>Situação</th>
                <th style={{ textAlign: "right" }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {temas.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontWeight: 600 }}>{t.titulo}</td>
                  <td>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                      {t.responsaveis.map((r) => (
                        <span key={r.id} className="pt-tag">{abreviarNome(r.nome)}</span>
                      ))}
                    </div>
                  </td>
                  <td className="pt-td-center pt-mono pt-muted">{formatarDataBr(t.data_aviso)}</td>
                  <td className="pt-td-center pt-mono pt-muted">{formatarDataBr(t.data_limite)}</td>
                  <td className="pt-td-center">
                    {t.situacao === "entregue" ? (
                      <ToneBadge tone="green">Entregue</ToneBadge>
                    ) : t.situacao === "atraso" ? (
                      <ToneBadge tone="amber">Atraso</ToneBadge>
                    ) : t.situacao === "nao_entregue" ? (
                      <ToneBadge tone="red">Não entregue</ToneBadge>
                    ) : (
                      <ToneBadge tone="neutral">Pendente</ToneBadge>
                    )}
                  </td>
                  <td className="pt-td-right">
                    {t.situacao === "pendente" ? (
                      <div style={{ display: "inline-flex", gap: 6 }}>
                        <button type="button" className="pt-btn pt-btn-soft-green pt-btn-sm" onClick={() => onMark(t.id, "entregue")}>
                          <Check size={13} /> Entregue
                        </button>
                        <button type="button" className="pt-btn pt-btn-soft-red pt-btn-sm" onClick={() => onMark(t.id, "nao_entregue")}>
                          <X size={13} /> Não entregue
                        </button>
                      </div>
                    ) : (
                      <span className="pt-mono pt-muted" style={{ fontSize: 12 }}>
                        {formatarDataBr(t.data_entrega)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modalOpen && (
        <div className="pt-modal-backdrop" onClick={() => setModalOpen(false)}>
          <div className="pt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="pt-modal-header">
              <BookOpen size={16} />
              <span className="pt-modal-title">Novo tema</span>
              <button type="button" className="pt-modal-close" onClick={() => setModalOpen(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={onCreate} className="pt-modal-body">
              <div className="pt-field">
                <label className="pt-label">Título</label>
                <input className="pt-input" required value={titulo} onChange={(e) => setTitulo(e.target.value)} />
              </div>
              <div className="pt-grid-2">
                <div className="pt-field">
                  <label className="pt-label">Aviso</label>
                  <input type="date" className="pt-input" value={dataAviso} onChange={(e) => setDataAviso(e.target.value)} />
                </div>
                <div className="pt-field">
                  <label className="pt-label">Prazo</label>
                  <input type="date" className="pt-input" required value={dataLimite} onChange={(e) => setDataLimite(e.target.value)} />
                </div>
              </div>
              <div className="pt-field">
                <label className="pt-label">Responsáveis</label>
                <select
                  multiple
                  required
                  className="pt-select"
                  style={{ height: 130 }}
                  value={selectedIds.map(String)}
                  onChange={(e) => setSelectedIds(Array.from(e.target.selectedOptions).map((o) => Number(o.value)))}
                >
                  {padrinhos.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome}</option>
                  ))}
                </select>
              </div>
              <div className="pt-modal-actions">
                <button type="button" className="pt-btn pt-btn-ghost" onClick={() => setModalOpen(false)}>Cancelar</button>
                <button type="submit" className="pt-btn pt-btn-primary">Registrar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
