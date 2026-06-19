// This server component fetches authenticated user parameters and renders the unified profile view and preferences form.
import React from "react";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { Navbar } from "@/components/Navbar";
import { ProfileView } from "@/components/ProfileView";

export default async function ProfilePage() {
  const session = await getServerSession(authOptions);

  // Fallback defaults if session details are null/undefined during offline runs
  const userDetails = {
    name: session?.user?.name || "Demo User",
    email: session?.user?.email || "user@example.com",
    image: session?.user?.image || null,
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      <main className="flex-grow">
        <ProfileView user={userDetails} />
      </main>
    </div>
  );
}
