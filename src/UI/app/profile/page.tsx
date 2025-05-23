/**
 * this is a client component
 * and it is used to display the login page
 * and handle the login process
 * and it is used to display the login page
 */ 


"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function ProfilePage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [user, setUser] = useState<{ name: string; email: string; picture: string } | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const name = searchParams.get("name");
    const email = searchParams.get("email");
    const picture = searchParams.get("picture");
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");

    if (name && email && picture) {
      const userData = { name, email, picture };
      setUser(userData);
      localStorage.setItem("user", JSON.stringify(userData));

      if (accessToken) {
        localStorage.setItem("access_token", accessToken);
      }

      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
      }

      // Trigger animation on next tick
      setTimeout(() => setVisible(true), 100);
    }
  }, [searchParams]);

  if (!user) return <p>Loading user info...</p>;

  return (
    <>
      {/* This keeps your existing layout intact */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          right: "5vw",
          transform: visible ? "translateY(-50%) translateX(0)" : "translateY(-50%) translateX(150%)",
          opacity: visible ? 1 : 0,
          transition: "all 0.8s ease",
          backgroundColor: "#fff",
          padding: "30px",
          borderRadius: "12px",
          boxShadow: "0 10px 30px rgba(0,0,0,0.1)",
          width: "350px",
          textAlign: "center",
          zIndex: 10,
        }}
      >
        <h2>Welcome, {user.name}</h2>
        <p>{user.email}</p>
        <img
          src={user.picture}
          alt={`${user.name}'s profile`}
          style={{
            width: "120px",
            height: "120px",
            borderRadius: "50%",
            objectFit: "cover",
            margin: "20px 0",
          }}
        />
        <button
          onClick={() => router.push("/")}
          style={{
            padding: "10px 20px",
            fontSize: "16px",
            borderRadius: "5px",
            border: "none",
            backgroundColor: "#0070f3",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          Proceed to Proposal Assistant
        </button>
      </div>
    </>
  );
}
