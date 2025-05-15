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



// import { useState } from "react"
// import { Message } from "ai"

// export function useCustomChat(apiUrl: string) {
//   const [messages, setMessages] = useState<Message[]>([])
//   const [input, setInput] = useState("")
//   const [isLoading, setIsLoading] = useState(false)
//   const [interrupted, setInterrupted] = useState(false)
//   const [savedState, setSavedState] = useState<any>(null)

//   const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     setInput(e.target.value)
//   }

//   const append = (msg: Message) => {
//     sendMessage(msg.content)
//   }

//   const sendMessage = async (content: string) => {
//     const userMessage: Message = {
//       id: crypto.randomUUID(),
//       content,
//       role: "user",
//     }

//     setMessages((prev) => [...prev, userMessage])
//     setIsLoading(true)

//     try {
//       const res = await fetch(apiUrl, {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ user_query: content }),
//       })

//       const data = await res.json()

//       if (data.interrupt) {
//         setInterrupted(true)
//         setSavedState({ state: data.state, next: data.next })
//         const interruptMsg: Message = {
//           id: crypto.randomUUID(),
//           content: data.message || "⚠️ Please provide feedback.",
//           role: "assistant",
//         }
//         setMessages((prev) => [...prev, interruptMsg])
//       } else {
//         const assistantMessage: Message = {
//           id: crypto.randomUUID(),
//           content: data.response ?? "No response",
//           role: "assistant",
//         }
//         setMessages((prev) => [...prev, assistantMessage])
//       }
//     } catch (err) {
//       console.error("Error sending message:", err)
//     } finally {
//       setIsLoading(false)
//       setInput("")
//     }
//   }

//   const sendFeedback = async (feedback: string) => {
//     if (!savedState) return

//     setIsLoading(true)

//     try {
//       const res = await fetch(`${apiUrl.replace("/retrieve", "/resume")}`, {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ feedback, ...savedState }),
//       })

//       const data = await res.json()

//       const resumedMessage: Message = {
//         id: crypto.randomUUID(),
//         content: data.response ?? "No response after resuming",
//         role: "assistant",
//       }

//       setMessages((prev) => [...prev, resumedMessage])
//     } catch (err) {
//       console.error("Error resuming graph:", err)
//     } finally {
//       setIsLoading(false)
//       setInput("")
//       setInterrupted(false)
//       setSavedState(null)
//     }
//   }

//   const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
//     e.preventDefault()
//     if (!input.trim()) return

//     if (interrupted) {
//       sendFeedback(input)
//     } else {
//       sendMessage(input)
//     }
//   }

//   return {
//     messages,
//     input,
//     isLoading,
//     handleInputChange,
//     handleSubmit,
//     append,
//     interrupted,
//   }
// }


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
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [interrupted, setInterrupted] = useState(false)
  const [feedbackOptions, setFeedbackOptions] = useState<string[]>([])
  const [currentState, setCurrentState] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
    setError(null) // Clear any previous errors
  }

  const append = (msg: Message) => {
    sendMessage(msg.content)
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
      setMessages(prev => [...prev, userMessage])

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_query: content }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      // Safe data parsing
      let data: ProposalResponse | null = null
      try {
        const text = await response.text()
        console.log('Raw response:', text) // Debug log
        data = text ? JSON.parse(text) : null
      } catch (e) {
        console.error('Parse error:', e)
        throw new Error('Failed to parse server response')
      }

      // Null check before accessing properties
      if (!data) {
        throw new Error('Empty response from server')
      }

      // Handle proposal/interrupt case
      if (data.interrupt === true) {  // Explicit comparison
        const content = data.proposal || data.message
        if (!content) {
          throw new Error('Missing content in server response')
        }

        const proposalMessage: Message = {
          id: crypto.randomUUID(),
          content,
          role: "assistant"
        }
        setMessages(prev => [...prev, proposalMessage])
        setInterrupted(true)
        setFeedbackOptions(data.feedback_options || [])
        setCurrentState(data.state)
        return
      }

      // Handle normal response
      if (!data.response) {
        throw new Error('Missing response field in server data')
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        content: data.response,
        role: "assistant"
      }
      setMessages(prev => [...prev, assistantMessage])

    } catch (err) {
      console.error("Error:", err) // Debug log
      const errorMessage = err instanceof Error ? err.message : "Unknown error"
      const errorBubble: Message = {
        id: crypto.randomUUID(),
        content: `⚠️ ${errorMessage}. Please try again.`,
        role: "assistant"
      }
      setMessages(prev => [...prev, errorBubble])
      setError(errorMessage)
    } finally {
      setIsLoading(false)
      setInput("")
    }
  }
  
  const sendFeedback = async (feedback: string) => {
    try {
        setIsLoading(true)
        setError(null)

        // Add feedback message to chat
        const feedbackMessage: Message = {
            id: crypto.randomUUID(),
            content: feedback,
            role: "user"
        }
        setMessages(prev => [...prev, feedbackMessage])

        const response = await fetch(`${apiUrl.replace("/retrieve", "/resume")}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                state: currentState,
                feedback: feedback
            }),
        })

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`)
        }

        const data: ProposalResponse = await response.json()

        if (data.error) {
            throw new Error(data.error)
        }

        // Handle proposal content from interrupt
        if (data.interrupt && data.proposal) {
            const proposalMessage: Message = {
                id: crypto.randomUUID(),
                content: data.proposal,
                role: "assistant"
            }
            setMessages(prev => [...prev, proposalMessage])
            setFeedbackOptions(data.feedback_options || [])
            setCurrentState(data.state)
            return
        }

        // Handle approval response
        if (data.status === "approved") {
            const approvalMessage: Message = {
                id: crypto.randomUUID(),
                content: "✅ Proposal approved. Process complete.",
                role: "assistant"
            }
            setMessages(prev => [...prev, approvalMessage])
            setInterrupted(false)
            setCurrentState(null)
            setFeedbackOptions([])
            return
        }

        // Handle normal response
        if (data.response) {
            const responseMessage: Message = {
                id: crypto.randomUUID(),
                content: data.response,
                role: "assistant"
            }
            setMessages(prev => [...prev, responseMessage])
        }

    } catch (err) {
        console.error("Error:", err)
        const errorMessage = err instanceof Error ? err.message : "Failed to send feedback"
        setError(errorMessage)
        
        const errorBubble: Message = {
            id: crypto.randomUUID(),
            content: `⚠️ ${errorMessage}. Please try again.`,
            role: "assistant"
        }
        setMessages(prev => [...prev, errorBubble])
    } finally {
        setIsLoading(false)
        setInput("")
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
  }

  return {
    messages,
    input,
    isLoading,
    error,
    setError,
    handleInputChange,
    handleSubmit,
    append,
    interrupted,
    feedbackOptions
  }
}


