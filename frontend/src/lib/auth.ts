// This module configures NextAuth options, defining Google OAuth and Credentials authentication strategies.
import { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "mock-google-client-id",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "mock-google-client-secret",
    }),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "user@example.com" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        try {
          const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
          
          // 1. Authenticate with FastAPI Backend
          const res = await fetch(`${apiBaseUrl}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });
          
          const loginData = await res.json();
          if (!res.ok || !loginData.success) {
            return null;
          }
          
          const { access_token, refresh_token } = loginData.data;
          
          // 2. Fetch User Profile for display name
          const profileRes = await fetch(`${apiBaseUrl}/users/profile`, {
            method: "GET",
            headers: {
              "Authorization": `Bearer ${access_token}`,
            },
          });
          
          let name = credentials.email.split("@")[0];
          let userId = credentials.email;
          
          if (profileRes.ok) {
            const profileData = await profileRes.json();
            if (profileData.success) {
              userId = profileData.data.id;
              name = profileData.data.profile?.full_name || name;
            }
          }
          
          return {
            id: userId,
            email: credentials.email,
            name: name,
            accessToken: access_token,
            refreshToken: refresh_token,
          };
        } catch (err) {
          console.error("Authorize error:", err);
          return null;
        }
      },
    }),
  ],
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.accessToken = (user as any).accessToken;
        token.refreshToken = (user as any).refreshToken;
        token.name = user.name;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        const user = session.user as any;
        user.id = token.id as string;
        user.accessToken = token.accessToken as string;
        user.refreshToken = token.refreshToken as string;
        if (token.name) {
          user.name = token.name as string;
        }
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
    signOut: "/",
    error: "/login",
  },
  secret: process.env.NEXTAUTH_SECRET || "fallback-secret-at-least-32-chars-long",
};
