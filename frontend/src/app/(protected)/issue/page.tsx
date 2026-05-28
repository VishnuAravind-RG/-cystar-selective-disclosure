
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
