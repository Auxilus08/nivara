import { ShieldCheck, Sparkles } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-12 sm:px-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-10">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-indigo-600 p-2 text-white"><ShieldCheck size={22} /></div>
            <span className="text-xl font-semibold tracking-tight">Nivara</span>
          </div>
          <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">Foundation preview</span>
        </header>
        <section className="max-w-3xl space-y-5">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">Contextual safety intelligence</p>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">Plan journeys with more context.</h1>
          <p className="max-w-2xl text-lg leading-8 text-slate-600">Nivara will help compare routes using travel efficiency and contextual safety indicators, without presenting estimates as guarantees.</p>
        </section>
        <Card className="max-w-2xl border-indigo-100">
          <CardContent className="flex gap-4">
            <Sparkles className="mt-1 shrink-0 text-indigo-600" size={20} />
            <div>
              <h2 className="font-semibold">Your safety-aware workspace is taking shape.</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">Navigation, incident reporting, Safe Trip, and emergency workflows will be added as independent feature modules.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
