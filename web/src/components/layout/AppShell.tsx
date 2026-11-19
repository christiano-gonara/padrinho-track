import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  BookOpen,
  CalendarDays,
  FileText,
  GraduationCap,
  History,
  Home,
  Link2,
  LogIn,
  LogOut,
  Menu,
  PlayCircle,
  Settings,
  SquareStack,
  Users,
  X,
} from "lucide-react";
import { useApp } from "../../context/AppContext";
import { getScenarioList } from "../../data/scenarios";
import "../../styles/layout/AppShell.css";

/** Menu agrupado pelo momento do semestre */
const GRUPOS = [
  {
    titulo: "O semestre",
    itens: [
      { to: "/dashboard", label: "Painel", icon: Home },
      { to: "/inicio", label: "Começar o semestre", icon: PlayCircle },
      { to: "/match", label: "Duplas", icon: Link2 },
    ],
  },
  {
    titulo: "Acompanhamento",
    itens: [
      { to: "/reunioes", label: "Reuniões", icon: CalendarDays },
      { to: "/temas", label: "Temas", icon: BookOpen },
      { to: "/advertencias", label: "Cartões", icon: SquareStack },
    ],
  },
  {
    titulo: "Pessoas",
    itens: [
      { to: "/padrinhos", label: "Padrinhos", icon: Users },
      { to: "/calouros", label: "Calouros", icon: GraduationCap },
    ],
  },
  {
    titulo: "Fechamento",
    itens: [{ to: "/relatorio", label: "Relatórios e certificados", icon: FileText }],
  },
];

const NOME_CURTO: Record<string, string> = {
  inicio: "Começo",
  andamento: "Meio",
  fechamento: "Fechamento",
};

export function AppShell({ title, children }: { title: string; children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { mode, authenticated, logoutLive, scenarioId, setScenarioId, scenario } = useApp();
  const navigate = useNavigate();
  const fechar = () => setMobileOpen(false);

  return (
    <div className="pt-app">
      <div className={`pt-sidebar-backdrop ${mobileOpen ? "is-open" : ""}`} onClick={fechar} />

      <aside className={`pt-sidebar ${mobileOpen ? "is-mobile-open" : ""}`} aria-label="Menu">
        <div className="pt-sidebar-top">
          <NavLink to="/" className="pt-sidebar-brand" onClick={fechar}>
            <span className="pt-sidebar-tile" aria-hidden="true">
              <svg width="22" height="22" viewBox="2 2 28 28" fill="none">
                <path
                  d="M10 22 C5 22, 5 12, 10 12 C14 12, 16 20, 22 20 C27 20, 27 10, 22 10 C18 10, 16 18, 10 18"
                  stroke="#ffffff"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
            </span>
            <span className="pt-sidebar-name">
              Padrinho <span>Track</span>
            </span>
          </NavLink>
          <button type="button" className="pt-sidebar-close" onClick={fechar} aria-label="Fechar menu">
            <X size={20} />
          </button>
        </div>

        <nav className="pt-sidebar-nav" aria-label="Navegação principal">
          {GRUPOS.map((g) => (
            <div key={g.titulo}>
              <p className="pt-sidebar-section">{g.titulo}</p>
              {g.itens.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) => `pt-nav-item ${isActive ? "is-active" : ""}`}
                    onClick={fechar}
                  >
                    <Icon size={19} />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="pt-sidebar-bottom">
          <NavLink to="/config" className={({ isActive }) => `pt-nav-item ${isActive ? "is-active" : ""}`} onClick={fechar}>
            <Settings size={19} />
            <span>Configurações</span>
          </NavLink>
          <NavLink to="/logs" className={({ isActive }) => `pt-nav-item ${isActive ? "is-active" : ""}`} onClick={fechar}>
            <History size={19} />
            <span>Histórico de ações</span>
          </NavLink>
          {authenticated && mode === "live" ? (
            <button
              type="button"
              className="pt-nav-item"
              onClick={async () => {
                await logoutLive();
                navigate("/");
              }}
            >
              <LogOut size={19} />
              <span>Sair</span>
            </button>
          ) : (
            <button type="button" className="pt-nav-item" onClick={() => navigate("/login")}>
              <LogIn size={19} />
              <span>Entrar</span>
            </button>
          )}
          <div className="pt-sidebar-org">
            <span className="pt-sidebar-org-tile">PUC</span>
            <span>
              <strong>Mentoria Acadêmica</strong>
              <small>Engenharia de Software</small>
            </span>
          </div>
        </div>
      </aside>

      <div className="pt-main">
        <header className="pt-topbar">
          <div className="pt-topbar-left">
            <button type="button" className="pt-mobile-btn" onClick={() => setMobileOpen(true)} aria-label="Abrir menu">
              <Menu size={20} />
            </button>
            <span className="pt-topbar-sem">Semestre {scenario.config.semestre}</span>
            <span className="pt-topbar-sep" aria-hidden="true">|</span>
            <span className="pt-topbar-page">{title}</span>
          </div>

          {mode === "live" ? (
            <span className="pt-topbar-live">Conectado ao servidor</span>
          ) : (
            <div className="pt-topbar-right">
              <span className="pt-topbar-hint">Dados de exemplo:</span>
              <div className="pt-seg" role="group" aria-label="Momento do semestre">
                {getScenarioList().map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className={scenarioId === s.id ? "is-on" : ""}
                    aria-pressed={scenarioId === s.id}
                    onClick={() => setScenarioId(s.id)}
                  >
                    {NOME_CURTO[s.id] ?? s.titulo}
                  </button>
                ))}
              </div>
            </div>
          )}
        </header>

        <main className="pt-content">{children}</main>
      </div>
    </div>
  );
}
