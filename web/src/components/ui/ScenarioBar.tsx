import { Layers } from "lucide-react";
import { useApp } from "../../context/AppContext";
import { getScenarioList } from "../../data/scenarios";
import "./ScenarioBar.css";

export function ScenarioBar() {
  const { mode, scenarioId, scenario, setScenarioId } = useApp();
  const list = getScenarioList();

  if (mode === "live") {
    return null;
  }

  return (
    <section className="pt-scenario-bar" aria-label="Seletor de cenários de uso">
      <div className="pt-scenario-info">
        <span className="pt-scenario-kicker">
          <Layers size={13} />
          Cenário de uso ativo · {scenario.badge}
        </span>
        <p className="pt-scenario-desc">{scenario.resumo}</p>
      </div>
      <div className="pt-scenario-pills">
        {list.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`pt-scenario-btn ${scenarioId === item.id ? "is-active" : ""}`}
            onClick={() => setScenarioId(item.id)}
          >
            {item.titulo}
          </button>
        ))}
      </div>
    </section>
  );
}
