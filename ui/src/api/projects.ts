import { apiDelete, apiGet, apiPost, apiPut } from "./client";
import type { Project, ProjectCreate, ProjectUpdate, ProjectMember } from "../types";

export const getProjects = () =>
  apiGet<Project[]>("/project");

export const createProject = (data: ProjectCreate) =>
  apiPost<Project>("/project", data);

export const updateProject = (id: string, data: ProjectUpdate) =>
  apiPut<Project>(`/project/${id}`, data);

export const deleteProject = (id: string) =>
  apiDelete<void>(`/project/${id}`);

export const getProjectMembers = (id: string) =>
  apiGet<ProjectMember[]>(`/project/${id}/members`);

export const addProjectMember = (projectId: string, userId: string, role = "member") =>
  apiPost<void>(`/project/${projectId}/members`, { projectId, userId, role });

export const removeProjectMember = (projectId: string, userId: string) =>
  apiDelete<void>(`/project/${projectId}/members/${userId}`);
