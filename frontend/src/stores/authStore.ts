import { create } from "zustand";
import { authApi } from "@/lib/api";

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        initDataUnsafe: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
          };
        };
        ready: () => void;
        close: () => void;
        expand: () => void;
        MainButton: {
          setText: (text: string) => void;
          show: () => void;
          hide: () => void;
          onClick: (cb: () => void) => void;
        };
        themeParams: Record<string, string>;
      };
    };
  }
}

interface AuthState {
  token: string | null;
  userId: number | null;
  displayName: string;
  isLoading: boolean;

  initTelegram: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("psych_token"),
  userId: localStorage.getItem("psych_user_id")
    ? Number(localStorage.getItem("psych_user_id"))
    : null,
  displayName: "",
  isLoading: true,

  initTelegram: async () => {
    const tg = window.Telegram?.WebApp;
    if (!tg) {
      // Не в Telegram — dev mode, пробуем сохранённый токен
      const savedToken = localStorage.getItem("psych_token");
      const savedId = localStorage.getItem("psych_user_id");
      if (savedToken && savedId) {
        set({ token: savedToken, userId: Number(savedId), isLoading: false });
      } else {
        set({ isLoading: false });
      }
      return;
    }

    tg.ready();
    tg.expand();

    try {
      const { token, user_id, display_name } = await authApi.telegramAuth(
        tg.initData
      );
      localStorage.setItem("psych_token", token);
      localStorage.setItem("psych_user_id", String(user_id));
      set({ token, userId: user_id, displayName: display_name, isLoading: false });
    } catch (e) {
      console.error("Telegram auth failed:", e);
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem("psych_token");
    localStorage.removeItem("psych_user_id");
    set({ token: null, userId: null });
  },
}));
