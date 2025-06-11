"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../authentication/useAuth";
import { uploadToGoogleDocs } from "../googledoc_upload/googleDrive";

type RFQ = {
  id: string;
  title: string;
  created_at: string;
};

type Proposal = {
  id: string;
  rfq_id: string;
  title: string;
  content: string;
  is_winning: boolean;
  created_at: string;
};

type RecentActivityPageProps = {
  onBack: () => void;
};

function isValidDate(date: string | undefined): boolean {
  return !!date && !isNaN(Date.parse(date));
}


const RecentActivityPage = ({ onBack }: RecentActivityPageProps) => {
  const { user: authenticatedUser, loading } = useAuth();
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loadingData, setLoadingData] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!authenticatedUser) return;

    const fetchRecentActivity = async () => {
      setLoadingData(true);

      try {
        const res = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/api/recent-activity", {
          method: "GET",
          credentials: "include",
        });

        if (!res.ok) {
          console.error("Failed to fetch recent activity");
          return;
        }

        const data = await res.json();
        setRfqs(data?.rfqs || []);
        setProposals(data?.proposals || []);
      } catch (error) {
        console.error("Error fetching recent activity", error);
      } finally {
        setLoadingData(false);
      }
    };

    fetchRecentActivity();
  }, [authenticatedUser]);

  const handleReupload = async (proposal: Proposal) => {
    setUploading(true);

    try {
      const link = await uploadToGoogleDocs({
        proposalText: proposal.content,
        state: { messages: [] },
        rfq_id: proposal.rfq_id,
        is_winning: proposal.is_winning,
      });

      if (link) {
        window.open(link, "_blank");
      }
    } catch (err) {
      console.error("Error uploading to Google Docs", err);
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <p>Loading authentication...</p>;
  if (!authenticatedUser) return <p>Please log in to view recent activity.</p>;

  return (
    <main>
      <h1>Recent RFQs and Proposals (Last 30 Days)</h1>

      {loadingData && <p>Loading recent activity...</p>}

      {!loadingData && rfqs.length === 0 && <p>No recent RFQs found.</p>}

      {!loadingData &&
        rfqs.map((rfq) => {
          const relatedProposals = proposals.filter((p) => p.rfq_id === rfq.id);

          return (
            <section className="rfq-section" key={rfq.id}>
              <h2>RFQ: {rfq.title}</h2>
              <small>
                Created: {isValidDate(rfq.created_at) ? new Date(rfq.created_at).toLocaleDateString() : "Unknown"}
              </small>


              {relatedProposals.length === 0 && <p>No proposals submitted yet.</p>}

              {relatedProposals.map((proposal, index) => (
                <article
                  className={`proposal-card ${proposal.is_winning ? "winning" : ""}`}
                  key={proposal.id || `${proposal.rfq_id}-${index}`}

                >
                  <h3>
                    {proposal.title}{" "}
                    {proposal.is_winning && (
                      <span className="winning-badge">Winning Proposal</span>
                    )}
                  </h3>
                  <p>{proposal.content ? proposal.content.slice(0, 300) + "..." : "No content available."}</p>
                  <small>
                    Submitted: {isValidDate(proposal.created_at) ? new Date(proposal.created_at).toLocaleDateString() : "Unknown"}
                  </small>


                  <div className="button-group">
                    <button
                      onClick={() => handleReupload(proposal)}
                      disabled={uploading}
                      className="upload-button"
                    >
                      📄 Re-export to Google Drive
                    </button>
                  </div>
                </article>
              ))}
            </section>
          );
        })}

      <button onClick={onBack} className="back-button">⬅ Back</button>
    </main>
  );
};

export default RecentActivityPage;
