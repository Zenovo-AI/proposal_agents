"use client"

import { useEffect, useState } from "react"
import { useCustomChat } from "../components/Hooks"
import { Message } from "ai"
import ReactMarkdown from "react-markdown"
import LoadingBubble from "../components/LoadingBubble"
import PromptSuggestionsRow from "../components/PromptSuggestionsRow"
import TypeaheadPrompts from "../components/TypeAheadSuggestions"
import { COMMON_PROMPTS } from "../typing_assistants/commonprompts"
import { FEEDBACK_OPTIONS } from "../typing_assistants/feedbackoptions"
import { uploadToGoogleDocs } from "../googledoc_upload/googleDrive"
import { usePathname, useRouter, useSearchParams } from "next/navigation"

type User = {
  email: string
  name: string
  picture: string
}

export type ChatPanelProps = {
  user?: User;
  onBack: () => void;
  rfqId?: string | null;
  chatMode?: string | null;
  showChatModeSelector?: boolean;
};


const ChatPanel = ({ onBack, rfqId, chatMode, showChatModeSelector }: ChatPanelProps) => {
  const [uploading, setUploading] = useState(false)
  const [isWinningChecked, setIsWinningChecked] = useState(false)
  const [docLink, setDocLink] = useState<string | null>(null)

  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const rfqIdFromUrl = searchParams.get("rfq") ?? ""
  const effectiveRfqId = rfqId ?? rfqIdFromUrl
  

  const initialMode = (searchParams.get("mode") as "local" | "hybrid") || "local"
  const [mode, setChatMode] = useState<"local" | "hybrid">(chatMode as "local" | "hybrid" || initialMode)

  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString())
    params.set("mode", mode)
    router.push(`${pathname}?${params.toString()}`, { scroll: false })
  }, [mode, router, pathname, searchParams])

  const queryUrl = `https://api.zenovo.ai/api/retrieve?rfq=${encodeURIComponent(effectiveRfqId)}&mode=${mode}`
  console.log("💡 Effective RFQ ID:", effectiveRfqId);

  const {
    append,
    isLoading,
    messages,
    input,
    setInput,
    handleInputChange,
    handleSubmit,
    interrupted,
    error,
    setError,
  } = useCustomChat(queryUrl, effectiveRfqId, mode)

  const noMessages = messages.length === 0
  const isApproved = messages.length > 0 && messages.at(-1)!.content.includes("✅ Proposal approved")

  useEffect(() => {
    if (!noMessages) {
      const container = document.querySelector("section.populated")
      if (container) container.scrollTop = container.scrollHeight
    }
  }, [messages, isLoading, noMessages])

  const handlePrompt = (promptText: string) => {
    const msg: Message = {
      id: crypto.randomUUID(),
      content: promptText,
      role: "user",
    }
    append(msg)
  }

  return (
    <>
      {showChatModeSelector && (
        <div className="chat-mode-selector">
          <p>Select chat mode:</p>
          <div className="chat-mode-button-container">
            <button
              onClick={() => setChatMode("local")}
              className={`chat-mode-button ${chatMode === "local" ? "selected" : ""}`}
            >
              Local
            </button>
            <button
              onClick={() => setChatMode("hybrid")}
              className={`chat-mode-button ${chatMode === "hybrid" ? "selected" : ""}`}
            >
              Hybrid
            </button>
          </div>
          {noMessages && !showChatModeSelector && (
              <PromptSuggestionsRow onPromptClick={handlePrompt} rfqId={effectiveRfqId} />
            )}
        </div>
      )}


      <section className={noMessages ? "" : "populated"}>
        {noMessages ? (
          <>
            <p className="starter-text">
             {"Welcome to CDGA's Proposal Assistant. I'm here to help you draft professional, standards-aligned proposals tailored to international engineering and consultancy work."}
            </p>
            <PromptSuggestionsRow onPromptClick={handlePrompt} rfqId={effectiveRfqId} />
          </>
        ) : (
          <>
            {messages.map((message, idx) => (
              <div
                key={`msg-${idx}`}
                className={`chat-bubble ${
                  message.role === "assistant" ? "assistant" : "user"
                }`}
              >
                <div className="bubble-label">
                  {message.role === "assistant" ? "CDGA‑AI" : "You"}
                </div>
                <div className="bubble-content">
                  {message.role === "assistant" ? (
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
              </div>
            ))}


            {isLoading && (
              <div className="chat-ans-bubble">
                <LoadingBubble />
              </div>
            )}

            {isApproved && (
              <div className="upload-section">
                {!uploading && (
                  <>
                    <label style={{ display: "block", marginBottom: "0.5rem" }}>
                      <input
                        type="checkbox"
                        checked={isWinningChecked}
                        onChange={(e) => setIsWinningChecked(e.target.checked)}
                        style={{ marginRight: "0.5rem" }}
                      />
                      Mark this proposal as a winning proposal
                    </label>

                    <button
                      onClick={async () => {
                        const lastUserMessage = [...messages].reverse().find((msg) => msg.role === "user")
                        if (!lastUserMessage?.content) return

                        setUploading(true)

                        const rfq_id = lastUserMessage.id || "unknown"

                        const link = await uploadToGoogleDocs({
                          proposalText: lastUserMessage.content,
                          state: { messages },
                          is_winning: isWinningChecked,
                          rfq_id,
                        })

                        setUploading(false)

                        if (link) {
                          setDocLink(link)
                          window.open(link, "_blank")
                        }
                      }}
                      disabled={uploading}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        padding: "0.5rem 1rem",
                        fontSize: "1rem",
                        cursor: uploading ? "not-allowed" : "pointer",
                        opacity: uploading ? 0.6 : 1,
                        border: "1px solid #ccc",
                        borderRadius: "6px",
                        backgroundColor: "#9b30ff",
                      }}
                    >
                      📄 Upload Approved Proposal to Google Docs
                    </button>
                  </>
                )}

                {uploading && <p>⏳ Uploading proposal to Google Drive...</p>}

                {docLink && (
                  <p className="doc-link">
                    ✅ Document uploaded!{" "}
                    <a href={docLink} target="_blank" rel="noopener noreferrer">
                      View it here
                    </a>
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </section>

      {error && (
        <div className="error-message" role="alert">
          <p>{error}</p>
          <button onClick={() => setError(null)} className="error-dismiss" aria-label="Dismiss error">
            ✕
          </button>
        </div>
      )}

      {interrupted ? (
        <div className="feedback-prompt">
          <p>Please provide feedback:</p>
          <form onSubmit={handleSubmit}>
            <input
              className="question-box"
              onChange={handleInputChange}
              value={input}
              placeholder="Please enter your feedback or type 'Approve' to approve proposal..."
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading}>Changes needed</button>
            <TypeaheadPrompts
              input={input}
              suggestions={FEEDBACK_OPTIONS}
              onSelect={(selected) => {
                append({ id: crypto.randomUUID(), content: selected, role: "user" })
                setInput("")
              }}
            />
          </form>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <input
            className="question-box"
            onChange={handleInputChange}
            value={input}
            placeholder="Ask me something..."
          />
          <input type="submit" value="Send" />
          <TypeaheadPrompts
            input={input}
            suggestions={COMMON_PROMPTS}
            onSelect={(selected) => {
              append({ id: crypto.randomUUID(), content: selected, role: "user" })
              setInput("")
            }}
          />
        </form>
      )}

      <button onClick={onBack}>⬅ Back</button>
    </>
  )
}

export default ChatPanel






// "use client"

// import { useEffect, useState } from "react"
// import { useCustomChat } from "../components/Hooks"
// import { Message } from "ai"
// import ReactMarkdown from "react-markdown"
// import LoadingBubble from "../components/LoadingBubble"
// import PromptSuggestionsRow from "../components/PromptSuggestionsRow"
// import TypeaheadPrompts from "../components/TypeAheadSuggestions"
// import { COMMON_PROMPTS } from "../typing_assistants/commonprompts"
// import { FEEDBACK_OPTIONS } from "../typing_assistants/feedbackoptions"
// import { uploadToGoogleDocs } from "../googledoc_upload/googleDrive"

// type User = {
//   email: string
//   name: string
//   picture: string
// }

// type ChatPanelProps = {
//   user: User
//   onBack: () => void
// }

// const ChatPanel = ({ onBack }: ChatPanelProps) => {

//   const {
//     append,
//     isLoading,
//     messages,
//     input,
//     setInput,
//     handleInputChange,
//     handleSubmit,
//     interrupted,
//     error,
//     setError,
//   } = useCustomChat("http://localhost:8000/retrieve")

//   const [uploading, setUploading] = useState(false)
//   const [isWinningChecked, setIsWinningChecked] = useState(false)
//   const [docLink, setDocLink] = useState<string | null>(null)

//   const noMessages = !messages || messages.length === 0
//   const isApproved =
//     messages.length > 0 &&
//     messages[messages.length - 1].content.includes("✅ Proposal approved")

//   // Scroll chat container to bottom on new messages or loading state changes
//   useEffect(() => {
//     if (!noMessages) {
//       const container = document.querySelector("section.populated")
//       if (container) container.scrollTop = container.scrollHeight
//     }
//   }, [messages, isLoading, noMessages])

//   // Helper to append a prompt message
//   const handlePrompt = (promptText: string) => {
//     const msg: Message = {
//       id: crypto.randomUUID(),
//       content: promptText,
//       role: "user",
//     }
//     append(msg)
//   }

//   return (
//     <>
//       <section className={noMessages ? "" : "populated"}>
//         {noMessages ? (
//           <>
//             <p className="starter-text">
//               {
//                 "Welcome to CDGA's Proposal Assistant. I'm here to help you draft professional, standards-aligned proposals tailored to international engineering and consultancy work."
//               }
//             </p>
//             <PromptSuggestionsRow onPromptClick={handlePrompt} />
//           </>
//         ) : (
//           <>
//             {messages.map((message, index) => (
//               <div key={`message-${index}`} className="chat-bubble">
//                 {message.role === "assistant" ? (
//                   <div className="prose">
//                     <ReactMarkdown>{message.content}</ReactMarkdown>
//                   </div>
//                 ) : (
//                   <p>
//                     <strong>You:</strong> {message.content}
//                   </p>
//                 )}
//               </div>
//             ))}

//             {isLoading && (
//               <div className="chat-bubble">
//                 <LoadingBubble />
//               </div>
//             )}

//             {isApproved && (
//               <div className="upload-section">
//                 {!uploading && (
//                   <>
//                     <label style={{ display: "block", marginBottom: "0.5rem" }}>
//                       <input
//                         type="checkbox"
//                         checked={isWinningChecked}
//                         onChange={(e) => setIsWinningChecked(e.target.checked)}
//                         style={{ marginRight: "0.5rem" }}
//                       />
//                       Mark this proposal as a winning proposal
//                     </label>

//                     <button
//                       onClick={async () => {
//                         const lastUserMessage = messages.findLast((msg) => msg.role === "user");
//                         if (!lastUserMessage?.content) return;

//                         setUploading(true);

//                         const rfq_id =
//                           messages.find((msg) => msg.role === "user" && msg.content)?.id || "unknown";

//                         const link = await uploadToGoogleDocs({
//                           proposalText: lastUserMessage.content,
//                           state: { messages },
//                           is_winning: isWinningChecked,
//                           rfq_id,
//                         });

//                         setUploading(false);

//                         if (link) {
//                           setDocLink(link);
//                           window.open(link, "_blank");
//                         }
//                       }}
//                       disabled={uploading}
//                       style={{
//                         display: "inline-flex",
//                         alignItems: "center",
//                         gap: "0.5rem",
//                         padding: "0.5rem 1rem",
//                         fontSize: "1rem",
//                         cursor: uploading ? "not-allowed" : "pointer",
//                         opacity: uploading ? 0.6 : 1,
//                         border: "1px solid #ccc",
//                         borderRadius: "6px",
//                         backgroundColor: "#9b30ff",
//                       }}
//                     >
//                       📄 Upload Approved Proposal to Google Docs
//                     </button>
//                   </>
//                 )}

//                 {uploading && <p>⏳ Uploading proposal to Google Drive...</p>}

//                 {docLink && (
//                   <p className="doc-link">
//                     ✅ Document uploaded!{" "}
//                     <a href={docLink} target="_blank" rel="noopener noreferrer">
//                       View it here
//                     </a>
//                   </p>
//                 )}
//               </div>
//             )}
//           </>
//         )}
//       </section>

//       {error && (
//         <div className="error-message" role="alert">
//           <p>{error}</p>
//           <button
//             onClick={() => setError(null)}
//             className="error-dismiss"
//             aria-label="Dismiss error"
//           >
//             ✕
//           </button>
//         </div>
//       )}

//       {interrupted ? (
//         <div className="feedback-prompt">
//           <p>Please provide feedback:</p>
//           <form onSubmit={handleSubmit}>
//             <input
//               className="question-box"
//               onChange={handleInputChange}
//               value={input}
//               placeholder="Please enter your feedback or type 'Approve' to approve proposal..."
//               disabled={isLoading}
//             />
//             <button type="submit" disabled={isLoading}>
//               Changes needed
//             </button>
//             <TypeaheadPrompts
//               input={input}
//               suggestions={FEEDBACK_OPTIONS}
//               onSelect={(selected) => {
//                 append({ id: crypto.randomUUID(), content: selected, role: "user" })
//                 setInput("")
//               }}
//             />
//           </form>
//         </div>
//       ) : (
//         <form onSubmit={handleSubmit}>
//           <input
//             className="question-box"
//             onChange={handleInputChange}
//             value={input}
//             placeholder="Ask me something..."
//           />
//           <input type="submit" value="Send" />
//           <TypeaheadPrompts
//             input={input}
//             suggestions={COMMON_PROMPTS}
//             onSelect={(selected) => {
//               append({ id: crypto.randomUUID(), content: selected, role: "user" })
//               setInput("")
//             }}
//           />
//         </form>
//       )}

//       <button onClick={onBack}>⬅ Back</button>
//     </>
//   )
// }

// export default ChatPanel
