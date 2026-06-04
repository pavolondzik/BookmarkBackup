import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ThemeSwitcher } from "./theme/ThemeSwitcher";
import { login } from "./api/client";
import {
  btnPrimaryClass,
  btnSecondaryClass,
  cardClass,
  inputClass,
} from "./ui/styles";

export default function AuthPage() {
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      // naive error feedback — in future show UI
      console.error("Login failed", err);
      alert("Login failed");
    }
  };

  const labelClass = "flex flex-col gap-1 text-sm text-muted";

  return (
    <div className="login-bg flex h-screen items-center justify-center bg-surface p-4">
      <div className="absolute right-4 top-4">
        <ThemeSwitcher />
      </div>
      <div className={`${cardClass} w-full max-w-sm`}>
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold">Bookmark Backup</h1>
          <p className="text-sm text-muted">
            {isRegistering ? "Create your account" : "Sign in to continue"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className={labelClass}>
            Email
            <input
              type="email"
              required
              className={inputClass}
              placeholder="email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label className={labelClass}>
            Password
            <input
              type="password"
              required
              className={inputClass}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>

          <div className="mt-2 flex flex-col gap-3">
            <button type="submit" className={btnPrimaryClass}>
              {isRegistering ? "Register" : "Login"}
            </button>
            <div className="relative my-2">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border"></span>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-surface px-2 text-muted">Or</span>
              </div>
            </div>
            <button
              type="button"
              className={btnSecondaryClass}
              onClick={() => setIsRegistering(!isRegistering)}
            >
              {isRegistering ? "Back to Login" : "Create an account"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
