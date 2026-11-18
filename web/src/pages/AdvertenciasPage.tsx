import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ShieldAlert, Trash2 } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { abreviarNome, formatarDataBr } from "../data/scenarios";
import { apiFetch } from "../services/api";
import { Advertencia, Padrinho } from "../types/domain";

interface LiveAdvResp {
  advertencias: Advertencia[];
  padrinhos: Padrinho[];
  total_reunioes: number;
}

export function AdvertenciasPage() {
  const { mode, scenario, addAdvertenciaDemo, removeAdvertenciaDemo, notify } = useApp();
  const [live, setLive] = useState<LiveAdvResp | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [padrinhoId, setPadrinhoId] = useState<number>(0);
  const [tipo, setTipo] = useState<"amarelo" | "vermelho">("amarelo");
  const [motivo, setMotivo] = useState("");

  function loadLive() {
    if (mode !== "live") return;
    apiFetch<LiveAdvResp>("/api/advertencias").then(setLive).catch(() => setLive(null));
  }

  useEffect(() => {
    if (mode === "live") loadLive();
    else setLive(null);
  }, [mode]);

  const advertencias = live ? live.advertencias : scenario.advertencias;
  const padrinhos = live ? live.padrinhos : scenario.padrinhos;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!padrinhoId) return;
    if (mode === "live") {
      await apiFetch("/api/advertencias", {
        method: "POST",
        body: JSON.stringify({ padrinho_id: padrinhoId, tipo, motivo }),
      });
      notify("Advertência registrada.", "error");
      loadLive();
    } else {
      addAdvertenciaDemo({ padrinho_id: padrinhoId, tipo, motivo });
    }
    setMotivo("");
    setModalOpen(false);
  }

  async function onDelete(id: number) {
    if (mode === "live") {
      await apiFetch(`/api/advertencias/${id}`, { method: "DELETE" });
      notify("Advertência removida.", "success");
      loadLive();
    } else {
      removeAdvertenciaDemo(id);
    }
  }

  return (
    <AppShell title="Advertências">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Advertências</h1>
          <p className="pt-page-subtitle">Registro de cartões amarelos e vermelhos</p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-danger" onClick={() => setModalOpen(true)}>
            <AlertTriangle size={15} /> Advertência manual
          </button>
        </div>
      </div>

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon" style={{ background: "var(--pt-red-tint)", color: "var(--pt-red-deep)" }}>
              <ShieldAlert size={16} />
            </div>
            <h2 className="pt-card-title">Histórico de advertências</h2>
          </div>
          <span className="pt-muted" style={{ fontSize: 12.5 }}>{advertencias.length} registros</span>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Padrinho</th>
                <th style={{ textAlign: "center" }}>Tipo</th>
                <th>Origem</th>
                <th>Motivo</th>
                <th>Data</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {advertencias.map((a) => (
                <tr key={a.id}>
                  <td style={{ fontWeight: 600 }}>
                    <Link to={`/padrinhos/${a.padrinho_id}`}>{abreviarNome(a.padrinho_nome)}</Link>
                  </td>
                  <td className="pt-td-center">
                    <ToneBadge tone={a.tipo === "amarelo" ? "amber" : "red"}>
                      {a.tipo === "amarelo" ? "Advertência" : "Advertência Grave"}
                    </ToneBadge>
                  </td>
                  <td className="pt-muted">{a.origem}</td>
                  <td className="pt-muted">{a.motivo}</td>
                  <td className="pt-mono pt-muted">{formatarDataBr(a.data)}</td>
                  <td className="pt-td-right">
                    <button type="button" className="pt-btn pt-btn-soft-red pt-btn-sm" onClick={() => onDelete(a.id)}>
                      <Trash2 size={13} /> Excluir
                    </button>
                  </td>
                </tr>
              ))}
              {advertencias.length === 0 && (
                <tr>
                  <td colSpan={6}>
                    <div className="pt-empty">
                      <div className="pt-empty-icon"><ShieldAlert size={20} /></div>
                      <strong>Nenhuma advertência neste cenário</strong>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {modalOpen && (
        <div className="pt-modal-backdrop" onClick={() => setModalOpen(false)}>
          <div className="pt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="pt-modal-header is-danger">
              <AlertTriangle size={16} />
              <span className="pt-modal-title">Advertência manual</span>
              <button type="button" className="pt-modal-close" onClick={() => setModalOpen(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={onSubmit} className="pt-modal-body">
              <div className="pt-field">
                <label className="pt-label">Padrinho</label>
                <select
                  className="pt-select"
                  required
                  value={padrinhoId || ""}
                  onChange={(e) => setPadrinhoId(Number(e.target.value))}
                >
                  <option value="">Selecione...</option>
                  {padrinhos.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome}</option>
                  ))}
                </select>
              </div>
              <div className="pt-field">
                <label className="pt-label">Tipo</label>
                <select className="pt-select" value={tipo} onChange={(e) => setTipo(e.target.value as "amarelo" | "vermelho")}>
                  <option value="amarelo">Advertência Amarela</option>
                  <option value="vermelho">Advertência Grave (Vermelha)</option>
                </select>
              </div>
              <div className="pt-field">
                <label className="pt-label">Motivo</label>
                <textarea className="pt-textarea" required rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
              </div>
              <div className="pt-modal-actions">
                <button type="button" className="pt-btn pt-btn-ghost" onClick={() => setModalOpen(false)}>Cancelar</button>
                <button type="submit" className="pt-btn pt-btn-danger">Emitir</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
