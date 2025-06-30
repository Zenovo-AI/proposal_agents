"use client";
import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

export function InactivityLogout() {
  const router = useRouter();
  const timerRef = useRef<number>(0);
  const EXPIRY = 2 * 60 * 60 * 1000; // 2 hours

  const resetTimer = () => {
    localStorage.setItem("lastActivity", Date.now().toString());
  };

  useEffect(() => {
    resetTimer(); // init timestamp

    // Listen for user activity
    const events = ["mousemove", "click", "keydown", "scroll", "touchstart"];
    events.forEach((ev) => window.addEventListener(ev, resetTimer, { passive: true }));

    // Poll every minute to check inactivity
    const interval = window.setInterval(() => {
      const last = parseInt(localStorage.getItem("lastActivity") || "0", 10);
      if (Date.now() - last > EXPIRY) {
        localStorage.removeItem("lastActivity");
        localStorage.removeItem("user");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        // Clear cookie
        document.cookie = `user_session=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;SameSite=None`;
        router.replace("/?notice=Session+expired+due+to+inactivity");
      }
    }, 60 * 1000);

    return () => {
      clearInterval(interval);
      events.forEach((ev) => window.removeEventListener(ev, resetTimer));
    };
  }, [router]);

  return null;
}
