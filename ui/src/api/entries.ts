import { apiDelete, apiGet, apiPost, apiPut } from "./client";
import type { Entry, EntryCreate, EntryUpdate } from "../types";

export const getEntries = (project_id?: string) => {
  const qs = project_id ? `?project_id=${encodeURIComponent(project_id)}` : "";
  return apiGet<Entry[]>(`/entries${qs}`);
};

export const getEntryById = (id: string) => apiGet<Entry>(`/entries/${id}`);

export const createEntry = (data: EntryCreate) =>
  apiPost<Entry>("/entries", data);

export const updateEntry = (id: string, data: EntryUpdate) =>
  apiPut<Entry>(`/entries/${id}`, data);

export const deleteEntry = (id: string) =>
  apiDelete<{ message: string }>(`/entries/${id}`);

export const indexEntry = (id: string) =>
  apiPost<Entry>(`/entries/${id}/index`);
