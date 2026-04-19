import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { MetaResponse } from "../types";

export function useMeta(): MetaResponse | null {
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  useEffect(() => {
    let mounted = true;
    api.meta().then((m) => {
      if (mounted) setMeta(m);
    }).catch(() => {
      /* swallow — will retry on next mount */
    });
    return () => {
      mounted = false;
    };
  }, []);
  return meta;
}
