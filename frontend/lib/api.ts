import { RememberRequest, RememberResponse, RecallRequest, RecallResponse, ForgetRequest, ForgetResponse, GraphData } from "./types";

const API_BASE = "http://localhost:8000";

export async function remember(req: RememberRequest): Promise<RememberResponse> {
  const res = await fetch(`${API_BASE}/remember`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req)
  });
  if (!res.ok) throw new Error("Failed to remember");
  return res.json();
}

export async function recall(req: RecallRequest): Promise<RecallResponse> {
  const res = await fetch(`${API_BASE}/recall`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req)
  });
  if (!res.ok) throw new Error("Failed to recall");
  return res.json();
}

export async function forget(req: ForgetRequest): Promise<ForgetResponse> {
  const res = await fetch(`${API_BASE}/forget`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req)
  });
  if (!res.ok) throw new Error("Failed to forget");
  return res.json();
}

export async function getGraph(): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/graph`);
  if (!res.ok) throw new Error("Failed to fetch graph");
  return res.json();
}

export async function getOverlap(caseA: string, caseB: string): Promise<{overlap: any[]}> {
  const res = await fetch(`${API_BASE}/overlap?case_a=${encodeURIComponent(caseA)}&case_b=${encodeURIComponent(caseB)}`);
  if (!res.ok) throw new Error("Failed to fetch overlap");
  return res.json();
}

export const STREAM_URL = `${API_BASE}/ingest/stream`;
