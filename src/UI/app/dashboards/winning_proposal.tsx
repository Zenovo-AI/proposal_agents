// "use client";

// import React, { useEffect, useState } from "react";

// type Proposal = {
//   proposal_id: string;
//   proposal_title: string;
//   proposal_content: string;
//   created_at: string | null;
// };

// function isValidDate(date: string | null): boolean {
//   return !!date && !isNaN(Date.parse(date));
// }

// type WinningProposalPageProps = {
//   onBack: () => void;
// };

// const WinningProposalPage = ({ onBack }: WinningProposalPageProps) => {
//   const [proposals, setProposals] = useState<Proposal[]>([]);
//   const [loading, setLoading] = useState<boolean>(false);
//   const [error, setError] = useState<string | null>(null);

//   useEffect(() => {
//     const fetchWinningProposals = async () => {
//       setLoading(true);
//       setError(null);
//       try {
//         const response = await fetch("http://localhost:8000/winning-proposals", {
//           method: "GET",
//           credentials: "include",
//         });

//         if (!response.ok) {
//           throw new Error(`Failed to fetch proposals: ${response.statusText}`);
//         }

//         const data = await response.json();
//         setProposals(data.proposals || []);
//       } catch (err: any) {
//         setError(err.message || "Unknown error");
//       } finally {
//         setLoading(false);
//       }
//     };

//     fetchWinningProposals();
//   }, []);

//   return (
//     <main style={{ maxWidth: 800, margin: "auto", padding: "1rem" }}>
//       <h1>Winning Proposals</h1>

//       {loading && <p>Loading proposals...</p>}
//       {error && <p style={{ color: "red" }}>Error: {error}</p>}

//       {!loading && proposals.length === 0 && <p>No winning proposals found.</p>}

//       {!loading &&
//         proposals.map((proposal) => (
//           <article
//             key={proposal.proposal_id}
//             style={{
//               border: "1px solid #ccc",
//               padding: "1rem",
//               marginBottom: "1rem",
//               borderRadius: "6px",
//               backgroundColor: "#f0fff0",
//             }}
//           >
//             <h2>{proposal.proposal_title}</h2>
//             <p>
//               {proposal.proposal_content
//                 ? proposal.proposal_content.slice(0, 300) + "..."
//                 : "No content available."}
//             </p>
//             <p>
//               <strong>Submitted:</strong>{" "}
//               {isValidDate(proposal.created_at)
//                 ? new Date(proposal.created_at!).toLocaleDateString()
//                 : "Unknown"}
//             </p>
//           </article>
//         ))}
//     </main>
//   );
// };

// export default WinningProposalPage;



"use client";

import React, { useEffect, useState } from "react";

type Proposal = {
  proposal_id: string;
  proposal_title: string;
  proposal_content: string;
  created_at: string | null;
  rfq_id?: string | number | null;
};

function isValidDate(date: string | null): boolean {
  return !!date && !isNaN(Date.parse(date));
}

type WinningProposalPageProps = {
  onBack: () => void;
};

const WinningProposalPage = ({ onBack }: WinningProposalPageProps) => {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [exportingIds, setExportingIds] = useState<Set<string>>(new Set());
  const [exportUrls, setExportUrls] = useState<Record<string, string>>({});
  const [exportErrors, setExportErrors] = useState<Record<string, string>>({});

  // Get refresh token from localStorage
  const getRefreshToken = (): string | null => {
    try {
      return localStorage.getItem("refresh_token");
    } catch {
      return null;
    }
  };

  useEffect(() => {
    const fetchWinningProposals = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/winning-proposals", {
          method: "GET",
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch proposals: ${response.statusText}`);
        }

        const data = await response.json();
        setProposals(data.proposals || []);
      } catch (err: any) {
        setError(err.message || "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchWinningProposals();
  }, []);

  const handleExportToDrive = async (proposal: Proposal) => {
    const refreshToken = getRefreshToken();

    if (!refreshToken) {
      alert("Missing Google OAuth refresh token in localStorage.");
      return;
    }

    setExportErrors((prev) => {
      const copy = { ...prev };
      delete copy[proposal.proposal_id];
      return copy;
    });

    setExportingIds((prev) => new Set(prev).add(proposal.proposal_id));
    setExportUrls((prev) => {
      const copy = { ...prev };
      delete copy[proposal.proposal_id];
      return copy;
    });

    const payload = {
      state: {
        messages: [
          { role: "assistant", content: proposal.proposal_content || "" },
          {
            role: "assistant",
            content: "✅ Proposal approved. You can now upload it to Google Docs.",
          },
        ],
      },
      refresh_token: refreshToken,
      rfq_id: proposal.rfq_id || null,
      is_winning: true,
    };

    try {
      const response = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/save-to-drive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const message =
          errorData?.error || `Failed to save to Drive: ${response.statusText}`;
        throw new Error(message);
      }

      const data = await response.json();
      setExportUrls((prev) => ({ ...prev, [proposal.proposal_id]: data.view_link }));
    } catch (error: any) {
      setExportErrors((prev) => ({
        ...prev,
        [proposal.proposal_id]: error.message || "Unknown export error",
      }));
    } finally {
      setExportingIds((prev) => {
        const copy = new Set(prev);
        copy.delete(proposal.proposal_id);
        return copy;
      });
    }
  };

  return (
    <main className="scrollable-main">
      <h1>Winning Proposals</h1>

      {loading && <p>Loading proposals...</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {!loading && proposals.length === 0 && <p>No winning proposals found.</p>}

      {!loading &&
        proposals.map((proposal) => {
          const isExporting = exportingIds.has(proposal.proposal_id);
          const exportUrl = exportUrls[proposal.proposal_id];
          const exportError = exportErrors[proposal.proposal_id];

          return (
            <article
              key={proposal.proposal_id}
              style={{
                border: "1px solid #ccc",
                padding: "1rem",
                marginBottom: "1rem",
                borderRadius: "6px",
                backgroundColor: "#f0fff0",
              }}
            >
              <h2>{proposal.proposal_title}</h2>
              <p>
                {proposal.proposal_content
                  ? proposal.proposal_content.slice(0, 300) + "..."
                  : "No content available."}
              </p>
              <p>
                <strong>Submitted:</strong>{" "}
                {isValidDate(proposal.created_at)
                  ? new Date(proposal.created_at!).toLocaleDateString()
                  : "Unknown"}
              </p>

              <button
                onClick={() => handleExportToDrive(proposal)}
                disabled={!proposal.proposal_content || isExporting}
              >
                {isExporting ? "Exporting..." : "Re-export to Google Drive"}
              </button>

              {exportUrl && (
                <p style={{ marginTop: "0.5rem" }}>
                  Exported document:{" "}
                  <a href={exportUrl} target="_blank" rel="noopener noreferrer">
                    View Document
                  </a>
                </p>
              )}

              {exportError && (
                <p style={{ color: "red", marginTop: "0.5rem" }}>
                  Export error: {exportError}
                </p>
              )}
            </article>
          );
        })}
    </main>
  );
};

export default WinningProposalPage;
