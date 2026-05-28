
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
