
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
