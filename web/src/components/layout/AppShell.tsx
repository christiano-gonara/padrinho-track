import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  BookOpen,
  CalendarDays,
  FileBarChart2,
  History,
  Home,
  LayoutDashboard,
  Link2,
  LogIn,
  LogOut,
  MapPin,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  UserCheck,
  Users,
  Video,
} from "lucide-react";
import { useApp } from "../../context/AppContext";
import { ScenarioBar } from "../ui/ScenarioBar";
import "./AppShell.css";

const MENU_PRINCIPAL = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/padrinhos", label: "Padrinhos", icon: UserCheck },
  { to: "/reunioes", label: "Reuniões", icon: Video },
  { to: "/temas", label: "Temas", icon: BookOpen },
  { to: "/calouros", label: "Calouros", icon: Users },
  { to: "/inicio", label: "Início do Semestre", icon: CalendarDays },
  { to: "/match", label: "Match", icon: Link2 },
];

const MENU_GESTAO = [
  { to: "/advertencias", label: "Advertências", icon: AlertTriangle },
  { to: "/relatorio", label: "Relatório", icon: FileBarChart2 },
  { to: "/config", label: "Configurações", icon: Settings },
  { to: "/logs", label: "Logs", icon: History },
];

export function AppShell({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { mode, authenticated, logoutLive } = useApp();
  const navigate = useNavigate();

  const base = import.meta.env.BASE_URL;

  return (
    <div className="pt-app">
      <div
        className={`pt-sidebar-backdrop ${mobileOpen ? "is-open" : ""}`}
        onClick={() => setMobileOpen(false)}
      />

      <aside className={`pt-sidebar ${collapsed ? "is-collapsed" : ""} ${mobileOpen ? "is-mobile-open" : ""}`}>
        <div className="pt-sidebar-logo">
          <NavLink
            to="/"
            style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0, flex: 1 }}
            onClick={() => setMobileOpen(false)}
          >
            <span className="pt-knot-tile">
              <img src={`${base}brand/padrinho-track-tile.svg`} alt="" />
            </span>
            {!collapsed && (
              <span className="pt-sidebar-logo-text">
                Padrinho <span>Track</span>
              </span>
            )}
          </NavLink>
          <button
            type="button"
            className="pt-sidebar-collapse-btn"
            onClick={() => setCollapsed((v) => !v)}
            aria-label="Alternar largura da barra lateral"
          >
            {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
        </div>

        <nav className="pt-sidebar-nav" aria-label="Navegação principal">
          {!collapsed && <p className="pt-sidebar-section">Menu</p>}
          {MENU_PRINCIPAL.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `pt-nav-item ${isActive ? "is-active" : ""}`}
                onClick={() => setMobileOpen(false)}
                title={item.label}
              >
                <Icon size={17} />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}

          {!collapsed && <p className="pt-sidebar-section">Gestão</p>}
          {MENU_GESTAO.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `pt-nav-item ${isActive ? "is-active" : ""}`}
                onClick={() => setMobileOpen(false)}
                title={item.label}
              >
                <Icon size={17} />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>

        <div className="pt-sidebar-footer">
          {!collapsed && (
            <div className="pt-sidebar-org">
              <div className="pt-sidebar-org-tile">PUC</div>
              <div className="pt-sidebar-org-text">
                <strong>PUC Minas</strong>
                <small>Eng. Software</small>
              </div>
            </div>
          )}

          <NavLink to="/" className="pt-nav-item" onClick={() => setMobileOpen(false)} title="Apresentação">
            <Home size={17} />
            {!collapsed && <span>Apresentação</span>}
          </NavLink>

          {authenticated && mode === "live" ? (
            <button
              type="button"
              className="pt-nav-item"
              style={{ border: "none", background: "transparent", width: "100%", textAlign: "left" }}
              onClick={async () => {
                await logoutLive();
                navigate("/");
              }}
            >
              <LogOut size={17} />
              {!collapsed && <span>Sair</span>}
            </button>
          ) : (
            <button
              type="button"
              className="pt-nav-item"
              style={{ border: "none", background: "transparent", width: "100%", textAlign: "left" }}
              onClick={() => navigate("/login")}
            >
              <LogIn size={17} />
              {!collapsed && <span>Login coordenação</span>}
            </button>
          )}
        </div>
      </aside>

      <div className="pt-main">
        <header className="pt-topbar">
          <div className="pt-topbar-left">
            <button
              type="button"
              className="pt-mobile-btn"
              onClick={() => setMobileOpen(true)}
              aria-label="Abrir menu"
            >
              <Menu size={18} />
            </button>
            <div className="pt-breadcrumb">
              <MapPin size={15} className="pt-breadcrumb-icon" />
              <span>{title}</span>
            </div>
          </div>

          <div className="pt-topbar-right">
            <span className="pt-course-pill">
              {mode === "live" ? "Servidor Flask ativo" : "Modo Cenários Interativos"}
            </span>
          </div>
        </header>

        <main className="pt-content">
          <ScenarioBar />
          {children}
        </main>
      </div>
    </div>
  );
}
