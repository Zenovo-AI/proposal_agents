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
import { Message } from "ai" // Optional if you're using this type

export function useCustomChat(apiUrl: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  const append = (msg: Message) => {
    // setMessages((prev) => [...prev, msg])
    sendMessage(msg.content)
  }

  const sendMessage = async (content: string) => {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      content,
      role: "user",
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const res = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_query: content }),
      })

      if (!res.ok) throw new Error("Server error")

      const data = await res.json()

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        content: data.response ?? "No response",
        role: "assistant",
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error("Error sending message:", err)
    } finally {
      setIsLoading(false)
      setInput("")
    }
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (input.trim()) {
      sendMessage(input)
    }
  }

  return {
    messages,
    input,
    isLoading,
    handleInputChange,
    handleSubmit,
    append,
  }
}
