// "use client";

// import { useEffect, useState } from "react";
// import { messages } from "../status/recentRFQs";

// interface RFQ {
//   document_name: string;
//   organization: string;
//   title: string;
//   deadline: string | null;
// }

// const UploadsPage = () => {
//   const [rfqs, setRfqs] = useState<RFQ[]>([]);
//   const [searchQuery, setSearchQuery] = useState("");
//   const [searchResults, setSearchResults] = useState<RFQ[] | null>(null);
//   const [loading, setLoading] = useState(false);
//   const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

//   useEffect(() => {
//     const fetchRecentRFQs = async () => {
//       try {
//         const res = await fetch("http://localhost:8000/recent-rfqs", {
//           method: "GET",
//           credentials: "include",
//         });
//         const data = await res.json();
//         setRfqs(data.rfqs);
//       } catch (error) {
//         console.error("Failed to fetch recent RFQs", error);
//       }
//     };

//     fetchRecentRFQs();

//     const interval = setInterval(() => {
//       setCurrentMessageIndex((prevIndex) => (prevIndex + 1) % messages.length);
//     }, 5000);

//     return () => clearInterval(interval);
//   }, []);

//   const handleSearch = async () => {
//     if (!searchQuery.trim()) return;

//     setLoading(true);
//     try {
//       const res = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/search-rfqs", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ query: searchQuery }),
//         credentials: "include",
//       });

//       const data = await res.json();
//       setSearchResults(data.results);
//     } catch (error) {
//       console.error("Search failed", error);
//       setSearchResults([]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <>
//       {/* Show placeholder above uploads-page */}
//       {(!rfqs || rfqs.length === 0) && !loading && (
//         <div className="center-wrapper">
//           <div className="placeholder-message">
//             {messages[currentMessageIndex]}
//           </div>
//         </div>
//       )}

//       <div className="uploads-page">
//         <div className="search-section">
//           <input
//             type="text"
//             placeholder="Search RFQs..."
//             value={searchQuery}
//             onChange={(e) => setSearchQuery(e.target.value)}
//           />
//           <button onClick={handleSearch} disabled={loading}>
//             {loading ? "Searching..." : "Search"}
//           </button>
//         </div>

//         <h2>Recent RFQs</h2>
//         <div className="rfq-scroll-container">
//           <ul className="rfq-list">
//             {rfqs.map((rfq, index) => (
//               <li key={rfq.document_name || index} className="rfq-item">
//                 <p><strong>Title:</strong> {rfq.title}</p>
//                 <p><strong>Organization:</strong> {rfq.organization}</p>
//                 {rfq.deadline && (
//                   <p><strong>Deadline:</strong> {new Date(rfq.deadline).toLocaleDateString()}</p>
//                 )}
//                 {rfq.document_name && (
//                   <p><strong>RFQ Name:</strong> {rfq.document_name}</p>
//                 )}
//               </li>
              
//             ))}
//           </ul>
//         </div>

//         {searchResults && (
//           <div className="search-results">
//             <h3>Search Results</h3>
//             {searchResults.length > 0 ? (
//               <ul className="rfq-list">
//                 {searchResults.map((result, index) => (
//                   <li key={result.document_name || index} className="rfq-item">
//                     <p><strong>Title:</strong> {result.title}</p>
//                     <p><strong>Organization:</strong> {result.organization}</p>
//                     {result.deadline && (
//                       <p><strong>Deadline:</strong> {new Date(result.deadline).toLocaleDateString()}</p>
//                     )}
//                     {result.document_name && (
//                       <p><strong>RFQ Name:</strong> {result.document_name}</p>
//                     )}
//                   </li>
//                 ))}
//               </ul>
//             ) : (
//               <p>No results found for &quot;{searchQuery}&quot;.</p>
//             )}
//           </div>
//         )}
//       </div>
//     </>
//   );
// };

// export default UploadsPage;



"use client";

import { useEffect, useState } from "react";
import { messages } from "../status/recentRFQs";

interface RFQ {
  document_name: string;
  organization: string;
  title: string;
  deadline: string | null;
}

type UploadsPageProps = {
  onSelectRfq?: (docName: string, chatMode: "local" | "hybrid") => void;
};

export default function UploadsPage({ onSelectRfq }: UploadsPageProps) {
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<RFQ[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [selectedChatMode, setSelectedChatMode] = useState<"local" | "hybrid">("local");

  useEffect(() => {
    const fetchRecentRFQs = async () => {
      try {
        const res = await fetch("https://api.zenovo.ai/api/recent-rfqs", {
          method: "GET",
          credentials: "include",
        });
        const data = await res.json();
        setRfqs(data.rfqs);
      } catch (err) {
        console.error("Failed to fetch recent RFQs", err);
      }
    };
    fetchRecentRFQs();

    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % messages.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("https://api.zenovo.ai/api/search-rfqs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery }),
        credentials: "include",
      });
      const data = await res.json();
      setSearchResults(data.results);
    } catch (err) {
      console.error("Search failed", err);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClick = (docName: string) => {
    if (onSelectRfq) {
      onSelectRfq(docName, selectedChatMode);
    }
  };

  const renderRFQItem = (rfq: RFQ) => (
    <li
      key={rfq.document_name}
      className="rfq-item"
      onClick={() => handleClick(rfq.document_name)}
      style={{ cursor: "pointer" }}
    >
      <p><strong>Title:</strong> {rfq.title}</p>
      <p><strong>Organization:</strong> {rfq.organization}</p>
      {rfq.deadline && (
        <p><strong>Deadline:</strong> {new Date(rfq.deadline).toLocaleDateString()}</p>
      )}
      <p><strong>RFQ Name:</strong> {rfq.document_name}</p>
    </li>
  );

  return (
    <>
      {!rfqs.length && !loading && (
        <div className="center-wrapper">
          <div className="placeholder-message">{messages[currentMessageIndex]}</div>
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

        <div className="chat-mode-selector">
          <label>
            <strong>Select Chat Mode:</strong>
            <select
              value={selectedChatMode}
              onChange={(e) => setSelectedChatMode(e.target.value as "local" | "hybrid")}
              style={{ marginLeft: "10px" }}
            >
              <option value="local">Local (specific RFQ)</option>
              <option value="hybrid">Hybrid (across sources)</option>
            </select>
          </label>
        </div>

        <h2>Recent RFQs</h2>
        <div className="rfq-scroll-container">
          <ul className="rfq-list">{rfqs.map(renderRFQItem)}</ul>
        </div>

        {searchResults && (
          <div className="search-results">
            <h3>Search Results</h3>
            {searchResults.length > 0 ? (
              <ul className="rfq-list">{searchResults.map(renderRFQItem)}</ul>
            ) : (
              <p>No results found for “{searchQuery}”.</p>
            )}
          </div>
        )}
      </div>
    </>
  );
}
