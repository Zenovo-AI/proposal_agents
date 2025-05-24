/**
 * Home Component
 * --------------
 * This is the main component for the Proposal Assistant web app.
 * It allows users to either upload documents or interact with a chatbot 
 * to help generate technical proposals for international engineering and consultancy projects.
 *
 * Key Imports:
 * - useState: For managing local state (mode, file, status, etc.).
 * - useChat: A custom hook from the AI SDK that handles chat interactions.
 * - UI components: Bubble (chat bubbles), LoadingBubble (typing indicator), PromptSuggestionsRow (suggested questions).
 * - Artboard_3 image: Displayed at the top of the interface.
 *
 * State Variables:
 * - mode: Tracks whether the user is in "upload" or "chat" mode.
 * - file: Stores the uploaded file.
 * - uploadStatus: Displays the result of the file upload process.
 * - useChat(): Manages chat input, message history, and loading state.
 *
 * Handlers:
 * - handlePrompt(): When a user clicks a suggested prompt, it sends the prompt as a user message.
 * - handleFileChange(): Captures the file selected by the user.
 * - handleFileUpload(): Uploads the file to the `/ingress-file` endpoint and updates the status.
 *
 * UI Flow:
 * 1. If no mode is selected, the user is shown two buttons to choose between uploading or chatting.
 * 2. If "upload" mode is selected, the user can select a file and upload it.
 * 3. If "chat" mode is selected, the chat interface is shown.
 *    - If no messages yet: shows welcome text and prompt suggestions.
 *    - If messages exist: displays chat history using the Bubble component.
 *    - While loading: shows a loading bubble.
 *    - Also includes a text box and submit button to send user questions.
 * 
 * Navigation:
 * - In both upload and chat mode, users can return to the home screen with a "⬅ Back" button.
 *
 * export default Home:
 * - Makes this component available for use in the application as the main homepage.
 */



"use client"

import { useState, useEffect } from "react"
import { Message } from "ai"
import LoadingBubble from "./components/LoadingBubble"
import PromptSuggestionsRow from "./components/PromptSuggestionsRow"
import Image from "next/image"
import Artboard_3 from "./assets/Artboard_3.png"
import { useCustomChat } from "./components/Hooks"
import ReactMarkdown from "react-markdown"
import TypeaheadPrompts from "./components/TypeAheadSuggestions"
import { COMMON_PROMPTS } from "./typing_assistants/commonprompts"
import { FEEDBACK_OPTIONS } from "./typing_assistants/feedbackoptions"
import { uploadToGoogleDocs } from "./googledoc_upload/googleDrive"
import LoginPage from "./authentication/loginPage"
import { useAuth } from "./authentication/useAuth"


