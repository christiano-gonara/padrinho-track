import { DependencyList, useCallback, useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import { apiFetch } from "../services/api";

/** Carrega dados de um endpoint REST apenas quando o aplicativo está no modo live. */
export function useLiveData<T>(endpoint: string | null, deps: DependencyList = []) {
  const { mode } = useApp();
  const [live, setLive] = useState<T | null>(null);

  const reload = useCallback(() => {
    if (mode !== "live" || !endpoint) {
      setLive(null);
      return;
    }
    apiFetch<T>(endpoint).then(setLive).catch(() => setLive(null));
  }, [mode, endpoint]);

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reload, ...deps]);

  return { live, reload, isLive: mode === "live" };
}
