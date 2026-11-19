import { useState } from "react";
import { Link } from "react-router-dom";
import { Link2, Moon, Printer, RefreshCw, Sparkles, Sun } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { Avatar, Aviso, StatsRow, TurnoTag } from "../components/ui/Kit";
import { useApp } from "../context/AppContext";
import { useLiveData } from "../hooks/useLiveData";
import { apiFetch } from "../services/api";
import { MatchGrupo } from "../types/domain";
import "../styles/pages/Pessoas.css";

interface LiveMatchResp {
  dados: MatchGrupo[];
  total_matches: number;
  total_calouros: number;
  total_padrinhos: number;
}

export function MatchPage() {
  const { mode, scenario, runMatchDemo, notify } = useApp();
  const { live, reload: loadLive } = useLiveData<LiveMatchResp>("/api/match");
  const [turno, setTurno] = useState<"todos" | "Manhã" | "Noite">("todos");

  const todos = live ? live.dados : scenario.matches;
  const grupos = todos.filter((g) => g.calouros.length > 0);
  const totalPadrinhos = live ? live.total_padrinhos : scenario.padrinhos.length;
  const totalCalouros = live ? live.total_calouros : scenario.calourosSoltos.length;
  const comPadrinho = live ? live.total_matches : grupos.reduce((acc, g) => acc + g.calouros.length, 0);
  const semCalouro = live
    ? live.dados.filter((g) => g.calouros.length === 0).map((g) => g.padrinho)
    : scenario.padrinhos.filter((p) => !grupos.some((g) => g.padrinho.id === p.id));
  const visiveis = grupos.filter((g) => turno === "todos" || g.padrinho.turno === turno);
  const contarTurno = (t: "Manhã" | "Noite") => grupos.filter((g) => g.padrinho.turno === t).length;

  async function handleRunMatch() {
    if (mode === "live") {
      try {
        const res = await apiFetch<{ total: number }>("/api/match/rodar", { method: "POST" });
        notify(`Pronto! ${res.total} calouros ganharam padrinho.`, "success");
        loadLive();
      } catch (err) {
        notify(err instanceof Error ? err.message : "Não deu pra formar as duplas.", "error");
      }
    } else {
      runMatchDemo();
    }
  }

  return (
    <AppShell title="Duplas">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Duplas do semestre</h1>
          <p className="pt-page-subtitle">Quem cuida de quem. Cada calouro tem um padrinho do mesmo turno.</p>
        </div>
        {comPadrinho > 0 && (
          <div className="pt-page-actions">
            <button type="button" className="pt-btn pt-btn-ghost" onClick={handleRunMatch}>
              <RefreshCw size={17} /> Refazer duplas
            </button>
            {mode === "live" && (
              <a href="/match/lista-contatos" target="_blank" rel="noopener noreferrer" className="pt-btn pt-btn-primary">
                <Printer size={17} /> Lista de contatos
              </a>
            )}
          </div>
        )}
      </div>

      {comPadrinho === 0 ? (
        <div className="pt-card" style={{ padding: "52px 24px", textAlign: "center" }}>
          <div className="pt-empty-icon" style={{ margin: "0 auto 14px", width: 56, height: 56 }}>
            <Link2 size={24} />
          </div>
          <h2 style={{ margin: "0 0 8px", fontSize: 20, color: "var(--pt-ink)" }}>As duplas ainda não foram formadas</h2>
          <p style={{ maxWidth: 520, margin: "0 auto 22px", fontSize: 15.5, color: "var(--pt-text)", lineHeight: 1.6 }}>
            O sistema junta os {totalCalouros} calouros com os {totalPadrinhos} padrinhos. Primeiro pelo turno, depois pelo
            perfil de cada um (gênero, idade, cidade, bolsa e trabalho). Você pode refazer quantas vezes quiser.
          </p>
          <button type="button" className="pt-btn pt-btn-primary pt-btn-lg" onClick={handleRunMatch}>
            <Sparkles size={18} /> Formar duplas agora
          </button>
        </div>
      ) : (
        <>
          <StatsRow
            items={[
              { valor: comPadrinho, texto: "calouros com padrinho", cor: "var(--pt-green-deep)" },
              { valor: Math.max(totalCalouros - comPadrinho, 0), texto: "calouros sem padrinho" },
              { valor: grupos.length, texto: "padrinhos com calouros" },
              { valor: semCalouro.length, texto: "padrinhos sem calouro" },
            ]}
          />

          {semCalouro.length > 0 && (
            <Aviso>
              As duplas foram formadas pelo <strong>turno</strong> e pelo <strong>perfil</strong> de cada pessoa.{" "}
              {semCalouro.map((p) => p.nome).join(", ")}{" "}
              {semCalouro.length > 1 ? "ficaram" : "ficou"} sem calouro porque havia mais padrinhos que calouros.
            </Aviso>
          )}

          <div role="group" aria-label="Filtrar por turno" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 18 }}>
            <button type="button" aria-pressed={turno === "todos"} className={`pt-chip ${turno === "todos" ? "is-active" : ""}`} onClick={() => setTurno("todos")}>
              Todas · {grupos.length}
            </button>
            <button type="button" aria-pressed={turno === "Manhã"} className={`pt-chip ${turno === "Manhã" ? "is-active" : ""}`} onClick={() => setTurno("Manhã")}>
              <Sun size={15} /> Manhã · {contarTurno("Manhã")}
            </button>
            <button type="button" aria-pressed={turno === "Noite"} className={`pt-chip ${turno === "Noite" ? "is-active" : ""}`} onClick={() => setTurno("Noite")}>
              <Moon size={15} /> Noite · {contarTurno("Noite")}
            </button>
          </div>

          <div className="pt-cards-3">
            {visiveis.map((g) => (
              <section key={g.padrinho.id} className="pt-card pt-card-flat">
                <div className="pt-padrinho-head">
                  <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
                    <Avatar nome={g.padrinho.nome} size={40} tone="white" />
                    <div style={{ minWidth: 0 }}>
                      <Link to={`/padrinhos/${g.padrinho.id}`} className="pt-padrinho-nome">
                        {g.padrinho.nome}
                      </Link>
                      <div className="pt-padrinho-kicker">
                        cuida de {g.calouros.length} calouro{g.calouros.length > 1 ? "s" : ""}
                      </div>
                    </div>
                  </div>
                  <TurnoTag turno={g.padrinho.turno} />
                </div>
                <div className="pt-dupla-body">
                  <div className="pt-dupla-linha" aria-hidden="true" />
                  <div className="pt-dupla-calouros">
                    {g.calouros.map((c) => (
                      <div key={c.id} className="pt-dupla-calouro">
                        <Avatar nome={c.nome} size={30} tone="white" />
                        {c.nome}
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            ))}
          </div>
        </>
      )}
    </AppShell>
  );
}
