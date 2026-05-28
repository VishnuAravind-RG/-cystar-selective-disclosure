import os
import sys

print("=" * 60)
print("  CyStar Frontend - Phase 2: Complete UI")
print("=" * 60)
print()

if not os.path.exists("package.json"):
    print("ERROR: Run this from the frontend/ directory!")
    print("  cd cystar-selective-disclosure\\frontend")
    print("  python phase2_frontend.py")
    sys.exit(1)

def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  + {path}")

print("[1/1] Creating frontend files...")
print()

write_file('src/types/index.ts', '''
export interface User {
  id: string;
  email: string;
  name: string;
}

export interface Credential {
  id: string;
  credential_title: string;
  claims: Record<string, string>;
  issuer_name: string;
  issue_date: string;
  created_at: string;
}

export interface ShareResponse {
  share_token: string;
  share_url: string;
  expires_at: string;
  selected_fields: string[];
}

export interface VerificationResult {
  verified: boolean;
  credential_title?: string;
  disclosed_fields?: Record<string, string>;
  issuer?: string;
  subject?: string;
  issued_at?: number;
  total_claims?: number;
  disclosed_count?: number;
  hidden_count?: number;
  expired?: boolean;
  error?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
''')

write_file('src/lib/api-client.ts', '''
import axios from "axios";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
''')

write_file('src/lib/auth-context.tsx', '''
"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import apiClient from "@/lib/api-client";
import { User, AuthResponse } from "@/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    const storedUser = localStorage.getItem("user");
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiClient.post<AuthResponse>("/api/auth/login", {
      email,
      password,
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
  };

  const register = async (name: string, email: string, password: string) => {
    const response = await apiClient.post<AuthResponse>("/api/auth/register", {
      name,
      email,
      password,
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
''')

write_file('src/app/layout.tsx', '''
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CyStar - Selective Disclosure & Verification",
  description: "IETF SD-JWT based selective disclosure and credential verification system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          {children}
          <Toaster richColors position="top-right" />
        </AuthProvider>
      </body>
    </html>
  );
}
''')

write_file('src/app/page.tsx', '''
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
          CyStar Summer Internship Assessment — IIT Madras
        </p>
      </div>
    </div>
  );
}
''')

write_file('src/app/(auth)/login/page.tsx', '''
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Shield, Loader2 } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
      router.push("/dashboard");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray-900 border-gray-800">
        <CardHeader className="text-center space-y-2">
          <div className="flex justify-center mb-2">
            <Shield className="h-10 w-10 text-emerald-400" />
          </div>
          <CardTitle className="text-2xl text-white">Welcome back</CardTitle>
          <CardDescription className="text-gray-400">
            Sign in to access your credentials
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-300">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-300">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Sign In
            </Button>
            <p className="text-sm text-gray-400">
              No account?{" "}
              <Link href="/register" className="text-emerald-400 hover:text-emerald-300 underline">
                Register
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
''')

write_file('src/app/(auth)/register/page.tsx', '''
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Shield, Loader2 } from "lucide-react";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    if (password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    try {
      await register(name, email, password);
      toast.success("Account created successfully!");
      router.push("/dashboard");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray-900 border-gray-800">
        <CardHeader className="text-center space-y-2">
          <div className="flex justify-center mb-2">
            <Shield className="h-10 w-10 text-emerald-400" />
          </div>
          <CardTitle className="text-2xl text-white">Create account</CardTitle>
          <CardDescription className="text-gray-400">
            Start managing your verifiable credentials
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-gray-300">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Vishnu Aravind"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-300">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-300">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Min 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-gray-300">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Create Account
            </Button>
            <p className="text-sm text-gray-400">
              Already have an account?{" "}
              <Link href="/login" className="text-emerald-400 hover:text-emerald-300 underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
''')

