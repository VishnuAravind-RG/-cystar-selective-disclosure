
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Shield } from "lucide-react";

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-emerald-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full text-center space-y-8">
        <div className="flex justify-center">
          <div className="p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20">
            <Shield className="h-16 w-16 text-emerald-400" />
          </div>
        </div>

        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-white tracking-tight">
            CyStar
          </h1>
          <p className="text-xl text-gray-400 max-w-lg mx-auto">
            Selective Disclosure & Verification Module
          </p>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            Share only what you choose. Cryptographically verify credentials
            without exposing private data. Built on IETF SD-JWT with Ed25519 signatures.
          </p>
        </div>

        <div className="flex gap-4 justify-center">
          <Button
            onClick={() => router.push("/login")}
            variant="outline"
            className="px-8 py-6 text-lg border-gray-700 text-gray-300 hover:bg-gray-800"
          >
            Login
          </Button>
          <Button
            onClick={() => router.push("/register")}
            className="px-8 py-6 text-lg bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            Get Started
          </Button>
        </div>

        <p className="text-xs text-gray-600">
          CyStar Selective Disclosure Platform
        </p>
      </div>
    </div>
  );
}
