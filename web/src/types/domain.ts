export type StatusACG = "apto" | "alerta" | "inapto_amarelo" | "inapto_vermelho";

export type Turno = "Manhã" | "Noite" | "";

export type ScenarioId = "inicio" | "andamento" | "fechamento";

export interface Padrinho {
  id: number;
  nome: string;
  matricula: string;
  email: string;
  telefone: string;
  turno: Turno;
  genero?: string | null;
  idade?: number | null;
  cidade_bh?: number;
  bolsista?: number;
  trabalha?: number;
  periodo?: string | null;
  status: StatusACG;
  amarelos: number;
  vermelhos: number;
}

export interface Calouro {
  id: number;
  nome: string;
  telefone: string;
  turno: Turno;
  genero?: string;
}

export interface MatchGrupo {
  padrinho: Padrinho;
  calouros: Calouro[];
}

export interface Reuniao {
  id: number;
  data: string;
  tema: string;
  descricao: string;
  presentes: number;
  justificadas: number;
  ausentes: number;
}

export interface PresencaItem {
  id: number;
  nome: string;
  matricula: string;
  presente: number;
  justificada: number;
}

export type SituacaoTema = "pendente" | "entregue" | "atraso" | "nao_entregue";

export interface TemaItem {
  id: number;
  titulo: string;
  data_aviso: string;
  data_limite: string;
  data_entrega?: string | null;
  situacao: SituacaoTema;
  responsaveis: { id: number; nome: string }[];
}

export interface Advertencia {
  id: number;
  padrinho_id: number;
  padrinho_nome: string;
  tipo: "amarelo" | "vermelho";
  origem: "falta" | "atraso_tema" | "nao_entrega" | "manual";
  motivo: string;
  data: string;
}

export interface LogAcao {
  id: number;
  data: string;
  acao: string;
  descricao: string;
  ip: string;
}

export interface ConfigSemestre {
  semestre: string;
  professor_coordenador: string;
  programa: string;
  instituicao: string;
  total_reunioes: number;
  data_inicio: string;
  data_fim: string;
  coordenadora_geral: string;
  coordenadores: string[];
}

export interface ScenarioBundle {
  id: ScenarioId;
  titulo: string;
  badge: string;
  resumo: string;
  config: ConfigSemestre;
  padrinhos: Padrinho[];
  calourosSoltos: Calouro[];
  matches: MatchGrupo[];
  reunioes: Reuniao[];
  presencasPorReuniao: Record<number, PresencaItem[]>;
  temas: TemaItem[];
  advertencias: Advertencia[];
  logs: LogAcao[];
}
