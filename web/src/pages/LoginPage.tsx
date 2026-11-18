import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Lock, LogIn, Play, User } from "lucide-react";
import { useApp } from "../context/AppContext";
import "./LoginPage.css";

export function LoginPage() {
  const { loginLive, setScenarioId } = useApp();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const base = import.meta.env.BASE_URL;

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
          ? `${err.message} (No GitHub Pages sem servidor Python, use o modo Cenários abaixo.)`
          : "Não foi possível conectar ao servidor."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="pt-login-wrap">
      <div className="pt-card pt-login-card">
        <div className="pt-login-brand">
          <img src={`${base}brand/padrinho-track-lockup.svg`} alt="Padrinho Track" />
          <p>Acesso restrito à coordenação · PUC Minas</p>
        </div>

        {error && (
          <div className="pt-alert pt-alert-danger" style={{ marginBottom: 16 }}>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={onSubmit} className="pt-stack-sm" style={{ gap: 14 }}>
          <div className="pt-field">
            <label className="pt-label" htmlFor="username">Usuário</label>
            <div className="pt-input-wrap">
              <span className="pt-input-icon"><User size={15} /></span>
              <input
                id="username"
                className="pt-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
              />
            </div>
          </div>

          <div className="pt-field">
            <label className="pt-label" htmlFor="password">Senha</label>
            <div className="pt-input-wrap">
              <span className="pt-input-icon"><Lock size={15} /></span>
              <input
                id="password"
                className="pt-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button type="submit" className="pt-btn pt-btn-primary pt-btn-lg" disabled={loading}>
            <LogIn size={16} /> {loading ? "Entrando..." : "Entrar no servidor"}
          </button>
        </form>

        <div className="pt-login-divider">ou testar sem servidor</div>

        <button
          type="button"
          className="pt-btn pt-btn-soft"
          style={{ width: "100%" }}
          onClick={() => {
            setScenarioId("fechamento");
            navigate("/dashboard");
          }}
        >
          <Play size={15} /> Entrar no Modo Cenários Interativos
        </button>

        <div style={{ marginTop: 18, textAlign: "center" }}>
          <Link to="/" className="pt-back-link" style={{ margin: 0 }}>
            <ArrowLeft size={14} /> Voltar para apresentação
          </Link>
        </div>
      </div>
    </div>
  );
}