write_file('src/app/(protected)/layout.tsx', '''
"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Shield, LayoutDashboard, FilePlus, LogOut, Loader2 } from "lucide-react";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  if (!user) return null;

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/issue", label: "Issue Credential", icon: FilePlus },
  ];

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-emerald-400" />
              <span className="text-lg font-semibold text-white">CyStar</span>
            </Link>
            <div className="hidden sm:flex items-center gap-1">
              {navItems.map((item) => (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`text-sm ${
                      pathname === item.href
                        ? "text-emerald-400 bg-emerald-400/10"
                        : "text-gray-400 hover:text-white hover:bg-gray-800"
                    }`}
                  >
                    <item.icon className="h-4 w-4 mr-2" />
                    {item.label}
                  </Button>
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400 hidden sm:block">{user.email}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-gray-400 hover:text-red-400 hover:bg-red-400/10"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}
''')

write_file('src/app/(protected)/dashboard/page.tsx', '''
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";
import { Credential } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { FileText, Share2, Plus, Loader2, Clock } from "lucide-react";

export default function DashboardPage() {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchCredentials();
  }, []);

  const fetchCredentials = async () => {
    try {
      const response = await apiClient.get("/api/credentials/");
      setCredentials(response.data);
    } catch (error: any) {
      toast.error("Failed to load credentials");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Credentials</h1>
          <p className="text-gray-400 text-sm mt-1">
            {credentials.length} credential{credentials.length !== 1 ? "s" : ""} issued
          </p>
        </div>
        <Button
          onClick={() => router.push("/issue")}
          className="bg-emerald-600 hover:bg-emerald-700 text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          Issue New
        </Button>
      </div>

      {credentials.length === 0 ? (
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <FileText className="h-12 w-12 text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-300 mb-2">No credentials yet</h3>
            <p className="text-gray-500 text-sm mb-6 max-w-sm">
              Issue your first verifiable credential to get started with selective disclosure.
            </p>
            <Button
              onClick={() => router.push("/issue")}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <Plus className="h-4 w-4 mr-2" />
              Issue Credential
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {credentials.map((cred) => (
            <Card key={cred.id} className="bg-gray-900 border-gray-800 hover:border-gray-700 transition-colors">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg text-white">
                    {cred.credential_title}
                  </CardTitle>
                  <Badge variant="outline" className="text-emerald-400 border-emerald-400/30 bg-emerald-400/5 text-xs">
                    {Object.keys(cred.claims).length} fields
                  </Badge>
                </div>
                <CardDescription className="text-gray-400">
                  Issued by {cred.issuer_name}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-1.5">
                  {Object.keys(cred.claims).slice(0, 5).map((key) => (
                    <Badge key={key} variant="secondary" className="bg-gray-800 text-gray-300 text-xs">
                      {key}
                    </Badge>
                  ))}
                  {Object.keys(cred.claims).length > 5 && (
                    <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
                      +{Object.keys(cred.claims).length - 5} more
                    </Badge>
                  )}
                </div>
                <div className="flex items-center text-xs text-gray-500">
                  <Clock className="h-3 w-3 mr-1" />
                  {new Date(cred.created_at).toLocaleDateString()}
                </div>
                <Button
                  onClick={() => router.push(`/share/${cred.id}`)}
                  variant="outline"
                  className="w-full border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-white"
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  Share Selectively
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
''')

