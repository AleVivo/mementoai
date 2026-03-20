import { apiGet } from "./client";
import type { User } from "../types";

export const lookupUserByEmail = (email: string) =>
  apiGet<User>(`/users/search?email=${encodeURIComponent(email)}`);
