import { apiGet, apiPut } from "./client";
import type { ConfigSection, ConfigUpdateRequest } from "../types";

export const getAllConfig = () =>
  apiGet<ConfigSection[]>("/admin/config");

export const getConfigSection = (sectionId: string) =>
  apiGet<ConfigSection>(`/admin/config/${sectionId}`);

export const updateConfigSection = (sectionId: string, body: ConfigUpdateRequest) =>
  apiPut<ConfigSection>(`/admin/config/${sectionId}`, body);