write_file('src/app/(protected)/issue/page.tsx', '''
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { toast } from "sonner";
import { Plus, Trash2, Loader2, FileText } from "lucide-react";

interface ClaimField {
  key: string;
  value: string;
}

const DEFAULT_CLAIMS: ClaimField[] = [
  { key: "name", value: "" },
  { key: "degree", value: "" },
  { key: "graduationYear", value: "" },
  { key: "cgpa", value: "" },
  { key: "marks", value: "" },
  { key: "issuerName", value: "" },
  { key: "issueDate", value: "" },
];

export default function IssuePage() {
  const [credentialTitle, setCredentialTitle] = useState("");
  const [issuerName, setIssuerName] = useState("");
  const [claims, setClaims] = useState<ClaimField[]>(DEFAULT_CLAIMS);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const addClaim = () => {
    setClaims([...claims, { key: "", value: "" }]);
  };

  const removeClaim = (index: number) => {
    setClaims(claims.filter((_, i) => i !== index));
  };

  const updateClaim = (index: number, field: "key" | "value", val: string) => {
    const updated = [...claims];
    updated[index][field] = val;
    setClaims(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!credentialTitle.trim()) {
      toast.error("Enter a credential title");
      return;
    }
    if (!issuerName.trim()) {
      toast.error("Enter an issuer name");
      return;
    }

    const validClaims = claims.filter((c) => c.key.trim() && c.value.trim());
    if (validClaims.length === 0) {
      toast.error("Add at least one claim with key and value");
      return;
    }

    const claimsObj: Record<string, string> = {};
    for (const c of validClaims) {
      claimsObj[c.key.trim()] = c.value.trim();
    }

    setLoading(true);
    try {
      await apiClient.post("/api/credentials/issue", {
        credential_title: credentialTitle,
        issuer_name: issuerName,
        claims: claimsObj,
      });
      toast.success("Credential issued successfully!");
      router.push("/dashboard");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to issue credential");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Issue Credential</h1>
        <p className="text-gray-400 text-sm mt-1">
          Create a new verifiable credential with custom claims
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-lg text-white flex items-center gap-2">
              <FileText className="h-5 w-5 text-emerald-400" />
              Credential Details
            </CardTitle>
            <CardDescription className="text-gray-400">
              Each claim will be individually hashable for selective disclosure
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-gray-300">Credential Title</Label>
                <Input
                  placeholder="e.g., B.Tech Degree Certificate"
                  value={credentialTitle}
                  onChange={(e) => setCredentialTitle(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-gray-300">Issuer Name</Label>
                <Input
                  placeholder="e.g., PSG College of Technology"
                  value={issuerName}
                  onChange={(e) => setIssuerName(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-gray-300">Claims</Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={addClaim}
                  className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-400/10"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Claim
                </Button>
              </div>

              {claims.map((claim, index) => (
                <div key={index} className="flex gap-2 items-center">
                  <Input
                    placeholder="Field name"
                    value={claim.key}
                    onChange={(e) => updateClaim(index, "key", e.target.value)}
                    className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 flex-1"
                  />
                  <Input
                    placeholder="Value"
                    value={claim.value}
                    onChange={(e) => updateClaim(index, "value", e.target.value)}
                    className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 flex-1"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeClaim(index)}
                    className="text-gray-500 hover:text-red-400 hover:bg-red-400/10 shrink-0"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>

            <Button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Issue Credential
            </Button>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
''')

