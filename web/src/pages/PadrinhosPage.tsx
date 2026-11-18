import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, Moon, Search, Sun, UserPlus, Users } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { StatusACGBadge, ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { abreviarNome } from "../data/scenarios";
import { apiFetch } from "../services/api";
import { Padrinho, StatusACG } from "../types/domain";

export function PadrinhosPage() {
  const { mode, scenario, addPadrinhoDemo, notify } = useApp();
  const navigate = useNavigate();
  const [liveList, setLiveList] = useState<Padrinho[] | null>(null);
  const [filtro, setFiltro] = useState<"todos" | StatusACG>("todos");
  const [busca, setBusca] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  const [nome, setNome] = useState("");
  const [matricula, setMatricula] = useState("");
  const [turno, setTurno] = useState<"Manhã" | "Noite" | "">("");
  const [email, setEmail] = useState("");
  const [telefone, setTelefone] = useState("");

  function loadLive() {
    if (mode !== "live") return;
    apiFetch<{ padrinhos: Padrinho[] }>("/api/padrinhos")
      .then((res) => setLiveList(res.padrinhos))
      .catch(() => setLiveList(null));
  }

  useEffect(() => {
    if (mode === "live") loadLive();
    else setLiveList(null);
  }, [mode]);

  const padrinhos = liveList ?? scenario.padrinhos;

  const filtrados = padrinhos.filter((p) => {
    const q = busca.trim().toLowerCase();
    const okBusca = !q || p.nome.toLowerCase().includes(q) || p.matricula.toLowerCase().includes(q);
    const okStatus = filtro === "todos" || p.status === filtro;
    return okBusca && okStatus;
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (mode === "live") {
      try {
        await apiFetch("/api/padrinhos", {
          method: "POST",
          body: JSON.stringify({ nome, matricula, turno, email, telefone }),
        });
        notify("Padrinho cadastrado com sucesso.", "success");
        loadLive();
      } catch (err) {
        notify(err instanceof Error ? err.message : "Erro ao cadastrar.", "error");
        return;
      }
    } else {
      addPadrinhoDemo({ nome, matricula, turno, email, telefone });
    }
    setNome("");
    setMatricula("");
    setTurno("");
    setEmail("");
    setTelefone("");
    setModalOpen(false);
  }

  return (
    <AppShell title="Padrinhos">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Padrinhos</h1>
          <p className="pt-page-subtitle">Veteranos inscritos no programa</p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-primary" onClick={() => setModalOpen(true)}>
            <UserPlus size={15} /> Novo padrinho
          </button>
        </div>
      </div>

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <span className="pt-card-title" style={{ marginRight: 6 }}>Lista de padrinhos</span>
            {(
              [
                ["todos", "Todos"],
                ["apto", "Aprovados"],
                ["alerta", "Em alerta"],
                ["inapto_amarelo", "Reprovados"],
                ["inapto_vermelho", "Reportados"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                className={`pt-chip ${filtro === key ? "is-active" : ""}`}
                onClick={() => setFiltro(key)}
              >
                {label}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span className="pt-muted" style={{ fontSize: 12.5 }}>{filtrados.length} cadastrados</span>
            <div className="pt-input-wrap" style={{ width: 215 }}>
              <span className="pt-input-icon"><Search size={14} /></span>
              <input
                type="text"
                className="pt-input"
                placeholder="Buscar por nome ou matrícula"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Matrícula</th>
                <th>Email</th>
                <th>Turno</th>
                <th style={{ textAlign: "center" }}>Status ACG</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtrados.map((p) => {
                const parts = p.nome.split(" ");
                const ini = ((parts[0]?.[0] || "") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
                return (
                  <tr key={p.id} className="is-clickable" onClick={() => navigate(`/padrinhos/${p.id}`)}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 600 }}>
                        <span className="pt-avatar">{ini}</span>
                        <span>{abreviarNome(p.nome)}</span>
                      </div>
                    </td>
                    <td className="pt-mono pt-muted">{p.matricula}</td>
                    <td className="pt-muted">{p.email || "—"}</td>
                    <td>
                      {p.turno === "Manhã" ? (
                        <ToneBadge tone="amber"><Sun size={12} /> Manhã</ToneBadge>
                      ) : p.turno === "Noite" ? (
                        <ToneBadge tone="brand"><Moon size={12} /> Noite</ToneBadge>
                      ) : (
                        <span className="pt-muted">—</span>
                      )}
                    </td>
                    <td className="pt-td-center"><StatusACGBadge status={p.status} /></td>
                    <td className="pt-td-right">
                      <button
                        type="button"
                        className="pt-btn pt-btn-ghost pt-btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/padrinhos/${p.id}`);
                        }}
                      >
                        <Eye size={13} /> Detalhes
                      </button>
                    </td>
                  </tr>
                );
              })}
              {filtrados.length === 0 && (
                <tr>
                  <td colSpan={6}>
                    <div className="pt-empty">
                      <div className="pt-empty-icon"><Users size={20} /></div>
                      <strong>Nenhum padrinho encontrado</strong>
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
            <div className="pt-modal-header">
              <UserPlus size={16} />
              <span className="pt-modal-title">Novo padrinho</span>
              <button type="button" className="pt-modal-close" onClick={() => setModalOpen(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={onSubmit} className="pt-modal-body">
              <div className="pt-field">
                <label className="pt-label">Nome completo</label>
                <input className="pt-input" required value={nome} onChange={(e) => setNome(e.target.value)} />
              </div>
              <div className="pt-grid-2">
                <div className="pt-field">
                  <label className="pt-label">Matrícula</label>
                  <input className="pt-input" required value={matricula} onChange={(e) => setMatricula(e.target.value)} />
                </div>
                <div className="pt-field">
                  <label className="pt-label">Turno</label>
                  <select className="pt-select" value={turno} onChange={(e) => setTurno(e.target.value as "Manhã" | "Noite" | "")}>
                    <option value="">Selecione...</option>
                    <option value="Manhã">Manhã</option>
                    <option value="Noite">Noite</option>
                  </select>
                </div>
              </div>
              <div className="pt-field">
                <label className="pt-label">Email</label>
                <input className="pt-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <div className="pt-field">
                <label className="pt-label">Telefone</label>
                <input className="pt-input" value={telefone} onChange={(e) => setTelefone(e.target.value)} />
              </div>
              <div className="pt-modal-actions">
                <button type="button" className="pt-btn pt-btn-ghost" onClick={() => setModalOpen(false)}>
                  Cancelar
                </button>
                <button type="submit" className="pt-btn pt-btn-primary">
                  Cadastrar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
