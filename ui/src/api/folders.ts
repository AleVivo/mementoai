import { apiDelete, apiGet, apiPost, apiPut } from "./client";
import type { FolderCreate, FolderMove, FolderResponse, FolderTree, FolderUpdate } from "../types";

const base = (projectId: string) => `/projects/${encodeURIComponent(projectId)}/folders`;

export const getFolderTree = (projectId: string) =>
  apiGet<FolderTree[]>(base(projectId));

export const createFolder = (projectId: string, data: FolderCreate) =>
  apiPost<FolderResponse>(base(projectId), data);

export const renameFolder = (projectId: string, folderId: string, data: FolderUpdate) =>
  apiPut<FolderResponse>(`${base(projectId)}/${folderId}`, data);

export const moveFolder = (projectId: string, folderId: string, data: FolderMove) =>
  apiPut<FolderResponse>(`${base(projectId)}/${folderId}/move`, data);

export const deleteFolder = (projectId: string, folderId: string) =>
  apiDelete<void>(`${base(projectId)}/${folderId}`);
