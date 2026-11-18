import { useNavigate } from "react-router-dom";
import "./Charts.css";

export function SemesterFlowDiagram({
  padrinhosCount,
  matchesCount,
  reunioesCount,
  temasCount,
  aptosCount,
}: {
  padrinhosCount: number;
  matchesCount: number;
  reunioesCount: number;
  temasCount: number;
  aptosCount: number;
}) {
  const navigate = useNavigate();

  const steps = [
    {
      num: 1,
      stat: `${padrinhosCount} padrinhos`,
      title: "Inscrições & Importação",
      desc: "Cadastro manual ou importação direta das planilhas do Google Forms.",
      to: "/inicio",
    },
    {
      num: 2,
      stat: `${matchesCount} pares`,
      title: "Match de Afinidade",
      desc: "Cruzamento por turno, gênero e perfil gerando a lista de contatos.",
      to: "/match",
    },
    {
      num: 3,
      stat: `${reunioesCount} reun. · ${temasCount} temas`,
      title: "Reuniões & Temas",
      desc: "Presenças e prazos alimentam automaticamente as advertências ACG.",
      to: "/reunioes",
    },
    {
      num: 4,
      stat: `${aptosCount} aptos`,
      title: "Relatório & Certificados",
      desc: "Emissão da lista de Aptidão ACG, Resumo do Semestre e ZIP em PDF.",
      to: "/relatorio",
    },
  ];

  return (
    <div className="pt-flow-grid">
      {steps.map((s) => (
        <button key={s.num} type="button" className="pt-flow-step" onClick={() => navigate(s.to)}>
          <div className="pt-flow-top">
            <span className="pt-flow-num">{s.num}</span>
            <span className="pt-flow-stat">{s.stat}</span>
          </div>
          <h3 className="pt-flow-title">{s.title}</h3>
          <p className="pt-flow-desc">{s.desc}</p>
        </button>
      ))}
    </div>
  );
}
