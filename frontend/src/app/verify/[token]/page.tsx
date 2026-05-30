
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
          CyStar Selective Disclosure & Verification
        </p>
      </div>
    </div>
  );
}
