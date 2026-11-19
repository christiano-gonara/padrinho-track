import { HashRouter, BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import { AdvertenciasPage } from "./pages/AdvertenciasPage";
import { CalourosPage } from "./pages/CalourosPage";
import { CriarContaPage } from "./pages/CriarContaPage";
import { ConfigPage } from "./pages/ConfigPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InicioSemestrePage } from "./pages/InicioSemestrePage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { LogsPage } from "./pages/LogsPage";
import { MatchPage } from "./pages/MatchPage";
import { PadrinhoDetalhePage } from "./pages/PadrinhoDetalhePage";
import { PadrinhosPage } from "./pages/PadrinhosPage";
import { PresencasPage } from "./pages/PresencasPage";
import { RelatoriosPage } from "./pages/RelatoriosPage";
import { ReunioesPage } from "./pages/ReunioesPage";
import { TemasPage } from "./pages/TemasPage";

function RouterSwitch() {
  const isPages = import.meta.env.BASE_URL !== "/";
  const Router = isPages ? HashRouter : BrowserRouter;

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/criar-conta" element={<CriarContaPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/padrinhos" element={<PadrinhosPage />} />
        <Route path="/padrinhos/:id" element={<PadrinhoDetalhePage />} />
        <Route path="/calouros" element={<CalourosPage />} />
        <Route path="/reunioes" element={<ReunioesPage />} />
        <Route path="/presencas/:id" element={<PresencasPage />} />
        <Route path="/temas" element={<TemasPage />} />
        <Route path="/inicio" element={<InicioSemestrePage />} />
        <Route path="/match" element={<MatchPage />} />
        <Route path="/advertencias" element={<AdvertenciasPage />} />
        <Route path="/relatorio" element={<RelatoriosPage />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default function App() {
  return (
    <AppProvider>
      <RouterSwitch />
    </AppProvider>
  );
}
