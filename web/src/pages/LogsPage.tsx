import { History } from "lucide-react";
import { AppShell } from "../components/layout/AppShell";
import { ToneBadge } from "../components/ui/StatusBadge";
import { useApp } from "../context/AppContext";
import { useLiveData } from "../hooks/useLiveData";
import { LogAcao } from "../types/domain";

export function LogsPage() {
  const { scenario } = useApp();
  const { live } = useLiveData<{ logs: LogAcao[] }>("/api/logs");

  const logs = live?.logs ?? scenario.logs;

  return (
    <AppShell title="Histórico de ações">
      <div className="pt-page-head">
        <div>
          <h1 className="pt-page-title">Histórico de ações</h1>
          <p className="pt-page-subtitle">Tudo o que foi feito no sistema, do mais novo pro mais antigo.</p>
        </div>
      </div>

      <div className="pt-card pt-card-flat">
        <div className="pt-card-header">
          <div className="pt-card-header-title">
            <div className="pt-card-header-icon"><History size={16} /></div>
            <h2 className="pt-card-title">Histórico de ações</h2>
          </div>
          <span className="pt-muted" style={{ fontSize: 12.5 }}>{logs.length} registros</span>
        </div>

        <div className="pt-table-wrap">
          <table className="pt-table">
            <thead>
              <tr>
                <th>Data / Hora</th>
                <th>Ação</th>
                <th>Descrição</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td className="pt-mono pt-muted">{l.data}</td>
                  <td><ToneBadge tone="brand">{l.acao}</ToneBadge></td>
                  <td className="pt-muted">{l.descricao}</td>
                  <td className="pt-mono pt-muted">{l.ip || "—"}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={4}>
                    <div className="pt-empty">
                      <div className="pt-empty-icon"><History size={20} /></div>
                      <strong>Nenhum log registrado</strong>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
