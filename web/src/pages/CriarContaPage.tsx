import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, Eye, EyeOff, KeyRound, Lock, Mail, User, Users } from "lucide-react";
import { AuthLayout } from "../components/layout/AuthLayout";
import { useApp } from "../context/AppContext";

export function CriarContaPage() {
  const { notify } = useApp();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [funcao, setFuncao] = useState("Coordenador(a) de alunos");
  const [senha, setSenha] = useState("");
  const [senha2, setSenha2] = useState("");
  const [codigo, setCodigo] = useState("");
  const [aceite, setAceite] = useState(false);
  const [mostrar, setMostrar] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    if (senha.length < 8) return setErro("A senha precisa ter pelo menos 8 caracteres.");
    if (senha !== senha2) return setErro("As duas senhas estão diferentes.");
    if (!aceite) return setErro("Marque a caixinha de cuidado com os dados pra continuar.");
    // O servidor ainda não cria contas sozinho: por enquanto quem cadastra é a coordenação geral.
    notify("Pedido anotado! Por enquanto a coordenação geral é quem libera o acesso.", "info");
  }

  return (
    <AuthLayout
      titulo="Bem-vindo à coordenação."
      texto="Em poucos minutos você já está acompanhando os padrinhos e calouros do semestre."
      itens={[
        "Acesso só pra quem tem convite da coordenação",
        "Seu nome sai certinho no certificado",
        "Dá pra mudar a senha quando quiser",
      ]}
    >
      <Link to="/login" className="pt-back-link">
        <ArrowLeft size={16} /> Voltar pro login
      </Link>
      <h1 style={{ marginTop: 8 }}>Criar sua conta</h1>
      <p className="pt-auth-lede">
        Pra quem faz parte da coordenação. Você vai precisar do código que a coordenação geral te passou.
      </p>

      {erro && (
        <div className="pt-alert pt-alert-danger" style={{ marginTop: 20 }} role="alert">
          <span>{erro}</span>
        </div>
      )}

      <form onSubmit={onSubmit} className="pt-auth-campos">
        <div className="pt-auth-campo">
          <label className="pt-label" htmlFor="cc-nome">Nome completo</label>
          <div className="pt-auth-input">
            <User size={18} aria-hidden="true" />
            <input id="cc-nome" autoComplete="name" placeholder="Como aparece no certificado" value={nome} onChange={(e) => setNome(e.target.value)} required />
          </div>
        </div>

        <div className="pt-auth-campo">
          <label className="pt-label" htmlFor="cc-email">E-mail da PUC</label>
          <div className="pt-auth-input">
            <Mail size={18} aria-hidden="true" />
            <input id="cc-email" type="email" autoComplete="email" placeholder="seunome@sga.pucminas.br" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
        </div>

        <div className="pt-auth-campo">
          <label className="pt-label" htmlFor="cc-funcao">Sua função</label>
          <div className="pt-auth-input">
            <Users size={18} aria-hidden="true" />
            <select id="cc-funcao" value={funcao} onChange={(e) => setFuncao(e.target.value)}>
              <option>Coordenador(a) de alunos</option>
              <option>Coordenação geral</option>
              <option>Professor(a) responsável</option>
            </select>
          </div>
        </div>

        <div className="pt-auth-dois">
          <div className="pt-auth-campo">
            <label className="pt-label" htmlFor="cc-senha">Senha</label>
            <div className="pt-auth-input">
              <Lock size={18} aria-hidden="true" />
              <input id="cc-senha" type={mostrar ? "text" : "password"} autoComplete="new-password" placeholder="Mínimo 8 caracteres" value={senha} onChange={(e) => setSenha(e.target.value)} required />
              <button type="button" className="pt-auth-olho" aria-label={mostrar ? "Esconder senhas" : "Mostrar senhas"} onClick={() => setMostrar((v) => !v)}>
                {mostrar ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <div className="pt-auth-campo">
            <label className="pt-label" htmlFor="cc-senha2">Repita a senha</label>
            <div className="pt-auth-input">
              <Lock size={18} aria-hidden="true" />
              <input id="cc-senha2" type={mostrar ? "text" : "password"} autoComplete="new-password" placeholder="Igual à de cima" value={senha2} onChange={(e) => setSenha2(e.target.value)} required />
            </div>
          </div>
        </div>

        <div className="pt-auth-campo">
          <label className="pt-label" htmlFor="cc-codigo">Código de convite</label>
          <div className="pt-auth-input">
            <KeyRound size={18} aria-hidden="true" />
            <input id="cc-codigo" autoComplete="off" placeholder="Ex.: PUC-2026-XXXX" value={codigo} onChange={(e) => setCodigo(e.target.value)} required />
          </div>
          <p style={{ margin: "8px 0 0", fontSize: 14, color: "#475569" }}>Não tem o código? Peça pra coordenação geral do programa.</p>
        </div>

        <label className="pt-auth-check">
          <input type="checkbox" checked={aceite} onChange={(e) => setAceite(e.target.checked)} />
          Entendo que vou ver dados de padrinhos e calouros e que eles são só pro programa.
        </label>

        <button type="submit" className="pt-btn pt-btn-primary pt-auth-btn">
          Criar conta <ArrowRight size={18} />
        </button>
      </form>

      <p className="pt-auth-alt">
        Já tem conta? <Link to="/login">Entrar</Link>
      </p>
    </AuthLayout>
  );
}
