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


// "use client"

// import { useState, useEffect } from "react"
// import { Message } from "ai"
// import Bubble from "./components/Bubble"
// import LoadingBubble from "./components/LoadingBubble"
// import PromptSuggestionsRow from "./components/PromptSuggestionsRow"
// import Image from "next/image"
// import Artboard_3 from "./assets/Artboard_3.png"
// import { useCustomChat } from "./components/Hooks"
// import ReactMarkdown from "react-markdown"
// import TypeaheadPrompts from "./components/TypeAheadSuggestions"
// import { COMMON_PROMPTS } from "./components/commonprompts"

// // Enhanced feedback options
// const FEEDBACK_OPTIONS = [
//   "Too vague",
//   "Too generic",
//   "Not aligned with scope",
//   "Needs more technical detail",
//   "Not suitable for client",
// ]

// const Home = () => {
//   const [mode, setMode] = useState<"upload" | "chat" | null>(null)
//   const [file, setFile] = useState<File | null>(null)
//   const [uploadStatus, setUploadStatus] = useState("")
//   const [showCustomFeedbackInput, setShowCustomFeedbackInput] = useState(false)
//   const [isFocused, setIsFocused] = useState(false)

//   const {
//     append,
//     isLoading,
//     messages,
//     input,
//     // Removed setInput as it does not exist in useCustomChat
//     handleInputChange,
//     handleSubmit,
//     interrupted,
//     feedbackOptions,
//     error,
//     setError,
//   } = useCustomChat("http://127.0.0.1:8000/retrieve")

//   // Removed redundant declaration of input and setInput

//   const noMessages = !messages || messages.length === 0

//   const handlePrompt = (promptText: string) => {
//     const msg: Message = {
//       id: crypto.randomUUID(),
//       content: promptText,
//       role: "user",
//     }
//     append(msg)
//   }

//   const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     const selected = e.target.files?.[0]
//     if (selected) {
//       setFile(selected)
//     }
//   }

//   const handleFileUpload = async () => {
//     if (!file) return

//     const formData = new FormData()
//     formData.append("file", file)

//     try {
//       const res = await fetch("http://127.0.0.1:8000/ingress-file", {
//         method: "POST",
//         body: formData,
//       })

//       if (res.ok) {
//         setUploadStatus("✅ File uploaded successfully!")
//       } else {
//         setUploadStatus("❌ Upload failed. Try again.")
//       }
//     } catch (error) {
//       console.error("Upload error:", error)
//       setUploadStatus("❌ Upload failed. Check the console.")
//     }
//   }

//   const scrollToBottom = () => {
//     const container = document.querySelector("section.populated")
//     if (container) {
//       container.scrollTop = container.scrollHeight
//     }
//   }

//   useEffect(() => {
//     if (!noMessages) scrollToBottom()
//   }, [messages])

//   const handleFeedbackClick = (feedback: string) => {
//     const msg: Message = {
//       id: crypto.randomUUID(),
//       content: feedback,
//       role: "user",
//     }
//     append(msg)
//     setShowCustomFeedbackInput(false)
//   }

//   return (
//     <main>
//       <Image src={Artboard_3} width="250" alt="CDGA Logo" />

//       {!mode && (
//         <div className="mode-selector">
//           <p>
//             Welcome to CDGA’s Proposal Agent.
//             I’m your virtual assistant, here to help you craft top-tier proposals rooted in CDGA’s 25+ years of international engineering and consultancy 
//             experience. Whether you're preparing documentation for CTBTO or drafting a bid for a global energy client, I’ve got you covered.
//             Would you like to upload a document or start drafting a proposal?
//           </p>
//           <button onClick={() => setMode("upload")}>📄 Upload Document</button>
//           <button onClick={() => setMode("chat")}>💬 Draft Proposal</button>
//         </div>
//       )}

//       {mode === "upload" && (
//         <div className="upload-section">
//           <p>Select a file to upload:</p>
//           <input type="file" onChange={handleFileChange} />
//           <button onClick={handleFileUpload} disabled={!file}>Upload</button>
//           <p>{uploadStatus}</p>
//           <button onClick={() => setMode(null)}>⬅ Back</button>
//         </div>
//       )}

//       {mode === "chat" && (
//         <>
//           <section className={noMessages ? "" : "populated"}>
//             {noMessages ? (
//               <>
//                 <p className="starter-text">
//                   Welcome to CDGA’s Proposal Assistant.  
//                   I’m here to help you draft professional, standards-aligned proposals tailored to international engineering and consultancy work.  
//                   Whether you're starting from scratch or need support developing sections for organizations like CTBTO or global energy partners,  
//                   simply tell me what you need, and I’ll generate a clear and compelling proposal for your project.
//                 </p>
//                 <PromptSuggestionsRow onPromptClick={handlePrompt} />
//               </>
//             ) : (
//               <>
//                 {messages.map((message, index) => (
//                   <div key={`message-${index}`} className="chat-bubble">
//                     {message.role === "assistant" ? (
//                       <div className="prose">
//                         <ReactMarkdown>{message.content}</ReactMarkdown>
//                       </div>
//                     ) : (
//                       <p><strong>You:</strong> {message.content}</p>
//                     )}
//                   </div>
//                 ))}
//                 {isLoading && <LoadingBubble />}
//               </>
//             )}
//           </section>

