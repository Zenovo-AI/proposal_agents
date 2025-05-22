/**
 * useCustomChat Hook
 * ------------------
 * This custom React hook manages the logic for a simple chatbot interface.
 * 
 * Main Features:
 * - Stores and updates the conversation messages (user and assistant).
 * - Tracks the user’s input and whether the assistant is "typing" (loading).
 * - Sends user messages to an external API and handles the assistant's response.
 * - Provides handler functions to use inside a chat UI component.
 * 
 * How it Works:
 * - `input`: The current text typed by the user.
 * - `messages`: An array of messages (both user and assistant).
 * - `handleInputChange`: Updates the input as the user types.
 * - `handleSubmit`: Sends the user's message when they press "Enter" or click submit.
 * - `append`: Sends a message programmatically (e.g., when clicking a prompt suggestion).
 * - `sendMessage`: Sends the user message to the backend API, waits for a response, and adds both to the message list.
 * 
 * This hook helps simplify building a chatbot UI by centralizing all the logic in one place.
 */



import { useState } from "react"
import { Message } from "ai"

interface ProposalResponse {
  interrupt?: boolean
  proposal?: string
  message?: string
  feedback_options?: string[]
  response?: string
  status?: string
  error?: string
  state?: any
}

export function useCustomChat(apiUrl: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState<string>("")
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [interrupted, setInterrupted] = useState<boolean>(false)
  const [feedbackOptions, setFeedbackOptions] = useState<string[]>([])
  const [currentState, setCurrentState] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [isApproved, setIsApproved] = useState<boolean>(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
    setError(null)
  }

  const append = (msg: Message) => {
    if (interrupted) {
      sendFeedback(msg.content)
    } else {
      sendMessage(msg.content)
    }
  }

  const sendMessage = async (content: string) => {
    try {
      setIsLoading(true)
      setError(null)

      const userMessage: Message = {
        id: crypto.randomUUID(),
        content,
        role: "user",
      }

      setMessages((prev) => [...prev, userMessage])
      setInput("")

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_query: content }),
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)

      const text = await response.text()
      let data: ProposalResponse | null = null

      try {
        data = text ? JSON.parse(text) : null
      } catch {
        throw new Error("Failed to parse server response")
      }

      if (!data) throw new Error("Empty response from server")

      if (data.interrupt === true) {
        const interruptContent: string =
          data.proposal ?? data.message ?? "Proposal suggestion received."

        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          content: interruptContent,
          role: "assistant",
        }

        setMessages((prev) => [...prev, assistantMessage])
        setInterrupted(true)
        setFeedbackOptions(data.feedback_options || [])
        setCurrentState(data.state)
        return
      }

      if (!data.response) throw new Error("Missing response field in server data")

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        content: data.response,
        role: "assistant",
      }

      setMessages((prev) => [...prev, assistantMessage])
      setInterrupted(false)
      setFeedbackOptions([])
      setCurrentState(null)
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred"
      const errorMessageBubble: Message = {
        id: crypto.randomUUID(),
        content: `⚠️ ${errorMessage}. Please try again.`,
        role: "assistant",
      }
      setMessages((prev) => [...prev, errorMessageBubble])
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const saveProposalToDrive = async (state: any): Promise<string | null> => {
    const refresh_token = localStorage.getItem("refresh_token")
    if (!refresh_token) {
      setError("Google refresh token missing. Please log in or configure it first.")
      return null
    }
  
    try {
      const response = await fetch(apiUrl.replace("/retrieve", "/save-to-drive"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state, refresh_token }),
      })
  
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to save proposal: ${response.status}`)
      }
  
      const data = await response.json()
      return data.view_link || null
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error during save"
      setError(errorMessage)
      return null
    }
  }

  const sendFeedback = async (feedback: string) => {
    try {
      setIsLoading(true)
      setError(null)

      const feedbackMessage: Message = {
        id: crypto.randomUUID(),
        content: feedback,
        role: "user",
      }

      setMessages((prev) => [...prev, feedbackMessage])
      setInput("")

      const response = await fetch(apiUrl.replace("/retrieve", "/resume"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: currentState, feedback }),
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)

      const data: ProposalResponse = await response.json()
      if (data.error) throw new Error(data.error)

      if (data.interrupt && data.proposal) {
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          content: data.proposal,
          role: "assistant",
        }

        setMessages((prev) => [...prev, assistantMessage])
        setFeedbackOptions(data.feedback_options || [])
        setCurrentState(data.state)
        return
      }

      if (data.status === "approved") {
        const approvedMessage: Message = {
          id: crypto.randomUUID(),
          content: "✅ Proposal approved. You can now upload it to Google Docs.",
          role: "assistant",
        };
      
        setMessages((prev) => [...prev, approvedMessage]);
        setInterrupted(false);
        setFeedbackOptions([]);
        setCurrentState(data.state);   // save the state for uploading later
        setIsApproved(true);           // flag to show upload button
        return;
      }
      


      if (data.response) {
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          content: data.response,
          role: "assistant",
        }

        setMessages((prev) => [...prev, assistantMessage])
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to send feedback"
      const errorMessageBubble: Message = {
        id: crypto.randomUUID(),
        content: `⚠️ ${errorMessage}. Please try again.`,
        role: "assistant",
      }
      setMessages((prev) => [...prev, errorMessageBubble])
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim()) return
    if (interrupted) {
      sendFeedback(input)
    } else {
      sendMessage(input)
    }
    setInput("")
  }

  return {
    messages,
    input,
    setInput,
    isLoading,
    error,
    setError,
    handleInputChange,
    handleSubmit,
    append,
    interrupted,
    feedbackOptions,
  }
}

