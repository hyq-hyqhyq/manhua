import type {
  ComicCreateRequest,
  ComicCreateResponse,
  ComicResult,
  ComicStatus,
  RevisionResponse
} from "./types";

const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

export const API_BASE =
  configuredApiBase && configuredApiBase.length > 0
    ? configuredApiBase
    : "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    let message = text;
    try {
      const payload = JSON.parse(text);
      message = payload.detail || text;
    } catch {
      message = text;
    }
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function assetUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  if (path.startsWith("/")) {
    return `${API_BASE}${path}`;
  }
  return `${API_BASE}/${path}`;
}

export function createComic(payload: ComicCreateRequest): Promise<ComicCreateResponse> {
  return request<ComicCreateResponse>("/api/comics", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getComic(comicId: string): Promise<ComicResult> {
  return request<ComicResult>(`/api/comics/${comicId}`);
}

export function getComicStatus(comicId: string): Promise<ComicStatus> {
  return request<ComicStatus>(`/api/comics/${comicId}/status`);
}

export function reviseComicGlobal(
  comicId: string,
  feedback: string
): Promise<RevisionResponse> {
  return request<RevisionResponse>(`/api/comics/${comicId}/revise-global`, {
    method: "POST",
    body: JSON.stringify({ feedback })
  });
}

export function reviseComicPanel(
  comicId: string,
  panelId: number,
  feedback: string
): Promise<RevisionResponse> {
  return request<RevisionResponse>(`/api/comics/${comicId}/revise-panel`, {
    method: "POST",
    body: JSON.stringify({ panel_id: panelId, feedback })
  });
}
