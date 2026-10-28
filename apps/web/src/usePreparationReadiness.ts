import { useQuery } from "@tanstack/react-query";
import type { Api } from "./api";

export function usePreparationReadiness(api: Api, owner: string) {
  return useQuery({
    queryKey: ["preparation-status", owner],
    queryFn: () => api.preparationStatus(),
    refetchInterval: 5000,
    retry: false,
  });
}
