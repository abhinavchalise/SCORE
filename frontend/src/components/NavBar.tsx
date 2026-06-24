"use client";

import Link from "next/link";
import { useEffect } from "react";
import { getMe, getToken } from "@/lib/api";
import { logout, setUser } from "@/stores/authSlice";
import { useAppDispatch, useAppSelector } from "@/stores/hooks";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/session", label: "Session" },
  { href: "/history", label: "History" },
  { href: "/settings", label: "Settings" },
];

export default function NavBar() {
  const dispatch = useAppDispatch();
  const { user, status } = useAppSelector((s) => s.auth);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    getMe()
      .then((restored) => dispatch(setUser({ user: restored, token })))
      .catch(() => dispatch(logout()));
  }, [dispatch]);

  return (
    <nav className="score-card flex items-center justify-between px-6 py-3 m-4">
      <div className="flex gap-4 text-sm">
        {LINKS.map((link) => (
          <Link key={link.href} href={link.href} className="score-link">
            {link.label}
          </Link>
        ))}
      </div>
      <div className="text-sm score-dim">
        {status === "authenticated" && user ? (
          <span className="flex items-center gap-3">
            <span>{user.username}</span>
            <button className="score-btn px-3 py-1" onClick={() => dispatch(logout())}>
              Log out
            </button>
          </span>
        ) : (
          <Link href="/login" className="score-link">
            Log in
          </Link>
        )}
      </div>
    </nav>
  );
}
