import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ThemeSwitcher } from "./theme/ThemeSwitcher";
import { login, register } from "./api/client";
import {
  btnPrimaryClass,
  btnSecondaryClass,
  cardClass,
  inputClass,
} from "./ui/styles";

export default function AuthPage() {
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  const hasAtLeastTwoLetters = (value: string) =>
    [...value].filter((char) => /[A-Za-z]/.test(char)).length >= 2;

  const isValidEmail = (value: string) =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isRegistering) {
        if (!isValidEmail(email)) {
          alert("Please enter a valid email address.");
          return;
        }
        if (!hasAtLeastTwoLetters(firstName)) {
          alert("First name must contain at least two letters.");
          return;
        }
        if (!hasAtLeastTwoLetters(lastName)) {
          alert("Last name must contain at least two letters.");
          return;
        }
        if (password !== confirmPassword) {
          alert("Passwords do not match.");
          return;
        }

        await register(email, password, confirmPassword, firstName, lastName);
      } else {
        await login(email, password);
      }

      navigate("/dashboard");
    } catch (err) {
      console.error("Authentication failed", err);
      alert(isRegistering ? "Registration failed" : "Login failed");
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
          {isRegistering && (
            <>
              <label className={labelClass}>
                First name
                <input
                  type="text"
                  required
                  className={inputClass}
                  placeholder="First name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
              </label>
              <label className={labelClass}>
                Last name
                <input
                  type="text"
                  required
                  className={inputClass}
                  placeholder="Last name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </label>
            </>
          )}
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
          {isRegistering && (
            <label className={labelClass}>
              Confirm password
              <input
                type="password"
                required
                className={inputClass}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </label>
          )}

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
