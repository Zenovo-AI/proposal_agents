// "use client";

// import { useState } from "react";
// import Image from "next/image";
// import Artboard_3 from "../assets/Artboard_3.png";
// import LoginPage from "../authentication/loginPage";
// import UploadPanel from "./upload";
// import ChatPanel from "./chat";
// import UploadsPage from "./view";
// import { useAuth } from "../authentication/useAuth";
// import WinningProposalPage from "./winning_proposal";

// export default function DocumentDashboardPage() {
//   const [mode, setMode] = useState<"upload" | "chat" | "view" | "winning_proposal" | null>(null);
//   const { user: authenticatedUser, loading } = useAuth();

//   if (loading) return <p>Loading...</p>;
//   if (!authenticatedUser) return <LoginPage notice={null} />;

//   return (
//     <main>
//       <header className="app-header">
//         <Image src={Artboard_3} width={250} alt="CDGA Logo" />
//         <div className="user-info">
//           <Image
//             src={authenticatedUser.picture}
//             alt="User profile"
//             width={40}
//             height={40}
//             style={{ borderRadius: "50%", marginRight: "10px" }}
//           />
//           <div>
//             <span><strong>Welcome, {authenticatedUser.name}</strong></span><br />
//             <span>{authenticatedUser.email}</span>
//           </div>
          // <a
          //   href="#"
          //   onClick={async (e) => {
          //     e.preventDefault();
          //     try {
          //       await fetch("http://localhost:8000/logout", {
          //         method: "GET",
          //         credentials: "include",
          //       });
          //     } catch (error) {
          //       console.error("Logout failed", error);
          //     }
          //     localStorage.removeItem("user");
          //     localStorage.removeItem("access_token");
          //     localStorage.removeItem("refresh_token");
          //     window.location.href = "/";
          //   }}
          //   className="btn btn-danger"
          // >
          //   Logout
          // </a>
//         </div>
//       </header>

//       {!mode && (
//         <div className="mode-selector">
//           <p>
//             {"Welcome to CDGA's Proposal Agent. I'm your virtual assistant, here to help you craft top-tier proposals rooted in CDGA's 25+ years of international engineering and consultancy experience. Whether you're preparing documentation for CTBTO or drafting a bid for a global energy client, I've got you covered. Would you like to upload a document or start drafting a proposal?"}
//           </p>
//           <div className="buttons">
//             <button onClick={() => setMode("upload")}>📄 Upload Document</button>
//             <button onClick={() => setMode("chat")}>💬 Draft Proposal</button>
//             <button onClick={() => setMode("view")}>🗂️ See Uploaded Files</button>
//             <button onClick={() => setMode("winning_proposal")}>🏆 Check Winning Proposals</button>
//           </div>
//         </div>
//       )}

//       {mode === "upload" && <UploadPanel onBack={() => setMode(null)} />}

//       {mode === "chat" && (
//         <ChatPanel
//           user={authenticatedUser}
//           onBack={() => setMode(null)}
//         />
//       )}

//       {mode === "view" && (
//         <div className="center-wrapper">
//           <UploadsPage />
//           <button
//             onClick={() => setMode(null)}
//             className="mt-4 px-3 py-2 bg-gray-200 rounded"
//           >
//             ⬅ Back
//           </button>
//         </div>
//       )}

//       {mode === "winning_proposal" && (
//         <div className="center-wrapper">
//           <WinningProposalPage onBack={() => setMode(null)} />
//           <button
//             onClick={() => setMode(null)}
//             className="mt-4 px-3 py-2 bg-gray-200 rounded"
//           >
//             ⬅ Back
//           </button>
//         </div>
//       )}

//     </main>
//   );
// }



"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import Artboard_3 from "../assets/Artboard_3.png";
import LoginPage from "../authentication/loginPage";
import UploadPanel from "./upload";
import ChatPanelWithSuspense from "./ChatPanelWithSuspense";
import UploadsPage from "./view";
import WinningProposalPage from "./winning_proposal";
import { useAuth } from "../authentication/useAuth";

export default function DocumentDashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const initialMode = (searchParams.get("mode") as
    | "upload"
    | "chat"
    | "view"
    | "winning_proposal"
    | null) ?? null;
  const initialRfq = searchParams.get("rfq") || null;
  const initialChatMode = searchParams.get("chat_mode") || "local";

  const [mode, setMode] = useState(initialMode);
  const [rfqId, setRfqId] = useState<string | null>(initialRfq);
  const [chatMode, setChatMode] = useState<string>(initialChatMode);

  const { user: authenticatedUser, loading } = useAuth();

  const handleSelectRfq = (docName: string, selectedChatMode: "local" | "hybrid") => {
    setRfqId(docName);
    setChatMode(selectedChatMode);
    setMode("chat");
  };


  // Update URL without full reload (shallow)
  useEffect(() => {
    const params = new URLSearchParams();
    if (mode) params.set("mode", mode);
    if (rfqId) params.set("rfq", rfqId);
    if (chatMode) params.set("chat_mode", chatMode);
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  }, [mode, rfqId, chatMode, router, pathname, searchParams]);

  if (loading) return <p>Loading...</p>;
  if (!authenticatedUser) return <LoginPage notice={null} />;


  return (
    <main>
      <header className="app-header">
        <Image src={Artboard_3} width={250} alt="CDGA Logo" />
        <div className="user-info">
          <Image
            src={authenticatedUser.picture}
            alt="User"
            width={40}
            height={40}
            style={{ borderRadius: "50%", marginRight: "10px" }}
          />
          <div>
            <strong>Welcome, {authenticatedUser.name}</strong><br />
            <span>{authenticatedUser.email}</span>
          </div>
          <a
            href="#"
            onClick={async (e) => {
              e.preventDefault();
              try {
                await fetch("https://api.zenovo.ai/api/logout", {
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
          <p>{"Welcome to CDGA's Proposal Agent. I'm your virtual assistant, here to help you craft top-tier proposals rooted in CDGA's 25+ years of international engineering and consultancy experience. Whether you're preparing documentation for CTBTO or drafting a bid for a global energy client, I've got you covered. What would you like to do:"}</p>
          <div className="buttons">
            <button onClick={() => setMode("upload")}>📄 Upload Document</button>
            <button onClick={() => setMode("chat")}>💬 Draft Proposal</button>
            <button onClick={() => setMode("view")}>🗂️ View RFQs</button>
            <button onClick={() => setMode("winning_proposal")}>🏆 Winning Proposals</button>
          </div>
        </div>
      )}

      {mode === "upload" && (
        <UploadPanel onBack={() => { setMode(null); setRfqId(null); }} />
      )}

      {mode === "view" && (
        <>
          <UploadsPage onSelectRfq={handleSelectRfq} />
          <button onClick={() => setMode(null)} className="mt-4 px-4 py-2 bg-gray-200 rounded">
            ⬅ Back
          </button>
        </>
      )}

      {mode === "chat" && (
        <ChatPanelWithSuspense
          user={authenticatedUser}
          rfqId={rfqId ?? undefined}
          chatMode={chatMode}
          showChatModeSelector={!rfqId}
          onBack={() => {
            setMode(null);
            setRfqId(null);
            setChatMode("local");
          }}
        />
      )}

      {mode === "winning_proposal" && (
        <WinningProposalPage onBack={() => setMode(null)} />
      )}
    </main>
  );
}
