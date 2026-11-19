import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldAlert, SquareStack, Trash2 } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { Avatar, CartoesMini } from "../components/ui/Kit";
import { StatusACGBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { formatarDataBr } from "../data/scenarios";
import "../styles/pages/Cartoes.css";
import { useLiveData } from "../hooks/useLiveData";
import { apiFetch } from "../services/api";
import { Advertencia, Padrinho } from "../types/domain";

interface LiveAdvResp {
  advertencias: Advertencia[];
  padrinhos: Padrinho[];
  total_reunioes: number;
}

export function AdvertenciasPage() {
  const { mode, scenario, addAdvertenciaDemo, removeAdvertenciaDemo, notify } = useApp();
  const { live, reload: loadLive } = useLiveData<LiveAdvResp>("/api/advertencias");
  const [modalOpen, setModalOpen] = useState(false);
  const [padrinhoId, setPadrinhoId] = useState<number>(0);
  const [tipo, setTipo] = useState<"amarelo" | "vermelho">("amarelo");
  const [motivo, setMotivo] = useState("");

  const advertencias = live ? live.advertencias : scenario.advertencias;
  const padrinhos = live ? live.padrinhos : scenario.padrinhos;
  const comCartao = padrinhos
    .filter((p) => p.amarelos > 0 || p.vermelhos > 0)
    .sort((a, b) => b.vermelhos - a.vermelhos || b.amarelos - a.amarelos);
  const limite = scenario.config.total_reunioes || 3;

  function situacaoTexto(amarelos: number, vermelhos: number): string {
    if (vermelhos > 0) return "Caso enviado ao professor";
    if (amarelos >= limite) return "Chegou ao limite";
    if (amarelos === limite - 1) return "Falta 1 pro limite";
    return "Tranquilo por enquanto";
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!padrinhoId) return;
    if (mode === "live") {
      await apiFetch("/api/advertencias", {
        method: "POST",
        body: JSON.stringify({ padrinho_id: padrinhoId, tipo, motivo }),
      });
      notify("Cartão registrado.", "success");
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
      notify("Cartão retirado.", "success");
      loadLive();
    } else {
      removeAdvertenciaDemo(id);
    }
  }

  return (
    <AppShell title="Cartões">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Cartões</h1>
          <p className="pt-page-subtitle">Os avisos que contam pra perder ou não a ACG. A maioria é dada sozinha pelo sistema.</p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-danger" onClick={() => setModalOpen(true)}>
            <SquareStack size={17} /> Dar cartão
          </button>
        </div>
      </div>

      <div className="pt-grid-2" style={{ marginBottom: 20, gap: 20 }}>
        <section className="pt-card pt-regra">
          <span className="pt-regra-cartao is-amarelo" aria-hidden="true" />
          <div>
            <h2 className="pt-card-title">Cartão amarelo</h2>
            <p>
              Falta sem justificar ou tema entregue com atraso. <strong>Com {limite} amarelos, a pessoa perde a ACG.</strong>
            </p>
          </div>
        </section>
        <section className="pt-card pt-regra">
          <span className="pt-regra-cartao is-vermelho" aria-hidden="true" />
          <div>
            <h2 className="pt-card-title">Cartão vermelho</h2>
            <p>
              Caso grave, como não entregar o tema. <strong>Perde a ACG na hora</strong> e o caso vai pro professor.
            </p>
          </div>
        </section>
      </div>

      <section className="pt-card" style={{ marginBottom: 20 }}>
        <div className="pt-cartoes-head">
          <h2 className="pt-card-title">Quem tem cartão</h2>
          <span>{comCartao.length} pessoa{comCartao.length === 1 ? "" : "s"}</span>
        </div>
        {comCartao.length === 0 && <p className="pt-cartoes-vazio">Ninguém levou cartão ainda.</p>}
        {comCartao.map((p) => (
          <div key={p.id} className="pt-row" style={{ flexWrap: "wrap" }}>
            <Avatar nome={p.nome} size={40} />
            <div style={{ flex: "1 1 200px" }}>
              <Link to={`/padrinhos/${p.id}`} className="pt-cartoes-nome">{p.nome}</Link>
              <div className="pt-cartoes-sit">{situacaoTexto(p.amarelos, p.vermelhos)}</div>
            </div>
            <CartoesMini amarelos={p.amarelos} vermelhos={p.vermelhos} />
            <StatusACGBadge status={p.status} />
          </div>
        ))}
      </section>

      <section className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <h2 className="pt-card-title">Todos os cartões</h2>
          <span style={{ fontSize: 14, color: "#475569" }}>{advertencias.length} no semestre</span>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Cartão</th>
                <th>Quem</th>
                <th>Motivo</th>
                <th>Data</th>
                <th aria-label="Ações" />
              </tr>
            </thead>
            <tbody>
              {advertencias.map((a) => (
                <tr key={a.id}>
                  <td>
                    <span className="pt-cartao-tipo">
                      <span className={a.tipo === "amarelo" ? "is-amarelo" : "is-vermelho"} />
                      {a.tipo === "amarelo" ? "Amarelo" : "Vermelho"}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>
                    <Link to={`/padrinhos/${a.padrinho_id}`}>{a.padrinho_nome}</Link>
                  </td>
                  <td>{a.motivo}</td>
                  <td style={{ fontWeight: 600 }}>{formatarDataBr(a.data)}</td>
                  <td className="pt-td-right">
                    <button
                      type="button"
                      className="pt-btn pt-btn-danger pt-btn-sm"
                      aria-label={`Tirar cartão de ${a.padrinho_nome}`}
                      onClick={() => onDelete(a.id)}
                    >
                      <Trash2 size={15} /> Tirar
                    </button>
                  </td>
                </tr>
              ))}
              {advertencias.length === 0 && (
                <tr>
                  <td colSpan={5}>
                    <div className="pt-empty">
                      <div className="pt-empty-icon"><ShieldAlert size={20} /></div>
                      <strong>Nenhum cartão neste semestre</strong>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {modalOpen && (
        <div className="pt-modal-backdrop" onClick={() => setModalOpen(false)}>
          <div className="pt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="pt-modal-header is-danger">
              <SquareStack size={18} />
              <span className="pt-modal-title">Dar cartão</span>
              <button type="button" className="pt-modal-close" onClick={() => setModalOpen(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={onSubmit} className="pt-modal-body">
              <div className="pt-field">
                <label className="pt-label">Pra quem</label>
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
                <label className="pt-label">Qual cartão</label>
                <select className="pt-select" value={tipo} onChange={(e) => setTipo(e.target.value as "amarelo" | "vermelho")}>
                  <option value="amarelo">Amarelo (aviso)</option>
                  <option value="vermelho">Vermelho (caso grave, perde a ACG)</option>
                </select>
              </div>
              <div className="pt-field">
                <label className="pt-label">Por quê</label>
                <textarea className="pt-textarea" required rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
              </div>
              <div className="pt-modal-actions">
                <button type="button" className="pt-btn pt-btn-ghost" onClick={() => setModalOpen(false)}>Cancelar</button>
                <button type="submit" className="pt-btn pt-btn-primary">Dar cartão</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
