// This page renders the landing view of the LMS, highlighting core AI tutoring features and action buttons.
import Link from "next/link";

export default function Home() {
  const features = [
    {
      title: "AI Tutor",
      description: "Receive personalized, real-time guidance and tutoring mapped to your learning pace and interests.",
      icon: "🤖",
    },
    {
      title: "Smart Quizzes",
      description: "Test your knowledge with dynamically generated quizzes that adapt in difficulty to match your level.",
      icon: "📝",
    },
    {
      title: "Adaptive Paths",
      description: "Follow customized curriculum paths designed specifically to address your academic and skill gaps.",
      icon: "🎯",
    },
    {
      title: "Progress Tracking",
      description: "Monitor milestones and track detailed analytics of your cognitive progress and subject mastery.",
      icon: "📈",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white font-sans">
      {/* Header Navigation */}
      <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent hover:opacity-90 transition-opacity">
            ai-lms
          </Link>
          <div className="flex gap-4">
            <Link href="/login" className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Sign In
            </Link>
            <Link href="/signup" className="px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-lg hover:shadow-indigo-500/20 transition-all">
              Sign Up
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col justify-center py-20 px-6 max-w-7xl mx-auto w-full">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-6 bg-gradient-to-b from-white to-slate-400 bg-clip-text text-transparent">
            Learn Anything with Your Personal AI Tutor
          </h1>
          <p className="text-lg md:text-xl text-slate-400 mb-8 max-w-2xl mx-auto leading-relaxed">
            Experience next-generation education powered by RAG technology, multi-agent cognitive orchestration, and personalized feedback.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup" className="px-8 py-3 text-base font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-lg hover:shadow-indigo-500/30 transition-all transform hover:-translate-y-0.5">
              Get Started
            </Link>
            <Link href="/login" className="px-8 py-3 text-base font-semibold border border-slate-800 hover:bg-slate-900 text-slate-300 hover:text-white rounded-lg transition-all transform hover:-translate-y-0.5">
              View Demo
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <section id="features" className="py-10 border-t border-slate-900">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Engineered for Accelerating Knowledge
            </h2>
            <p className="text-slate-400 max-w-lg mx-auto">
              Our autonomous learning engine coordinates multiple tools to optimize your educational experience.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, idx) => (
              <div 
                key={idx} 
                className="p-6 bg-slate-900/40 border border-slate-900 hover:border-slate-800 rounded-xl transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/[0.02] group"
              >
                <div className="text-3xl mb-4 bg-slate-800/50 w-12 h-12 flex items-center justify-center rounded-lg group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold mb-2 text-slate-200 group-hover:text-white transition-colors">
                  {feature.title}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-8 text-center text-sm text-slate-500">
        <div className="max-w-7xl mx-auto px-6">
          <p>© {new Date().getFullYear()} AI Learning Management System. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
