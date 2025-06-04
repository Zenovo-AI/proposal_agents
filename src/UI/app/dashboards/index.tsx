"use client";

import { useState } from "react";
import Image from "next/image";
import Artboard_3 from "../assets/Artboard_3.png";
import LoginPage from "../authentication/loginPage";
import UploadPanel from "./upload";
import ChatPanel from "./chat";
import UploadsPage from "./view";
import { useAuth } from "../authentication/useAuth";
import WinningProposalPage from "./winning_proposal";

export default function DocumentDashboardPage() {
  const [mode, setMode] = useState<"upload" | "chat" | "view" | "winning_proposal" | null>(null);
  const { user: authenticatedUser, loading } = useAuth();

  if (loading) return <p>Loading...</p>;
  if (!authenticatedUser) return <LoginPage notice={null} />;

  return (
    <main>
      <header className="app-header">
        <Image src={Artboard_3} width={250} alt="CDGA Logo" />
        <div className="user-info">
          <Image
            src={authenticatedUser.picture}
            alt="User profile"
            width={40}
            height={40}
            style={{ borderRadius: "50%", marginRight: "10px" }}
          />
          <div>
            <span><strong>Welcome, {authenticatedUser.name}</strong></span><br />
            <span>{authenticatedUser.email}</span>
          </div>
          <a
            href="#"
            onClick={async (e) => {
              e.preventDefault();
              try {
                await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/logout", {
                  method: "GET",
                  credentials: "include",
                });
              } catch (error) {
                console.error("Logout failed", error);
              }
              localStorage.removeItem("user");
              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");
              window.location.href = "/";
            }}
            className="btn btn-danger"
          >
            Logout
          </a>
        </div>
      </header>

      {!mode && (
        <div className="mode-selector">
          <p>
            {"Welcome to CDGA's Proposal Agent. I'm your virtual assistant, here to help you craft top-tier proposals rooted in CDGA's 25+ years of international engineering and consultancy experience. Whether you're preparing documentation for CTBTO or drafting a bid for a global energy client, I've got you covered. Would you like to upload a document or start drafting a proposal?"}
          </p>
          <div className="buttons">
            <button onClick={() => setMode("upload")}>📄 Upload Document</button>
            <button onClick={() => setMode("chat")}>💬 Draft Proposal</button>
            <button onClick={() => setMode("view")}>🗂️ See Uploaded Files</button>
            <button onClick={() => setMode("winning_proposal")}>🏆 Check Winning Proposals</button>
          </div>
        </div>
      )}

      {mode === "upload" && <UploadPanel onBack={() => setMode(null)} />}

      {mode === "chat" && (
        <ChatPanel
          user={authenticatedUser}
          onBack={() => setMode(null)}
        />
      )}

      {mode === "view" && (
        <div className="center-wrapper">
          <UploadsPage />
          <button
            onClick={() => setMode(null)}
            className="mt-4 px-3 py-2 bg-gray-200 rounded"
          >
            ⬅ Back
          </button>
        </div>
      )}

      {mode === "winning_proposal" && (
        <div className="center-wrapper">
          <WinningProposalPage onBack={() => setMode(null)} />
          <button
            onClick={() => setMode(null)}
            className="mt-4 px-3 py-2 bg-gray-200 rounded"
          >
            ⬅ Back
          </button>
        </div>
      )}

    </main>
  );
}
