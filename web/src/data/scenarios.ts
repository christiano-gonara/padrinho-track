import rawData from "./scenarios.json";
import {
  Advertencia,
  Calouro,
  Padrinho,
  PresencaItem,
  Reuniao,
  ScenarioBundle,
  ScenarioId,
  StatusACG,
  TemaItem,
  Turno,
} from "../types/domain";

interface StatusOverride {
  status: StatusACG;
  amarelos: number;
  vermelhos: number;
}

interface RawScenario {
  id: ScenarioId;
  titulo: string;
  badge: string;
  resumo: string;
  hasMatches: boolean;
  statusOverrides: Record<string, StatusOverride>;
  reunioes: (Reuniao & { ausentesIds: number[]; justificadasIds: number[] })[];
  temas: TemaItem[];
  advertencias: Advertencia[];
  logs: ScenarioBundle["logs"];
}

function buildPadrinhos(overrides: Record<string, StatusOverride>): Padrinho[] {
  return rawData.padrinhosBase.map((base) => {
    const ov = overrides[String(base.id)];
    return {
      ...base,
      turno: base.turno as Turno,
      status: ov ? ov.status : "apto",
      amarelos: ov ? ov.amarelos : 0,
      vermelhos: ov ? ov.vermelhos : 0,
    };
  });
}

function buildMatches(padrinhos: Padrinho[]) {
  const calouros = rawData.calouros as Calouro[];
  return rawData.matchPairs.map(([pIdx, calIdxs]) => ({
    padrinho: padrinhos[pIdx as number],
    calouros: (calIdxs as number[]).map((idx) => calouros[idx]),
  }));
}

function buildScenario(raw: RawScenario): ScenarioBundle {
  const padrinhos = buildPadrinhos(raw.statusOverrides);
  const presencasPorReuniao: Record<number, PresencaItem[]> = {};

  const reunioes = raw.reunioes.map(({ ausentesIds, justificadasIds, ...reuniao }) => {
    const ausentesSet = new Set<number>(ausentesIds);
    const justificadasSet = new Set<number>(justificadasIds);
    presencasPorReuniao[reuniao.id] = padrinhos.map((p) => ({
      id: p.id,
      nome: p.nome,
      matricula: p.matricula,
      presente: ausentesSet.has(p.id) ? 0 : 1,
      justificada: justificadasSet.has(p.id) ? 1 : 0,
    }));
    return reuniao;
  });

  return {
    id: raw.id,
    titulo: raw.titulo,
    badge: raw.badge,
    resumo: raw.resumo,
    config: rawData.config,
    padrinhos,
    calourosSoltos: rawData.calouros as Calouro[],
    matches: raw.hasMatches ? buildMatches(padrinhos) : [],
    reunioes,
    presencasPorReuniao,
    temas: raw.temas,
    advertencias: raw.advertencias,
    logs: raw.logs,
  };
}

const rawScenarios = rawData.scenarios as unknown as Record<ScenarioId, RawScenario>;

export const SCENARIOS: Record<ScenarioId, ScenarioBundle> = {
  inicio: buildScenario(rawScenarios.inicio),
  andamento: buildScenario(rawScenarios.andamento),
  fechamento: buildScenario(rawScenarios.fechamento),
};

export function getScenarioList(): ScenarioBundle[] {
  return [SCENARIOS.inicio, SCENARIOS.andamento, SCENARIOS.fechamento];
}

export function abreviarNome(nome: string): string {
  const partes = nome.trim().split(/\s+/);
  if (partes.length <= 2) return nome;
  const preps = new Set(["de", "da", "do", "dos", "das", "e"]);
  let idx = partes.length - 1;
  while (idx > 1 && preps.has(partes[idx].toLowerCase())) {
    idx -= 1;
  }
  return `${partes[0]} ${partes[idx]}`;
}

export function formatarDataBr(iso?: string | null): string {
  if (!iso) return "—";
  const parts = iso.split("-");
  if (parts.length !== 3) return iso;
  return `${parts[2]}/${parts[1]}`;
}

export const DEFAULT_SCENARIO: ScenarioId = "fechamento";
