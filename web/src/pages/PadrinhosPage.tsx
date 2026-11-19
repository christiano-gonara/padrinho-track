import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Search, UserPlus, Users } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { Avatar, CartoesMini, PresencaDots, TurnoTag } from "../components/ui/Kit";
import { StatusACGBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { useLiveData } from "../hooks/useLiveData";
import { apiFetch } from "../services/api";
import { Padrinho, StatusACG } from "../types/domain";

export function PadrinhosPage() {
  const { mode, scenario, addPadrinhoDemo, notify } = useApp();
  const navigate = useNavigate();
  const { live, reload: loadLive } = useLiveData<{ padrinhos: Padrinho[] }>("/api/padrinhos");
  const [filtro, setFiltro] = useState<"todos" | StatusACG>("todos");
  const [busca, setBusca] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  const [nome, setNome] = useState("");
  const [matricula, setMatricula] = useState("");
  const [turno, setTurno] = useState<"Manhã" | "Noite" | "">("");
  const [email, setEmail] = useState("");
  const [telefone, setTelefone] = useState("");

  const padrinhos = live?.padrinhos ?? scenario.padrinhos;
  const totalReunioes = scenario.reunioes.length;

  /** Quantas reuniões cada padrinho foi (só nos dados de exemplo) */
  function presencasDe(id: number): number | null {
    if (live) return null;
    return scenario.reunioes.filter((r) => scenario.presencasPorReuniao[r.id]?.find((x) => x.id === id)?.presente === 1).length;
  }

  function calourosDe(id: number): number {
    return scenario.matches.find((m) => m.padrinho.id === id)?.calouros.length ?? 0;
  }

  const contagem = (s: StatusACG | "sem") =>
    s === "sem"
      ? padrinhos.filter((p) => p.status === "inapto_amarelo" || p.status === "inapto_vermelho").length
      : padrinhos.filter((p) => p.status === s).length;

  const filtrados = padrinhos.filter((p) => {
    const q = busca.trim().toLowerCase();
    const okBusca = !q || p.nome.toLowerCase().includes(q) || p.matricula.toLowerCase().includes(q);
    const okStatus =
      filtro === "todos" ||
      p.status === filtro ||
      (filtro === "inapto_amarelo" && p.status === "inapto_vermelho");
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
          <h1 className="pt-page-title">Padrinhos e madrinhas</h1>
          <p className="pt-page-subtitle">{padrinhos.length} pessoas no programa neste semestre.</p>
        </div>
        <div className="pt-page-actions">
          <button type="button" className="pt-btn pt-btn-primary" onClick={() => setModalOpen(true)}>
            <UserPlus size={17} /> Adicionar padrinho
          </button>
        </div>
      </div>

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div role="group" aria-label="Filtrar por situação" style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            {(
              [
                ["todos", "Todos", padrinhos.length],
                ["apto", "Apto", contagem("apto")],
                ["alerta", "Atenção", contagem("alerta")],
                ["inapto_amarelo", "Sem ACG", contagem("sem")],
              ] as const
            ).map(([key, label, n]) => (
              <button
                key={key}
                type="button"
                aria-pressed={filtro === key}
                className={`pt-chip ${filtro === key ? "is-active" : ""}`}
                onClick={() => setFiltro(key)}
              >
                {label} · {n}
              </button>
            ))}
          </div>

          <div className="pt-input-wrap" style={{ width: 280, maxWidth: "100%" }}>
            <span className="pt-input-icon"><Search size={17} /></span>
            <input
              type="search"
              className="pt-input"
              aria-label="Buscar por nome ou matrícula"
              placeholder="Buscar por nome ou matrícula"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Turno</th>
                <th>Calouros</th>
                <th>Presença</th>
                <th>Cartões</th>
                <th>Situação</th>
                <th aria-label="Abrir" />
              </tr>
            </thead>
            <tbody>
              {filtrados.map((p) => {
                const pres = presencasDe(p.id);
                const ncal = calourosDe(p.id);
                return (
                  <tr key={p.id} className="is-clickable" onClick={() => navigate(`/padrinhos/${p.id}`)}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <Avatar nome={p.nome} />
                        <span>
                          <strong style={{ display: "block", fontSize: 15.5 }}>{p.nome}</strong>
                          <span style={{ fontSize: 13.5, color: "var(--pt-muted)" }}>Matrícula {p.matricula}</span>
                        </span>
                      </div>
                    </td>
                    <td><TurnoTag turno={p.turno} /></td>
                    <td>{ncal || "—"}</td>
                    <td>{pres === null ? <span className="pt-muted">—</span> : <PresencaDots feitas={pres} total={totalReunioes} />}</td>
                    <td><CartoesMini amarelos={p.amarelos} vermelhos={p.vermelhos} /></td>
                    <td><StatusACGBadge status={p.status} /></td>
                    <td className="pt-td-right">
                      <button
                        type="button"
                        className="pt-btn pt-btn-ghost pt-btn-sm"
                        aria-label={`Ver ${p.nome}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/padrinhos/${p.id}`);
                        }}
                      >
                        <ArrowRight size={17} />
                      </button>
                    </td>
                  </tr>
                );
              })}
              {filtrados.length === 0 && (
                <tr>
                  <td colSpan={7}>
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
              <span className="pt-modal-title">Adicionar padrinho</span>
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
                <label className="pt-label">E-mail</label>
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
