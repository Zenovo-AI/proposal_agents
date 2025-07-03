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


import { useState } from "react";
import { Message } from "ai";

interface State {
  user_query: string;
  candidate: Message;
  examples: string;
  messages: string[];
  runtime_limit: number;
  human_feedback: string[];
  iteration: number;
  structure: Message;
}

interface ProposalResponse {
  interrupt?: boolean;
  proposal?: string;
  message?: string;
  feedback_options?: string[];
  response?: string;
  status?: string;
  error?: string;
  state?: State;
  type?: string;
}

export function useCustomChat(
  apiUrl: string,
  selectedRfq: string,
  mode: string
) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [interrupted, setInterrupted] = useState<boolean>(false);
  const [feedbackOptions, setFeedbackOptions] = useState<string[]>([]);
  const [currentState, setCurrentState] = useState<State | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isApproved, setIsApproved] = useState<boolean>(false);

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    setError(null);
  };

  // Append a message (used for prompt suggestions)
  const append = (msg: Message) => {
    if (interrupted) {
      handleFeedback(msg.content);
    } else {
      handleMessage(msg.content);
    }
  };

  // Send a user message to the backend
  const handleMessage = async (content: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const userMessage: Message = {
        id: crypto.randomUUID(),
        content,
        role: "user",
      };
      setMessages((prev) => [...prev, userMessage]);
      setInput("");

      const stored = localStorage.getItem("user");
      const user = stored ? JSON.parse(stored) : null;
      const userId = user?.email;

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          user_query: content,
          rfq_id: selectedRfq,
          mode,
          user_id: userId,
        }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data: ProposalResponse = await response.json();

      if (data.interrupt) {
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          content: data.proposal ?? data.message ?? "",
          role: "assistant",
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setInterrupted(true);
        setCurrentState(data.state || null);
        setFeedbackOptions(data.feedback_options || []);
        return;
      }

      setInterrupted(false);
      setFeedbackOptions([]);
      setCurrentState(null);

      if (data.response) {
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          content: data.response,
          role: "assistant",
        };
        setMessages((prev) => [...prev, assistantMessage]);
        return;
      }

      throw new Error("Missing response field in server data");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          content: `⚠️ ${errorMessage}. Please try again.`,
          role: "assistant",
        },
      ]);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Send feedback to the backend, always with the latest state
  const handleFeedback = async (feedback: string) => {
    if (!currentState) {
      setError("Cannot send feedback: missing conversation state.");
      return;
    }
    try {
      setIsLoading(true);
      setError(null);

      const feedbackMessage: Message = {
        id: crypto.randomUUID(),
        content: feedback,
        role: "user",
      };
      setMessages((prev) => [...prev, feedbackMessage]);
      setInput("");

      // Optionally, update human_feedback in state before sending
      const newState = {
        ...currentState,
        human_feedback: [
          ...(currentState.human_feedback || []),
          feedback,
        ],
        interrupt_type: "human_interrupt",
      };

      const response = await fetch(apiUrl.replace("/retrieve", "/resume"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: newState, feedback }),
        credentials: "include",
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data: ProposalResponse = await response.json();
      if (data.error) throw new Error(data.error);

      if (data.interrupt && data.proposal) {
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          content: data.proposal,
          role: "assistant",
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setFeedbackOptions(data.feedback_options || []);
        setCurrentState(data.state || null);
        return;
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
        setCurrentState(data.state || null);
        setIsApproved(true);
        return;
      }

      if (data.response) {
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          content: data.response,
          role: "assistant",
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to send feedback";
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          content: `⚠️ ${errorMessage}. Please try again.`,
          role: "assistant",
        },
      ]);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Unified submit handler
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim()) return;
    if (interrupted) {
      handleFeedback(input);
    } else {
      handleMessage(input);
    }
    setInput("");
  };

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
    isApproved,
    currentState,
  };
}