const Home = () => {
  const [mode, setMode] = useState<"upload" | "chat" | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState("")
  const [uploading, setUploading] = useState(false)
  const [docLink, setDocLink] = useState<string | null>(null)
  const [notice] = useState<string | null>(null);
  const { user: authenticatedUser, loading } = useAuth();
  
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
    setError
  } = useCustomChat("https://proposal-generator-app-b2pah.ondigitalocean.app/retrieve")

  const noMessages = !messages || messages.length === 0

  const handlePrompt = (promptText: string) => {
    const msg: Message = {
      id: crypto.randomUUID(),
      content: promptText,
      role: "user",
    }
    append(msg)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
    }
  }

  const handleFileUpload = async () => {
    if (!file) return

    const formData = new FormData()
    formData.append("file", file)

    setUploadStatus("⏳ Uploading file...");

    try {
      const res = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/ingress-file", {
        method: "POST",
        body: formData,
      })

      if (res.ok) {
        setUploadStatus("✅ File uploaded successfully!")
      } else {
        setUploadStatus("❌ Upload failed. Try again.")
      }
    } catch (error) {
      console.error("Upload error:", error)
      setUploadStatus("❌ Upload failed. Check the console.")
    }
  }

  const scrollToBottom = () => {
    const container = document.querySelector("section.populated")
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }
  
  useEffect(() => {
    if (!noMessages) scrollToBottom()
  }, [messages, noMessages])

  const isApproved = messages.length > 0 && messages[messages.length - 1].content.includes("✅ Proposal approved")  

  if (loading) {
    return <p>Loading...</p>;
  }

  if (!authenticatedUser) {
    return <LoginPage notice={notice} />
  }

  return (
    <main>
      {authenticatedUser && (
        <header className="app-header">
          <Image src={Artboard_3} width="250" alt="CDGA Logo" />
          <div className="user-info">
          <Image
            src={authenticatedUser.picture}
            alt="User profile"
            width={40}
            height={40}
            style={{ borderRadius: '50%', marginRight: '10px' }}
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
                  await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/logout", { method: "GET", credentials: "include" });
                } catch (error) {
                  console.error("Logout failed", error);
                }
                localStorage.removeItem("user");
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                window.location.href = "/";  // redirect to your app's root to show login page
              }}
              className="btn btn-danger"
            >
              Logout
            </a>

          </div>
        </header>
      )}


      {!mode && (
        <div className="mode-selector">
          <p>
          {"Welcome to CDGA's Proposal Agent. I'm your virtual assistant, here to help you craft top-tier proposals rooted in CDGA's 25+ years of international engineering and consultancy experience. Whether you're preparing documentation for CTBTO or drafting a bid for a global energy client, I've got you covered. Would you like to upload a document or start drafting a proposal?"}
          </p>
          <div className="buttons">
            <button onClick={() => setMode("upload")}>📄 Upload Document</button>
            <button onClick={() => setMode("chat")}>💬 Draft Proposal</button>
          </div>
        </div>
      )}


      {mode === "upload" && (
        <div className="center-wrapper">
          <div className="upload-section">
            <p>Select a file to upload:</p>
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleFileUpload} disabled={!file}>Upload</button>
            <p>{uploadStatus}</p>
            <button onClick={() => setMode(null)}>⬅ Back</button>
          </div>
        </div>
      )}


      {mode === "chat" && (
        <>
          <section className={noMessages ? "" : "populated"}>
            {noMessages ? (
              <>
                <p className="starter-text">
                  {"Welcome to CDGA's Proposal Assistant. I'm here to help you draft professional, standards-aligned proposals tailored to international engineering and consultancy work. Whether you're starting from scratch or need support developing sections for organizations like CTBTO or global energy partners, simply tell me what you need, and I'll generate a clear and compelling proposal for your project."}
                </p>
                <PromptSuggestionsRow onPromptClick={handlePrompt} />
              </>
            ) : (
              <>
                {messages.map((message, index) => (
                  <div key={`message-${index}`} className="chat-bubble">
                    {message.role === "assistant" ? (
                      <div className="prose">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    ) : (
                    <p><strong>You:</strong> {message.content}</p>
                    )}
                  </div>
                ))}

                {isLoading && <LoadingBubble />}

                {isApproved && !uploading && (
                  <button
                    onClick={async () => {
                      const lastUserMessage = messages.findLast(msg => msg.role === "user");
                      if (!lastUserMessage?.content) return;

                      setUploading(true);

                      const link = await uploadToGoogleDocs(lastUserMessage.content, {
                        user: authenticatedUser,
                        messages: messages, // ✅ add messages here
                      });

                      setUploading(false);

                      if (link) {
                        setDocLink(link);
                        window.open(link, "_blank");
                      }
                    }}
                    disabled={uploading}
                  >
                    📄 Upload Approved Proposal to Google Docs
                  </button>
                )}

                {uploading && <p>⏳ Uploading proposal to Google Drive...</p>}
                {docLink && (
                  <p className="doc-link">
                    ✅ Document uploaded! <a href={docLink} target="_blank" rel="noopener noreferrer">View it here</a>
                  </p>
                )}

              </>
            )}
          </section>

          {/* Add error handling here, before feedback options */}
          {error && (
            <div className="error-message" role="alert">
              <p>{error}</p>
              <button 
                onClick={() => setError(null)} 
                className="error-dismiss"
                aria-label="Dismiss error"
              >
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
                  placeholder="Type your feedback or select a suggestion..."
                  disabled={isLoading}
                />
                <button type="submit" disabled={isLoading}>
                  Send Feedback
                </button>

                <TypeaheadPrompts
                  input={input}
                  suggestions={FEEDBACK_OPTIONS}
                  onSelect={(selected) => {
                    const msg: Message = {
                      id: crypto.randomUUID(),
                      content: selected,
                      role: "user",
                    }
                    append(msg)
                    setInput("") // Important!
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
                  const msg: Message = {
                    id: crypto.randomUUID(),
                    content: selected,
                    role: "user",
                  }
                  append(msg)
                  setInput("")
                }}
              />
            </form>
          )}

          <button onClick={() => setMode(null)}>⬅ Back</button>
        </>
      )}
    </main>
  )
}

export default Home
