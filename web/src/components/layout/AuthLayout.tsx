import { Check } from "lucide-react";
import { Link } from "react-router-dom";
import "../../styles/pages/Auth.css";

const LACO = "M10 22 C5 22, 5 12, 10 12 C14 12, 16 20, 22 20 C27 20, 27 10, 22 10 C18 10, 16 18, 10 18";

/** Tela dividida: painel azul da marca à esquerda e formulário à direita */
export function AuthLayout({
  titulo,
  texto,
  itens,
  children,
}: {
  titulo: string;
  texto: string;
  itens: string[];
  children: React.ReactNode;
}) {
  return (
    <div className="pt-auth">
      <aside className="pt-auth-brand">
        <div className="pt-auth-brilho" aria-hidden="true" />
        <svg className="pt-auth-laco" width="560" height="560" viewBox="2 2 28 28" fill="none" aria-hidden="true">
          <path d={LACO} stroke="#ffffff" strokeWidth="2.4" strokeLinecap="round" />
        </svg>
        <Link to="/" className="pt-auth-logo">
          <span aria-hidden="true">
            <svg width="26" height="26" viewBox="2 2 28 28" fill="none">
              <path d={LACO} stroke="#ffffff" strokeWidth="3" strokeLinecap="round" />
            </svg>
          </span>
          Padrinho <em>Track</em>
        </Link>
        <div className="pt-auth-copy">
          <h2>{titulo}</h2>
          <p>{texto}</p>
          <ul>
            {itens.map((i) => (
              <li key={i}>
                <span aria-hidden="true">
                  <Check size={15} strokeWidth={2.6} />
                </span>
                {i}
              </li>
            ))}
          </ul>
        </div>
        <div className="pt-auth-rodape">Mentoria Acadêmica · Engenharia de Software · PUC Minas</div>
      </aside>
      <main className="pt-auth-main">
        <div className="pt-auth-form">{children}</div>
      </main>
    </div>
  );
}
