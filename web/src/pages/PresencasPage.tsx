import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CheckSquare, Save } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { useApp } from "../context/AppContext";
import { Avatar, Aviso, StatsRow } from "../components/ui/Kit";
import { formatarDataBr } from "../data/scenarios";
import "../styles/pages/Presencas.css";
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

  type Estado = "foi" | "justificou" | "faltou";

  function estadoDe(item: PresencaItem): Estado {
    if (item.presente === 1) return "foi";
    if (item.justificada === 1) return "justificou";
    return "faltou";
  }

  function marcar(pid: number, estado: Estado) {
    setLista((prev) =>
      prev.map((item) =>
        item.id === pid
          ? { ...item, presente: estado === "foi" ? 1 : 0, justificada: estado === "justificou" ? 1 : 0 }
          : item
      )
    );
  }

  function marcarTodosPresentes() {
    setLista((prev) => prev.map((item) => ({ ...item, presente: 1, justificada: 0 })));
  }

  const nFoi = lista.filter((x) => estadoDe(x) === "foi").length;
  const nJust = lista.filter((x) => estadoDe(x) === "justificou").length;
  const nFaltou = lista.length - nFoi - nJust;
  const OPCOES: { k: Estado; label: string }[] = [
    { k: "foi", label: "Foi" },
    { k: "justificou", label: "Justificou" },
    { k: "faltou", label: "Faltou" },
  ];

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const presentesIds = lista.filter((x) => x.presente === 1).map((x) => x.id);
    const justificadasIds = lista.filter((x) => x.justificada === 1).map((x) => x.id);
    if (mode === "live") {
      await apiFetch(`/api/presencas/${reuniaoId}`, {
        method: "POST",
        body: JSON.stringify({ presentes: presentesIds, justificadas: justificadasIds }),
      });
      notify("Presença salva.", "success");
    } else {
      savePresencasDemo(reuniaoId, presentesIds, justificadasIds);
    }
    navigate("/reunioes");
  }

  return (
    <AppShell title="Lançar presença">
      <div className="pt-page-head">
        <div>
          <Link to="/reunioes" className="pt-back-link">
            <ArrowLeft size={16} /> Voltar pras reuniões
          </Link>
          <h1 className="pt-page-title">Presença{reuniaoInfo?.tema ? ` · ${reuniaoInfo.tema}` : ""}</h1>
          <p className="pt-page-subtitle">
            {reuniaoInfo ? `Reunião de ${formatarDataBr(reuniaoInfo.data)}. ` : ""}Marque como cada pessoa ficou.
          </p>
        </div>
      </div>

      <StatsRow
        items={[
          { valor: nFoi, texto: "foram", cor: "var(--pt-brand-hover)" },
          { valor: nJust, texto: "justificaram" },
          { valor: nFaltou, texto: "faltaram sem justificar", cor: "var(--pt-amber-deep)" },
        ]}
      />

      <Aviso>
        Quem <strong>faltar sem justificar</strong> ganha um cartão amarelo sozinho. Se a pessoa avisou, marque{" "}
        <strong>Justificou</strong>: assim ela não leva cartão.
      </Aviso>

      <form onSubmit={onSubmit} className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <h2 className="pt-card-title">{lista.length} padrinhos</h2>
          <button type="button" className="pt-chip" onClick={marcarTodosPresentes}>
            <CheckSquare size={15} /> Marcar todos como presentes
          </button>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th style={{ textAlign: "right" }}>Presença</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((p) => {
                const est = estadoDe(p);
                return (
                  <tr key={p.id}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <Avatar nome={p.nome} />
                        <span>
                          <strong style={{ display: "block", fontSize: 15.5 }}>{p.nome}</strong>
                          {est === "faltou" && <span className="pt-pres-aviso">vai ganhar cartão amarelo</span>}
                        </span>
                      </div>
                    </td>
                    <td className="pt-td-right">
                      <div className="pt-pres-seg" role="group" aria-label={`Presença de ${p.nome}`}>
                        {OPCOES.map((o) => (
                          <button
                            key={o.k}
                            type="button"
                            aria-pressed={est === o.k}
                            className={est === o.k ? `is-${o.k}` : ""}
                            onClick={() => marcar(p.id, o.k)}
                          >
                            {o.label}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="pt-pres-footer">
          <Link to="/reunioes" className="pt-btn pt-btn-ghost">Cancelar</Link>
          <button type="submit" className="pt-btn pt-btn-primary">
            <Save size={17} /> Salvar presença
          </button>
        </div>
      </form>
    </AppShell>
  );
}