write_file('src/app/(protected)/share/[id]/page.tsx', '''
"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import apiClient from "@/lib/api-client";
import { Credential, ShareResponse } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { QRCodeSVG } from "qrcode.react";
import { Loader2, Copy, Share2, Eye, EyeOff, QrCode, ExternalLink, Clock } from "lucide-react";

export default function SharePage() {
  const params = useParams();
  const credentialId = params.id as string;

  const [credential, setCredential] = useState<Credential | null>(null);
  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set());
  const [expiryHours, setExpiryHours] = useState(24);
  const [loading, setLoading] = useState(true);
  const [sharing, setSharing] = useState(false);
  const [shareResult, setShareResult] = useState<ShareResponse | null>(null);

  useEffect(() => {
    fetchCredential();
  }, []);

  const fetchCredential = async () => {
    try {
      const response = await apiClient.get("/api/credentials/");
      const cred = response.data.find((c: Credential) => c.id === credentialId);
      if (cred) {
        setCredential(cred);
      } else {
        toast.error("Credential not found");
      }
    } catch (error: any) {
      toast.error("Failed to load credential");
    } finally {
      setLoading(false);
    }
  };

  const toggleField = (field: string) => {
    const updated = new Set(selectedFields);
    if (updated.has(field)) {
      updated.delete(field);
    } else {
      updated.add(field);
    }
    setSelectedFields(updated);
  };

  const handleShare = async () => {
    if (selectedFields.size === 0) {
      toast.error("Select at least one field to share");
      return;
    }

    setSharing(true);
    try {
      const response = await apiClient.post("/api/credentials/share", {
        credential_id: credentialId,
        selected_fields: Array.from(selectedFields),
        expires_in_hours: expiryHours,
      });
      setShareResult(response.data);
      toast.success("Share link generated!");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to generate share link");
    } finally {
      setSharing(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  if (!credential) {
    return (
      <div className="text-center py-20 text-gray-400">
        Credential not found
      </div>
    );
  }

  const allFields = Object.keys(credential.claims);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Share Credential</h1>
        <p className="text-gray-400 text-sm mt-1">
          Select which fields to disclose — hidden fields remain cryptographically sealed
        </p>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-lg text-white">{credential.credential_title}</CardTitle>
          <CardDescription className="text-gray-400">
            Issued by {credential.issuer_name} — {allFields.length} total fields
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-gray-300 font-medium">Select fields to reveal</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedFields(new Set(allFields))}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Select All
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedFields(new Set())}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Clear
                </Button>
              </div>
            </div>

            {allFields.map((field) => (
              <div
                key={field}
                className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedFields.has(field)
                    ? "border-emerald-500/30 bg-emerald-500/5"
                    : "border-gray-800 bg-gray-800/50 hover:border-gray-700"
                }`}
                onClick={() => toggleField(field)}
              >
                <div className="flex items-center gap-3">
                  <Checkbox
                    checked={selectedFields.has(field)}
                    onCheckedChange={() => toggleField(field)}
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-200">{field}</p>
                    <p className="text-xs text-gray-500">{credential.claims[field]}</p>
                  </div>
                </div>
                {selectedFields.has(field) ? (
                  <Eye className="h-4 w-4 text-emerald-400" />
                ) : (
                  <EyeOff className="h-4 w-4 text-gray-600" />
                )}
              </div>
            ))}
          </div>

          <div className="space-y-2">
            <Label className="text-gray-300">Link expires in</Label>
            <select
              value={expiryHours}
              onChange={(e) => setExpiryHours(Number(e.target.value))}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-md px-3 py-2 text-sm"
            >
              <option value={1}>1 hour</option>
              <option value={6}>6 hours</option>
              <option value={12}>12 hours</option>
              <option value={24}>24 hours</option>
              <option value={48}>48 hours</option>
              <option value={72}>3 days</option>
              <option value={168}>7 days</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Eye className="h-4 w-4 text-emerald-400" />
            <span>{selectedFields.size} fields visible</span>
            <span className="text-gray-600">|</span>
            <EyeOff className="h-4 w-4 text-gray-500" />
            <span>{allFields.length - selectedFields.size} fields hidden</span>
          </div>

          <Button
            onClick={handleShare}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
            disabled={sharing || selectedFields.size === 0}
          >
            {sharing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Share2 className="h-4 w-4 mr-2" />}
            Generate Share Link
          </Button>
        </CardContent>
      </Card>

      {shareResult && (
        <Card className="bg-gray-900 border-emerald-500/30">
          <CardHeader>
            <CardTitle className="text-lg text-emerald-400 flex items-center gap-2">
              <QrCode className="h-5 w-5" />
              Share Link Generated
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-gray-300">Shareable Link</Label>
              <div className="flex gap-2">
                <div className="flex-1 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-gray-300 truncate">
                  {shareResult.share_url}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(shareResult.share_url)}
                  className="border-gray-700 text-gray-300 hover:bg-gray-800 shrink-0"
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="flex justify-center p-6 bg-white rounded-xl">
              <QRCodeSVG value={shareResult.share_url} size={200} />
            </div>

            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              Expires: {new Date(shareResult.expires_at).toLocaleString()}
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1 border-gray-700 text-gray-300 hover:bg-gray-800"
                onClick={() => copyToClipboard(shareResult.share_token)}
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy Token
              </Button>
              <Button
                className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={() => window.open(`/verify/${shareResult.share_token}`, "_blank")}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Open Verify Page
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
''')

