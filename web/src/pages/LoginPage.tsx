import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Eye, EyeOff, Lock, Mail, PlayCircle } from "lucide-react";
import { AuthLayout } from "../components/layout/AuthLayout";
import { useApp } from "../context/AppContext";

export function LoginPage() {
  const { loginLive, setScenarioId, notify } = useApp();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mostrar, setMostrar] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await loginLive(username, password);
      navigate("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message} Se você está na versão de demonstração, use o botão "Ver o sistema com dados de exemplo".`
          : "Não deu pra conectar ao servidor. Tente de novo em instantes."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      titulo="O apadrinhamento inteiro, num lugar só."
      texto="Duplas, reuniões, temas e certificados de ACG acompanhados sem planilha solta."
      itens={[
        "Veja quem está perto de perder a ACG antes que aconteça",
        "Lance a presença em poucos cliques",
        "Gere todos os certificados de uma vez",
      ]}
    >
      <h1>Que bom te ver de novo</h1>
      <p className="pt-auth-lede">Entre com seu e-mail da PUC pra acompanhar o semestre.</p>

      {error && (
        <div className="pt-alert pt-alert-danger" style={{ marginTop: 20 }} role="alert">
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={onSubmit} className="pt-auth-campos">
        <div className="pt-auth-campo">
          <label className="pt-label" htmlFor="login-usuario">E-mail</label>
          <div className="pt-auth-input">
            <Mail size={18} aria-hidden="true" />
            <input
              id="login-usuario"
              type="text"
              autoComplete="username"
              placeholder="seunome@sga.pucminas.br"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="pt-auth-campo">
          <div className="pt-auth-linha">
            <label className="pt-label" htmlFor="login-senha">Senha</label>
            <button
              type="button"
              className="pt-auth-link"
              style={{ border: 0, background: "transparent", padding: 0 }}
              onClick={() => notify("Peça pra coordenação geral trocar sua senha.", "info")}
            >
              Esqueci minha senha
            </button>
          </div>
          <div className="pt-auth-input">
            <Lock size={18} aria-hidden="true" />
            <input
              id="login-senha"
              type={mostrar ? "text" : "password"}
              autoComplete="current-password"
              placeholder="Sua senha"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              type="button"
              className="pt-auth-olho"
              aria-label={mostrar ? "Esconder senha" : "Mostrar senha"}
              onClick={() => setMostrar((v) => !v)}
            >
              {mostrar ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <button type="submit" className="pt-btn pt-btn-primary pt-auth-btn" disabled={loading}>
          {loading ? "Entrando..." : "Entrar"} {!loading && <ArrowRight size={18} />}
        </button>
      </form>

      <p className="pt-auth-alt">
        Ainda não tem conta? <Link to="/criar-conta">Criar conta</Link>
      </p>

      <div className="pt-auth-ou">ou só quer conhecer?</div>
      <button
        type="button"
        className="pt-btn pt-btn-ghost pt-auth-btn"
        onClick={() => {
          setScenarioId("fechamento");
          navigate("/dashboard");
        }}
      >
        <PlayCircle size={18} /> Ver o sistema com dados de exemplo
      </button>
    </AuthLayout>
  );
}
