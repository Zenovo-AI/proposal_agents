"use client";

import { useEffect, useState } from "react";
import { messages } from "../status/recentRFQs"

interface RFQ {
  document_name: string;
  organization: string;
  title: string;
  deadline: string | null;
}

const UploadsPage = () => {
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<RFQ[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

  useEffect(() => {
    const fetchRecentRFQs = async () => {
      try {
        const res = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/recent-rfqs", {
          method: "GET",
          credentials: "include",
        });
        const data = await res.json();
        setRfqs(data.rfqs);
      } catch (error) {
        console.error("Failed to fetch recent RFQs", error);
      }
    };

    fetchRecentRFQs();

    const interval = setInterval(() => {
      setCurrentMessageIndex((prevIndex) => (prevIndex + 1) % messages.length);
    }, 5000);

    return () => clearInterval(interval);
  }, []);


  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const res = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/search-rfqs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: searchQuery }),
        credentials: "include"
      });

      const data = await res.json();
      setSearchResults(data.results);
    } catch (error) {
      console.error("Search failed", error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };
  console.log("RFQs received:", rfqs);

    return (
    <>
        {/* Show placeholder above uploads-page */}
        {(!rfqs || rfqs.length === 0) && !loading && (
        <div className="center-wrapper">
            <div className="placeholder-message">
            {messages[currentMessageIndex]}
            </div>
        </div>
        )}

        <div className="uploads-page">
        <div className="search-section">
            <input
            type="text"
            placeholder="Search RFQs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button onClick={handleSearch} disabled={loading}>
            {loading ? "Searching..." : "Search"}
            </button>
        </div>

        <h2>Recent RFQs</h2>
        <div className="rfq-scroll-container">
          <ul className="rfq-list">
            {rfqs && rfqs.map((rfq) => (
              <li key={rfq.document_name}>
                <p className="rfq-title">{rfq.title}</p>
                <p className="rfq-org">{rfq.organization}</p>
                {rfq.deadline && (
                  <p className="rfq-deadline">
                    Deadline: {new Date(rfq.deadline).toLocaleDateString()}
                  </p>
                )}
                {rfq.document_name && (
                  <p className="rfq-doc">Document: {rfq.document_name}</p>
                )}
                {/* Add more fields as needed */}
              </li>
            ))}
          </ul>
        </div>



        {searchResults && (
            <div className="search-results">
            <h3>Search Results</h3>
            {searchResults.length > 0 ? (
                <ul className="rfq-list">
                {searchResults.map((result) => (
                    <li key={result.document_name} className="rfq-item">
                    <p className="rfq-title">{result.title}</p>
                    <p className="rfq-org">{result.organization}</p>
                    {result.deadline && (
                        <p className="rfq-deadline">
                        Deadline: {new Date(result.deadline).toLocaleDateString()}
                        </p>
                    )}
                    </li>
                ))}
                </ul>
            ) : (
                <p>No results found for &quot;{searchQuery}&quot;.</p>
            )}
            </div>
        )}
        </div>
    </>
    );
};

export default UploadsPage;