write_file('src/app/verify/[token]/page.tsx', '''
"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { VerificationResult } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ShieldCheck, ShieldX, Loader2, Clock, Eye, EyeOff, AlertTriangle, User, Building } from "lucide-react";
import axios from "axios";

export default function VerifyPage() {
  const params = useParams();
  const token = params.token as string;

  const [result, setResult] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    verifyCredential();
  }, []);

  const verifyCredential = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await axios.get(`${apiUrl}/api/verify/${token}`);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-emerald-400 mx-auto" />
          <p className="text-gray-400">Verifying credential...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
        <Card className="w-full max-w-lg bg-gray-900 border-red-500/30">
          <CardContent className="flex flex-col items-center py-12 text-center">
            <ShieldX className="h-16 w-16 text-red-400 mb-4" />
            <h2 className="text-xl font-bold text-red-400 mb-2">Verification Failed</h2>
            <p className="text-gray-400">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!result) return null;

  const isExpired = result.expired;
  const isVerified = result.verified && !isExpired;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg space-y-4">
        <Card className={`bg-gray-900 ${
          isVerified ? "border-emerald-500/30" : isExpired ? "border-amber-500/30" : "border-red-500/30"
        }`}>
          <CardHeader className="text-center pb-2">
            {isVerified ? (
              <>
                <ShieldCheck className="h-16 w-16 text-emerald-400 mx-auto mb-2" />
                <Badge className="mx-auto bg-emerald-500/10 text-emerald-400 border-emerald-500/30 text-sm px-4 py-1">
                  Verified
                </Badge>
              </>
            ) : isExpired ? (
              <>
                <AlertTriangle className="h-16 w-16 text-amber-400 mx-auto mb-2" />
                <Badge className="mx-auto bg-amber-500/10 text-amber-400 border-amber-500/30 text-sm px-4 py-1">
                  Expired
                </Badge>
              </>
            ) : (
              <>
                <ShieldX className="h-16 w-16 text-red-400 mx-auto mb-2" />
                <Badge className="mx-auto bg-red-500/10 text-red-400 border-red-500/30 text-sm px-4 py-1">
                  Invalid
                </Badge>
              </>
            )}
            {result.credential_title && (
              <CardTitle className="text-xl text-white mt-4">{result.credential_title}</CardTitle>
            )}
          </CardHeader>

          {isVerified && result.disclosed_fields && (
            <CardContent className="space-y-4">
              <Separator className="bg-gray-800" />

              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-400 flex items-center gap-2">
                  <Eye className="h-4 w-4 text-emerald-400" />
                  Disclosed Fields
                </h3>
                {Object.entries(result.disclosed_fields).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span className="text-sm text-gray-400">{key}</span>
                    <span className="text-sm font-medium text-white">{value}</span>
                  </div>
                ))}
              </div>

              {result.hidden_count && result.hidden_count > 0 && (
                <div className="flex items-center gap-2 p-3 bg-gray-800/30 rounded-lg">
                  <EyeOff className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-500">
                    {result.hidden_count} field{result.hidden_count > 1 ? "s" : ""} kept private
                  </span>
                </div>
              )}

              <Separator className="bg-gray-800" />

              <div className="space-y-2">
                {result.issuer && (
                  <div className="flex items-center gap-2 text-sm">
                    <Building className="h-4 w-4 text-gray-500" />
                    <span className="text-gray-400">Issuer:</span>
                    <span className="text-gray-200">{result.issuer}</span>
                  </div>
                )}
                {result.issued_at && (
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="h-4 w-4 text-gray-500" />
                    <span className="text-gray-400">Issued:</span>
                    <span className="text-gray-200">
                      {new Date(result.issued_at * 1000).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>

              <div className="text-center pt-2">
                <p className="text-xs text-gray-600">
                  Cryptographically verified using IETF SD-JWT with Ed25519
                </p>
              </div>
            </CardContent>
          )}

          {!isVerified && result.error && (
            <CardContent>
              <p className="text-sm text-gray-400 text-center">{result.error}</p>
            </CardContent>
          )}
        </Card>

        <p className="text-center text-xs text-gray-600">
          CyStar Selective Disclosure & Verification — IIT Madras
        </p>
      </div>
    </div>
  );
}
''')


print()
print("=" * 60)
print("  PHASE 2 COMPLETE!")
print("=" * 60)
print()
print("  Files created:")
print("    - 12 frontend components/pages")
print()
print("  Next steps:")
print("    1. cd frontend")
print("    2. npm run dev")
print("    3. Open http://localhost:3000")
print("    4. Make sure backend is running on :8000")
print()
print("  Test the full flow:")
print("    1. Register a new account")
print("    2. Issue a credential with custom claims")
print("    3. Share with selected fields -> get QR + link")
print("    4. Open verify link in incognito -> see verification")
print()