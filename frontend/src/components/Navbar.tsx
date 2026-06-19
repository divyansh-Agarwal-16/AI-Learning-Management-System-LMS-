// This client component renders the authenticated navigation header, providing links to core pages and active session actions.
"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";

export function Navbar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const [isOpen, setIsOpen] = useState(false);

  const links = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/courses", label: "Courses" },
    { href: "/profile", label: "Profile" },
  ];

  const handleSignOut = () => {
    signOut({ callbackUrl: "/" });
  };

  return (
    <nav className="border-b border-slate-900 bg-slate-950/80 backdrop-blur sticky top-0 z-50 w-full text-slate-100 font-sans">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between h-16 items-center">
          
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/dashboard" className="text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent hover:opacity-90 transition-opacity">
              ai-lms
            </Link>
          </div>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex space-x-8 items-center">
            {links.map((link) => {
              const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm font-medium transition-colors ${
                    isActive ? "text-indigo-400" : "text-slate-300 hover:text-white"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* User & SignOut Actions */}
          <div className="hidden md:flex items-center gap-4">
            <span className="text-xs text-slate-400">
              {session?.user?.name || session?.user?.email || "Scholar"}
            </span>
            <button
              onClick={handleSignOut}
              className="px-3 py-1.5 text-xs font-semibold bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 hover:text-white transition-colors"
            >
              Log Out
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 focus:outline-none"
            >
              <span className="sr-only">Open main menu</span>
              {isOpen ? (
                <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden border-b border-slate-900 bg-slate-950 px-4 pt-2 pb-4 space-y-2">
          {links.map((link) => {
            const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setIsOpen(false)}
                className={`block px-3 py-2 rounded-lg text-base font-medium transition-colors ${
                  isActive ? "bg-indigo-500/10 text-indigo-400" : "text-slate-300 hover:bg-slate-900 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          <div className="pt-4 border-t border-slate-900 flex justify-between items-center px-3">
            <span className="text-xs text-slate-500 truncate max-w-[200px]">
              {session?.user?.name || session?.user?.email || "Scholar"}
            </span>
            <button
              onClick={handleSignOut}
              className="px-3 py-1.5 text-xs font-semibold bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 hover:text-white transition-colors"
            >
              Log Out
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
