import { FormEvent, useState } from "react";
import { BookOpen, Check, Plus, X } from "lucide-react";
import { Avatar, Aviso } from "../components/ui/Kit";
import { AppShell } from "../components/layout/AppShell";
import { ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { formatarDataBr } from "../data/scenarios";
import "../styles/pages/Temas.css";
import { useLiveData } from "../hooks/useLiveData";
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
  const { live, reload: loadLive } = useLiveData<LiveTemasResp>("/api/temas");
  const [modalOpen, setModalOpen] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [dataAviso, setDataAviso] = useState("");
  const [dataLimite, setDataLimite] = useState("");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const temas: TemaItem[] = live
    ? live.temas.map((x) => ({
        ...x.tema,
        responsaveis: x.padrinhos,
      }))
    : scenario.temas;

  const padrinhos = live ? live.padrinhos : scenario.padrinhos;
  const COR: Record<TemaItem["situacao"], string> = {
    entregue: "#10b981",
    atraso: "#f59e0b",
    nao_entregue: "#dc2626",
    pendente: "#e2e8f0",
  };
  const qtd = (s: TemaItem["situacao"]) => temas.filter((t) => t.situacao === s).length;

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
          <p className="pt-page-subtitle">O cronograma de conteúdos que os padrinhos preparam pros calouros.</p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={17} /> Novo tema
          </button>
        </div>
      </div>

      {temas.length > 0 && (
        <section className="pt-card" style={{ marginBottom: 20 }}>
          <h2 className="pt-card-title" style={{ marginBottom: 14 }}>Como estão as entregas</h2>
          <div className="pt-temas-bar" role="img" aria-label={`${qtd("entregue")} no prazo, ${qtd("atraso")} atrasaram, ${qtd("nao_entregue")} não entregues, ${qtd("pendente")} ainda no prazo`}>
            {temas.map((t) => (
              <span key={t.id} style={{ background: COR[t.situacao] }} title={t.titulo} />
            ))}
          </div>
          <div className="pt-temas-leg">
            <span className="is-ok"><strong>{qtd("entregue")}</strong> no prazo</span>
            <span className="is-atraso"><strong>{qtd("atraso")}</strong> atrasou</span>
            <span className="is-nao"><strong>{qtd("nao_entregue")}</strong> não veio</span>
            {qtd("pendente") > 0 && <span><strong>{qtd("pendente")}</strong> ainda no prazo</span>}
          </div>
        </section>
      )}

      <Aviso>
        Entrega atrasada dá <strong>cartão amarelo</strong> pra dupla. Tema não entregue dá <strong>cartão vermelho</strong>.
      </Aviso>

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <h2 className="pt-card-title">Cronograma</h2>
          <span style={{ fontSize: 14, color: "#475569" }}>{temas.length} temas</span>
        </div>
        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Tema</th>
                <th>Quem apresenta</th>
                <th>Prazo</th>
                <th>Situação</th>
                <th style={{ textAlign: "right" }}>Entregue em</th>
              </tr>
            </thead>
            <tbody>
              {temas.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontWeight: 700 }}>{t.titulo}</td>
                  <td>
                    <span className="pt-temas-quem">
                      <span className="pt-temas-avts">
                        {t.responsaveis.map((r) => (
                          <Avatar key={r.id} nome={r.nome} size={32} />
                        ))}
                      </span>
                      {t.responsaveis.map((r) => r.nome.split(" ")[0]).join(" e ")}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{formatarDataBr(t.data_limite)}</td>
                  <td>
                    {t.situacao === "entregue" ? (
                      <ToneBadge tone="green">Entregue</ToneBadge>
                    ) : t.situacao === "atraso" ? (
                      <ToneBadge tone="amber">Atrasou</ToneBadge>
                    ) : t.situacao === "nao_entregue" ? (
                      <ToneBadge tone="red">Não entregue</ToneBadge>
                    ) : (
                      <ToneBadge tone="neutral">No prazo</ToneBadge>
                    )}
                  </td>
                  <td className="pt-td-right">
                    {t.situacao === "pendente" ? (
                      <div style={{ display: "inline-flex", gap: 6 }}>
                        <button type="button" className="pt-btn pt-btn-soft-green pt-btn-sm" onClick={() => onMark(t.id, "entregue")}>
                          <Check size={15} /> Entregou
                        </button>
                        <button type="button" className="pt-btn pt-btn-soft-red pt-btn-sm" onClick={() => onMark(t.id, "nao_entregue")}>
                          <X size={15} /> Não entregou
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontSize: 15 }}>{formatarDataBr(t.data_entrega)}</span>
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
                <label className="pt-label">Nome do tema</label>
                <input className="pt-input" required value={titulo} onChange={(e) => setTitulo(e.target.value)} />
              </div>
              <div className="pt-grid-2">
                <div className="pt-field">
                  <label className="pt-label">Avisar em</label>
                  <input type="date" className="pt-input" value={dataAviso} onChange={(e) => setDataAviso(e.target.value)} />
                </div>
                <div className="pt-field">
                  <label className="pt-label">Prazo</label>
                  <input type="date" className="pt-input" required value={dataLimite} onChange={(e) => setDataLimite(e.target.value)} />
                </div>
              </div>
              <div className="pt-field">
                <label className="pt-label">Quem apresenta (segure Ctrl pra escolher mais de um)</label>
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
                <button type="submit" className="pt-btn pt-btn-primary">Criar tema</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
