// This middleware protects private pages like onboarding and dashboard by requiring active NextAuth sessions.
import { withAuth } from "next-auth/middleware";

export default withAuth({
  pages: {
    signIn: "/login",
  },
});

export const config = {
  matcher: [
    "/onboarding/:path*",
    "/dashboard/:path*",
    "/courses/:path*",
    "/course/:path*",
    "/profile/:path*",
  ],
};
