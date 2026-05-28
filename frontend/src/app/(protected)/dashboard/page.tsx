
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
