export interface RememberRequest {
  content: string;
  source_name: string;
}

export interface RememberResponse {
  status: string;
  entities_found: number;
}

export interface RecallRequest {
  query: string;
}

export interface RecallResponse {
  answer: string;
  raw_path: any[];
  path: string[];
}

export interface ForgetRequest {
  target: string;
  reason: string;
}

export interface ForgetResponse {
  status: string;
  affected_edges: number;
}

export interface Node {
  id: string;
  label: string;
  type: string;
}

export interface Edge {
  source: string;
  target: string;
  label: string;
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}