//           {error && (
//             <div className="error-message" role="alert">
//               <p>{error}</p>
//               <button onClick={() => setError(null)} className="error-dismiss" aria-label="Dismiss error">
//                 ✕
//               </button>
//             </div>
//           )}

//           {interrupted && (
//             <div className="feedback-prompt">
//               <p>This draft might need improvements. How would you rate it?</p>
//               <div className="feedback-options">
//                 {FEEDBACK_OPTIONS.map((option, idx) => (
//                   <button
//                     key={idx}
//                     className="feedback-button"
//                     onClick={() => handleFeedbackClick(option)}
//                     disabled={isLoading}
//                   >
//                     {option}
//                   </button>
//                 ))}
//               </div>

//               <button
//                 className="custom-feedback-toggle"
//                 onClick={() => setShowCustomFeedbackInput((prev) => !prev)}
//               >
//                 {showCustomFeedbackInput ? "Hide custom feedback" : "💬 Enter Custom Feedback"}
//               </button>

//               {showCustomFeedbackInput && (
//                 <form onSubmit={handleSubmit}>
//                   <input
//                     className="question-box"
//                     onChange={handleInputChange}
//                     value={input}
//                     placeholder="Enter your feedback..."
//                     disabled={isLoading}
//                   />
//                   <button type="submit" disabled={isLoading}>Send Feedback</button>
//                 </form>
//               )}
//             </div>
//           )}

//           <div className="form-container">
//             <form onSubmit={handleSubmit}>
//               <div className="input-wrapper relative">
//                 <input
//                   className="question-box"
//                   onChange={handleInputChange}
//                   value={input}
//                   placeholder={interrupted ? "Provide your feedback..." : "Ask me something..."}
//                 />
//                 <TypeaheadPrompts
//                   input={input}
//                   suggestions={COMMON_PROMPTS}
//                   onSelect={(suggestion) => {
//                     // Update the input field with the selected suggestion
//                     handleInputChange({ target: { value: suggestion } } as React.ChangeEvent<HTMLInputElement>);

//                     // Immediately submit the form after updating the input
//                     handleSubmit(new Event('submit') as any);
//                   }}
//                 />
                
//               </div>
//               <button 
//                 type="submit"
//                 disabled={isLoading || !input.trim()}
//               >
//                 {interrupted ? "Send Feedback" : "Send"}
//               </button>
//             </form>
//           </div>


//           <button onClick={() => setMode(null)}>⬅ Back</button>
//         </>
//       )}
//     </main>
//   )
// }

// export default Home



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



const Home = () => {
  const [mode, setMode] = useState<"upload" | "chat" | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState("")

  const {
    append,
    isLoading,
    messages,
    input,
    setInput,
    handleInputChange,
    handleSubmit,
    interrupted,
    feedbackOptions,
    error,
    setError
  } = useCustomChat("http://127.0.0.1:8000/retrieve")

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

    try {
      const res = await fetch("http://127.0.0.1:8000/ingress-file", {
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
  }, [messages])

  

  return (
    <main>
      <Image src={Artboard_3} width="250" alt="CDGA Logo" />

      {!mode && (
        <div className="mode-selector">
          <p>
            Welcome to CDGA’s Proposal Agent.
            I’m your virtual assistant, here to help you craft top-tier proposals rooted in CDGA’s 25+ years of international engineering and consultancy 
            experience. Whether you're preparing documentation for CTBTO or drafting a bid for a global energy client, I’ve got you covered.
            Would you like to upload a document or start drafting a proposal?
          </p>
          <button onClick={() => setMode("upload")}>📄 Upload Document</button>
          <button onClick={() => setMode("chat")}>💬 Draft Proposal</button>
        </div>
      )}

      {mode === "upload" && (
        <div className="upload-section">
          <p>Select a file to upload:</p>
          <input type="file" onChange={handleFileChange} />
          <button onClick={handleFileUpload} disabled={!file}>Upload</button>
          <p>{uploadStatus}</p>
          <button onClick={() => setMode(null)}>⬅ Back</button>
        </div>
      )}

      {mode === "chat" && (
        <>
          <section className={noMessages ? "" : "populated"}>
            {noMessages ? (
              <>
                <p className="starter-text">
                  Welcome to CDGA’s Proposal Assistant.  
                  I’m here to help you draft professional, standards-aligned proposals tailored to international engineering and consultancy work.  
                  Whether you're starting from scratch or need support developing sections for organizations like CTBTO or global energy partners,  
                  simply tell me what you need, and I’ll generate a clear and compelling proposal for your project.

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