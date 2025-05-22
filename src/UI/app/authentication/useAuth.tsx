"use client";

import { useEffect, useState } from "react";

export function useAuth() {
  const [user, setUser] = useState<{
    name: string;
    email: string;
    picture: string;
    accessToken?: string;
    refreshToken?: string;
  } | null>(null);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const storedUser = localStorage.getItem("user");
      const accessToken = localStorage.getItem("access_token");
      const refreshToken = localStorage.getItem("refresh_token");

      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        setUser({
          ...parsedUser,
          accessToken: accessToken || undefined,
          refreshToken: refreshToken || undefined,
        });
      }
    } catch {
      localStorage.removeItem("user");
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    } finally {
      setLoading(false);
    }
  }, []);

  return { user, loading };
}
