// This file exposes NextAuth credentials and OAuth endpoints as standard Next.js App Router GET/POST route handlers.
import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth";

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
