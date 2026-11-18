import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CheckSquare, Save, UserCheck } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { useApp } from "../context/AppContext";
import { abreviarNome, formatarDataBr } from "../data/scenarios";
import { apiFetch } from "../services/api";
import { PresencaItem } from "../types/domain";

interface LivePresencasResp {
  reuniao: { id: number; data: string; tema: string } | null;
  presencas: PresencaItem[];
}

export function PresencasPage() {
  const { id } = useParams();
  const reuniaoId = Number(id);
  const { mode, scenario, savePresencasDemo, notify } = useApp();
  const navigate = useNavigate();

  const [reuniaoInfo, setReuniaoInfo] = useState<{ data?: string; tema?: string } | null>(null);
  const [lista, setLista] = useState<PresencaItem[]>([]);

  useEffect(() => {
    if (mode === "live") {
      apiFetch<LivePresencasResp>(`/api/presencas/${reuniaoId}`)
        .then((res) => {
          setReuniaoInfo(res.reuniao);
          setLista(res.presencas);
        })
        .catch(() => {});
    } else {
      const r = scenario.reunioes.find((x) => x.id === reuniaoId);
      setReuniaoInfo(r ?? null);
      const base =
        scenario.presencasPorReuniao[reuniaoId] ||
        scenario.padrinhos.map((p) => ({ id: p.id, nome: p.nome, matricula: p.matricula, presente: 0, justificada: 0 }));
      setLista(base.map((x) => ({ ...x })));
    }
  }, [mode, reuniaoId, scenario]);

  function toggleCampo(pid: number, campo: "presente" | "justificada") {
    setLista((prev) =>
      prev.map((item) => (item.id === pid ? { ...item, [campo]: item[campo] ? 0 : 1 } : item))
    );
  }

  function marcarTodos(valor: number) {
    setLista((prev) => prev.map((item) => ({ ...item, presente: valor })));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const presentesIds = lista.filter((x) => x.presente === 1).map((x) => x.id);
    const justificadasIds = lista.filter((x) => x.justificada === 1).map((x) => x.id);
    if (mode === "live") {
      await apiFetch(`/api/presencas/${reuniaoId}`, {
        method: "POST",
        body: JSON.stringify({ presentes: presentesIds, justificadas: justificadasIds }),
      });
      notify("Presenças registradas.", "success");
    } else {
      savePresencasDemo(reuniaoId, presentesIds, justificadasIds);
    }
    navigate("/reunioes");
  }

  return (
    <AppShell title="Lançar presenças">
      <div className="pt-page-head">
        <div>
          <Link to="/reunioes" className="pt-back-link">
            <ArrowLeft size={14} /> voltar para reuniões
          </Link>
          <h1 className="pt-page-title">Lançar presenças</h1>
          <p className="pt-page-subtitle">
            {reuniaoInfo ? `Reunião de ${formatarDataBr(reuniaoInfo.data)} — ${reuniaoInfo.tema || "sem tema"}` : `Reunião #${reuniaoId}`}
          </p>
        </div>
      </div>

      <form onSubmit={onSubmit} className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon"><UserCheck size={16} /></div>
            <h2 className="pt-card-title">Lista de padrinhos ativos</h2>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" className="pt-btn pt-btn-ghost pt-btn-sm" onClick={() => marcarTodos(1)}>
              <CheckSquare size={13} /> Marcar todos presentes
            </button>
            <button type="button" className="pt-btn pt-btn-ghost pt-btn-sm" onClick={() => marcarTodos(0)}>
              Desmarcar todos
            </button>
          </div>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Padrinho</th>
                <th>Matrícula</th>
                <th style={{ textAlign: "center" }}>Presente</th>
                <th style={{ textAlign: "center" }}>Falta justificada</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((p) => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 600 }}>{abreviarNome(p.nome)}</td>
                  <td className="pt-mono pt-muted">{p.matricula}</td>
                  <td className="pt-td-center">
                    <input
                      type="checkbox"
                      checked={p.presente === 1}
                      onChange={() => toggleCampo(p.id, "presente")}
                      style={{ width: 18, height: 18, accentColor: "var(--pt-brand)" }}
                    />
                  </td>
                  <td className="pt-td-center">
                    <input
                      type="checkbox"
                      checked={p.justificada === 1}
                      onChange={() => toggleCampo(p.id, "justificada")}
                      style={{ width: 18, height: 18, accentColor: "var(--pt-amber)" }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div
          className="pt-card-body"
          style={{
            borderTop: "1px solid var(--pt-border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <span className="pt-muted" style={{ fontSize: 12.5 }}>
            Ausentes sem justificativa recebem advertência amarela automaticamente.
          </span>
          <div style={{ display: "flex", gap: 10 }}>
            <Link to="/reunioes" className="pt-btn pt-btn-ghost">Cancelar</Link>
            <button type="submit" className="pt-btn pt-btn-primary">
              <Save size={15} /> Salvar presenças
            </button>
          </div>
        </div>
      </form>
    </AppShell>
  );
}
