"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { login, register } from "@/stores/authSlice";
import { useAppDispatch, useAppSelector } from "@/stores/hooks";

export default function LoginPage() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { status, error } = useAppSelector((s) => s.auth);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const result =
      mode === "login"
        ? await dispatch(login({ email, password }))
        : await dispatch(register({ email, username, password }));
    if (login.fulfilled.match(result) || register.fulfilled.match(result)) {
      router.push("/session");
    }
  };

  return (
    <main className="max-w-md mx-auto p-10 flex flex-col gap-6">
      <h1 className="text-2xl font-bold">{mode === "login" ? "Log in" : "Create account"}</h1>
      <form className="score-card p-6 flex flex-col gap-4" onSubmit={submit}>
        <label className="flex flex-col gap-2 text-sm">
          <span className="score-dim">Email</span>
          <input
            className="score-input px-3 py-2"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        {mode === "register" && (
          <label className="flex flex-col gap-2 text-sm">
            <span className="score-dim">Username</span>
            <input
              className="score-input px-3 py-2"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
              minLength={3}
            />
          </label>
        )}
        <label className="flex flex-col gap-2 text-sm">
          <span className="score-dim">Password</span>
          <input
            className="score-input px-3 py-2"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            minLength={8}
          />
        </label>
        {error && <p className="score-warn text-sm">{error}</p>}
        <button
          className="score-btn score-btn-accent px-6 py-2"
          type="submit"
          disabled={status === "authenticating"}
        >
          {status === "authenticating" ? "..." : mode === "login" ? "Log in" : "Sign up"}
        </button>
      </form>
      <button
        className="score-link text-sm self-start"
        onClick={() => setMode(mode === "login" ? "register" : "login")}
      >
        {mode === "login" ? "Need an account? Register" : "Have an account? Log in"}
      </button>
    </main>
  );
}
