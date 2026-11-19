import { useState } from "react";
import { Link } from "react-router-dom";
import { Moon, Search, Sun, Users } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { Avatar, TurnoTag } from "../components/ui/Kit";
import { useApp } from "../context/AppContext";
import { useLiveData } from "../hooks/useLiveData";
import { MatchGrupo } from "../types/domain";
import "../styles/pages/Pessoas.css";

export function CalourosPage() {
  const { scenario } = useApp();
  const { live } = useLiveData<{ grupos: MatchGrupo[] }>("/api/calouros");
  const [busca, setBusca] = useState("");
  const [turno, setTurno] = useState<"todos" | "Manhã" | "Noite">("todos");

  const grupos = (live?.grupos ?? scenario.matches).filter((g) => g.calouros.length > 0);
  const q = busca.trim().toLowerCase();
  const filtrados = grupos.filter(
    (g) =>
      (turno === "todos" || g.padrinho.turno === turno) &&
      (!q || g.padrinho.nome.toLowerCase().includes(q) || g.calouros.some((c) => c.nome.toLowerCase().includes(q)))
  );

  const total = grupos.reduce((acc, g) => acc + g.calouros.length, 0);
  const porTurno = (t: "Manhã" | "Noite") =>
    grupos.filter((g) => g.padrinho.turno === t).reduce((acc, g) => acc + g.calouros.length, 0);

  return (
    <AppShell title="Calouros">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Calouros</h1>
          <p className="pt-page-subtitle">
            {total > 0
              ? `${total} calouros, agrupados por quem cuida de cada um.`
              : "Os calouros aparecem aqui depois que as duplas forem formadas."}
          </p>
        </div>
      </div>

      {grupos.length > 0 && (
        <div className="pt-filtros">
          <div role="group" aria-label="Filtrar por turno" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" aria-pressed={turno === "todos"} className={`pt-chip ${turno === "todos" ? "is-active" : ""}`} onClick={() => setTurno("todos")}>
              Todos · {total}
            </button>
            <button type="button" aria-pressed={turno === "Manhã"} className={`pt-chip ${turno === "Manhã" ? "is-active" : ""}`} onClick={() => setTurno("Manhã")}>
              <Sun size={15} /> Manhã · {porTurno("Manhã")}
            </button>
            <button type="button" aria-pressed={turno === "Noite"} className={`pt-chip ${turno === "Noite" ? "is-active" : ""}`} onClick={() => setTurno("Noite")}>
              <Moon size={15} /> Noite · {porTurno("Noite")}
            </button>
          </div>
          <div className="pt-input-wrap" style={{ width: 300, maxWidth: "100%" }}>
            <span className="pt-input-icon"><Search size={17} /></span>
            <input
              type="search"
              className="pt-input"
              aria-label="Buscar calouro ou padrinho"
              placeholder="Buscar calouro ou padrinho"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
        </div>
      )}

      <div className="pt-cards-3">
        {filtrados.map((g) => (
          <section key={g.padrinho.id} className="pt-card pt-card-flat">
            <div className="pt-padrinho-head">
              <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
                <Avatar nome={g.padrinho.nome} size={38} tone="white" />
                <div style={{ minWidth: 0 }}>
                  <div className="pt-padrinho-kicker">Padrinho</div>
                  <Link to={`/padrinhos/${g.padrinho.id}`} className="pt-padrinho-nome">
                    {g.padrinho.nome}
                  </Link>
                </div>
              </div>
              <TurnoTag turno={g.padrinho.turno} />
            </div>
            <div style={{ padding: "6px 20px 18px" }}>
              {g.calouros.map((c) => (
                <div key={c.id} className="pt-calouro">
                  <Avatar nome={c.nome} size={32} tone="neutral" />
                  <div>
                    <div className="pt-calouro-nome">{c.nome}</div>
                    <div className="pt-calouro-tel">{c.telefone || "sem telefone"}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

      {filtrados.length === 0 && (
        <div className="pt-card">
          <div className="pt-empty">
            <div className="pt-empty-icon"><Users size={20} /></div>
            <strong style={{ color: "var(--pt-ink)", fontSize: 16 }}>
              {grupos.length === 0 ? "As duplas ainda não foram formadas" : "Ninguém encontrado com essa busca"}
            </strong>
            {grupos.length === 0 && (
              <p style={{ margin: 0, fontSize: 15 }}>
                Os {scenario.calourosSoltos.length} calouros inscritos aparecem aqui depois que você formar as duplas.{" "}
                <Link to="/match" style={{ color: "var(--pt-brand-hover)", fontWeight: 600 }}>Formar duplas</Link>
              </p>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}
