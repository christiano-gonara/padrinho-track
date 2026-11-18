import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { DEFAULT_SCENARIO, SCENARIOS } from "../data/scenarios";
import { api } from "../services/api";
import {
  Advertencia,
  Calouro,
  ConfigSemestre,
  LogAcao,
  MatchGrupo,
  Padrinho,
  PresencaItem,
  Reuniao,
  ScenarioBundle,
  ScenarioId,
  TemaItem,
} from "../types/domain";

export type AppMode = "demo" | "live";

interface ToastItem {
  id: number;
  text: string;
  tone: "info" | "success" | "error";
}

interface AppContextValue {
  mode: AppMode;
  authenticated: boolean;
  checkingAuth: boolean;
  scenarioId: ScenarioId;
  scenario: ScenarioBundle;
  setScenarioId: (id: ScenarioId) => void;
  setMode: (mode: AppMode) => void;
  loginLive: (username: string, password: string) => Promise<void>;
  logoutLive: () => Promise<void>;
  notify: (text: string, tone?: "info" | "success" | "error") => void;
  // Mutações interativas no modo Demo (cenários editáveis na sessão)
  addPadrinhoDemo: (p: { nome: string; matricula: string; email: string; telefone: string; turno: "Manhã" | "Noite" | "" }) => void;
  runMatchDemo: () => void;
  addReuniaoDemo: (r: { data: string; tema: string; descricao: string }) => void;
  savePresencasDemo: (reuniaoId: number, presentesIds: number[], justificadasIds: number[]) => void;
  addTemaDemo: (t: { titulo: string; data_aviso: string; data_limite: string; padrinho_ids: number[] }) => void;
  markTemaDemo: (temaId: number, situacao: "entregue" | "atraso" | "nao_entregue") => void;
  addAdvertenciaDemo: (a: { padrinho_id: number; tipo: "amarelo" | "vermelho"; motivo: string }) => void;
  removeAdvertenciaDemo: (id: number) => void;
  updateConfigDemo: (cfg: ConfigSemestre) => void;
  clearLogsDemo: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

function cloneBundle(b: ScenarioBundle): ScenarioBundle {
  return JSON.parse(JSON.stringify(b)) as ScenarioBundle;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<AppMode>("demo");
  const [authenticated, setAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [scenarioId, setScenarioIdState] = useState<ScenarioId>(DEFAULT_SCENARIO);
  const [bundles, setBundles] = useState<Record<ScenarioId, ScenarioBundle>>(() => ({
    inicio: cloneBundle(SCENARIOS.inicio),
    andamento: cloneBundle(SCENARIOS.andamento),
    fechamento: cloneBundle(SCENARIOS.fechamento),
  }));
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const notify = useCallback((text: string, tone: "info" | "success" | "error" = "info") => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setToasts((prev) => [...prev, { id, text, tone }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3600);
  }, []);

  useEffect(() => {
    let active = true;
    api
      .authMe()
      .then((res) => {
        if (!active) return;
        setAuthenticated(res.authenticated);
        if (res.authenticated) {
          setMode("live");
        }
      })
      .catch(() => {
        // Sem backend Flask (ex: GitHub Pages): permanece em modo Demonstração
      })
      .finally(() => {
        if (active) setCheckingAuth(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const setScenarioId = useCallback(
    (id: ScenarioId) => {
      setScenarioIdState(id);
      setMode("demo");
      notify(`Exibindo ${SCENARIOS[id].titulo}`, "info");
    },
    [notify]
  );

  const loginLive = useCallback(
    async (username: string, password: string) => {
      await api.login(username, password);
      setAuthenticated(true);
      setMode("live");
      notify("Sessão iniciada no servidor Flask.", "success");
    },
    [notify]
  );

  const logoutLive = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // ignora em modo estático
    }
    setAuthenticated(false);
    setMode("demo");
    notify("Sessão encerrada. Modo de cenários ativo.", "info");
  }, [notify]);

  const mutateScenario = useCallback(
    (updater: (draft: ScenarioBundle) => void) => {
      setBundles((prev) => {
        const next = cloneBundle(prev[scenarioId]);
        updater(next);
        return { ...prev, [scenarioId]: next };
      });
    },
    [scenarioId]
  );

  const addPadrinhoDemo = useCallback(
    (p: { nome: string; matricula: string; email: string; telefone: string; turno: "Manhã" | "Noite" | "" }) => {
      mutateScenario((draft) => {
        const nextId = Math.max(0, ...draft.padrinhos.map((x) => x.id)) + 1;
        const novo: Padrinho = {
          id: nextId,
          nome: p.nome,
          matricula: p.matricula,
          email: p.email,
          telefone: p.telefone,
          turno: p.turno,
          status: "apto",
          amarelos: 0,
          vermelhos: 0,
        };
        draft.padrinhos.push(novo);
        draft.logs.unshift({
          id: Date.now(),
          data: "Agora",
          acao: "CADASTRO_PADRINHO",
          descricao: `Padrinho '${p.nome}' cadastrado no cenário.`,
          ip: "demo",
        });
      });
      notify("Padrinho adicionado ao cenário.", "success");
    },
    [mutateScenario, notify]
  );

  const runMatchDemo = useCallback(() => {
    mutateScenario((draft) => {
      const grupos: MatchGrupo[] = draft.padrinhos.map((padrinho) => ({
        padrinho,
        calouros: [],
      }));
      if (grupos.length > 0) {
        draft.calourosSoltos.forEach((calouro: Calouro, idx: number) => {
          const mesmos = grupos.filter((g) => !calouro.turno || g.padrinho.turno === calouro.turno);
          const alvo = (mesmos.length > 0 ? mesmos : grupos)[idx % (mesmos.length || grupos.length)];
          alvo.calouros.push(calouro);
        });
      }
      draft.matches = grupos.filter((g) => g.calouros.length > 0);
      draft.logs.unshift({
        id: Date.now(),
        data: "Agora",
        acao: "MATCH_GERADO",
        descricao: `${draft.calourosSoltos.length} calouros distribuídos entre padrinhos.`,
        ip: "demo",
      });
    });
    notify("Match executado no cenário atual.", "success");
  }, [mutateScenario, notify]);

  const addReuniaoDemo = useCallback(
    (r: { data: string; tema: string; descricao: string }) => {
      mutateScenario((draft) => {
        const nextId = Math.max(0, ...draft.reunioes.map((x) => x.id)) + 1;
        const nova: Reuniao = {
          id: nextId,
          data: r.data,
          tema: r.tema || "Reunião",
          descricao: r.descricao,
          presentes: 0,
          justificadas: 0,
          ausentes: 0,
        };
        draft.reunioes.unshift(nova);
        draft.presencasPorReuniao[nextId] = draft.padrinhos.map((p) => ({
          id: p.id,
          nome: p.nome,
          matricula: p.matricula,
          presente: 0,
          justificada: 0,
        }));
      });
      notify("Reunião criada no cenário.", "success");
    },
    [mutateScenario, notify]
  );

  const savePresencasDemo = useCallback(
    (reuniaoId: number, presentesIds: number[], justificadasIds: number[]) => {
      mutateScenario((draft) => {
        const presSet = new Set(presentesIds);
        const justSet = new Set(justificadasIds);
        const lista: PresencaItem[] = draft.padrinhos.map((p) => ({
          id: p.id,
          nome: p.nome,
          matricula: p.matricula,
          presente: presSet.has(p.id) ? 1 : 0,
          justificada: justSet.has(p.id) ? 1 : 0,
        }));
        draft.presencasPorReuniao[reuniaoId] = lista;
        const reuniao = draft.reunioes.find((r) => r.id === reuniaoId);
        if (reuniao) {
          reuniao.presentes = lista.filter((x) => x.presente === 1).length;
          reuniao.justificadas = lista.filter((x) => x.presente === 0 && x.justificada === 1).length;
          reuniao.ausentes = lista.filter((x) => x.presente === 0 && x.justificada === 0).length;
        }
        draft.logs.unshift({
          id: Date.now(),
          data: "Agora",
          acao: "LANCAMENTO_PRESENCA",
          descricao: `Presenças atualizadas na reunião #${reuniaoId}.`,
          ip: "demo",
        });
      });
      notify("Presenças salvas no cenário.", "success");
    },
    [mutateScenario, notify]
  );

  const addTemaDemo = useCallback(
    (t: { titulo: string; data_aviso: string; data_limite: string; padrinho_ids: number[] }) => {
      mutateScenario((draft) => {
        const nextId = Math.max(0, ...draft.temas.map((x) => x.id)) + 1;
        const responsaveis = draft.padrinhos
          .filter((p) => t.padrinho_ids.includes(p.id))
          .map((p) => ({ id: p.id, nome: p.nome }));
        const novo: TemaItem = {
          id: nextId,
          titulo: t.titulo,
          data_aviso: t.data_aviso,
          data_limite: t.data_limite,
          situacao: "pendente",
          responsaveis,
        };
        draft.temas.push(novo);
      });
      notify("Tema criado no cenário.", "success");
    },
    [mutateScenario, notify]
  );

  const markTemaDemo = useCallback(
    (temaId: number, situacao: "entregue" | "atraso" | "nao_entregue") => {
      mutateScenario((draft) => {
        const tema = draft.temas.find((t) => t.id === temaId);
        if (tema) {
          tema.situacao = situacao;
          tema.data_entrega = new Date().toISOString().slice(0, 10);
        }
      });
      notify("Status do tema atualizado.", "success");
    },
    [mutateScenario, notify]
  );

  const addAdvertenciaDemo = useCallback(
    (a: { padrinho_id: number; tipo: "amarelo" | "vermelho"; motivo: string }) => {
      mutateScenario((draft) => {
        const padrinho = draft.padrinhos.find((p) => p.id === a.padrinho_id);
        if (!padrinho) return;
        const nova: Advertencia = {
          id: Date.now(),
          padrinho_id: padrinho.id,
          padrinho_nome: padrinho.nome,
          tipo: a.tipo,
          origem: "manual",
          motivo: a.motivo,
          data: new Date().toISOString().slice(0, 10),
        };
        draft.advertencias.unshift(nova);
        if (a.tipo === "vermelho") {
          padrinho.vermelhos += 1;
          padrinho.status = "inapto_vermelho";
        } else {
          padrinho.amarelos += 1;
          if (padrinho.vermelhos === 0) {
            const lim = Math.max(1, draft.reunioes.length);
            padrinho.status = padrinho.amarelos >= lim ? "inapto_amarelo" : "alerta";
          }
        }
      });
      notify("Advertência registrada no cenário.", "error");
    },
    [mutateScenario, notify]
  );

  const removeAdvertenciaDemo = useCallback(
    (id: number) => {
      mutateScenario((draft) => {
        draft.advertencias = draft.advertencias.filter((x) => x.id !== id);
      });
      notify("Advertência removida.", "success");
    },
    [mutateScenario, notify]
  );

  const updateConfigDemo = useCallback(
    (cfg: ConfigSemestre) => {
      mutateScenario((draft) => {
        draft.config = cfg;
        const log: LogAcao = {
          id: Date.now(),
          data: "Agora",
          acao: "ALTERACAO_CONFIG",
          descricao: `Configurações do semestre ${cfg.semestre} salvas.`,
          ip: "demo",
        };
        draft.logs.unshift(log);
      });
      notify("Configurações atualizadas no cenário.", "success");
    },
    [mutateScenario, notify]
  );

  const clearLogsDemo = useCallback(() => {
    mutateScenario((draft) => {
      draft.logs = [];
    });
    notify("Logs limpos no cenário.", "success");
  }, [mutateScenario, notify]);

  return (
    <AppContext.Provider
      value={{
        mode,
        authenticated,
        checkingAuth,
        scenarioId,
        scenario: bundles[scenarioId],
        setScenarioId,
        setMode,
        loginLive,
        logoutLive,
        notify,
        addPadrinhoDemo,
        runMatchDemo,
        addReuniaoDemo,
        savePresencasDemo,
        addTemaDemo,
        markTemaDemo,
        addAdvertenciaDemo,
        removeAdvertenciaDemo,
        updateConfigDemo,
        clearLogsDemo,
      }}
    >
      {children}
      {toasts.length > 0 && (
        <div
          style={{
            position: "fixed",
            right: 20,
            bottom: 20,
            zIndex: 400,
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
        >
          {toasts.map((t) => (
            <div
              key={t.id}
              style={{
                padding: "11px 16px",
                borderRadius: 12,
                fontSize: 13,
                fontWeight: 600,
                color: "#fff",
                boxShadow: "0 12px 28px -10px rgba(15,23,42,0.35)",
                background:
                  t.tone === "success"
                    ? "#059669"
                    : t.tone === "error"
                    ? "#dc2626"
                    : "var(--pt-brand)",
              }}
            >
              {t.text}
            </div>
          ))}
        </div>
      )}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp deve ser usado dentro de AppProvider");
  return ctx;
}
