import { apiPost } from "./client";
import type { SearchRequest, SearchResult } from "../types";

export const searchEntries = (data: SearchRequest) =>
  apiPost<SearchResult[]>("/search", data);
