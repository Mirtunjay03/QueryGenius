import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { getMe, type TokenResponse, type User } from "../api/auth";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isLoading: boolean;
  setTokens: (tokens: TokenResponse) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(() =>
    localStorage.getItem("qg_access_token"),
  );
  const [refreshToken, setRefreshToken] = useState<string | null>(() =>
    localStorage.getItem("qg_refresh_token"),
  );
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(accessToken));

  useEffect(() => {
    if (!accessToken) {
      setIsLoading(false);
      return;
    }
    let active = true;
    getMe(accessToken)
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) {
          setUser(null);
          setAccessToken(null);
          setRefreshToken(null);
          localStorage.removeItem("qg_access_token");
          localStorage.removeItem("qg_refresh_token");
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [accessToken]);

  const value = useMemo<AuthState>(
    () => ({
      accessToken,
      refreshToken,
      user,
      isLoading,
      setTokens(tokens) {
        localStorage.setItem("qg_access_token", tokens.access_token);
        localStorage.setItem("qg_refresh_token", tokens.refresh_token);
        setAccessToken(tokens.access_token);
        setRefreshToken(tokens.refresh_token);
      },
      logout() {
        localStorage.removeItem("qg_access_token");
        localStorage.removeItem("qg_refresh_token");
        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
      },
    }),
    [accessToken, refreshToken, user, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
