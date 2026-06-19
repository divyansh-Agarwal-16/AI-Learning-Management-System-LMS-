// This client-side wrapper component supplies the NextAuth SessionContext to all descendent React components.
"use client";

import React from "react";
import { SessionProvider } from "next-auth/react";

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
