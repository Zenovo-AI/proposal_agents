"use client"

import Image from "next/image"
import { useEffect, useState } from "react"
import Artboard_3 from "../assets/Artboard_3.png"
import { STATUS_MESSAGES } from "../status/statusMessages"

interface LoginPageProps {
  notice?: string | null
}

export default function LoginPage({ notice }: LoginPageProps) {
  const [statusIndex, setStatusIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setStatusIndex((i) => (i + 1) % STATUS_MESSAGES.length)
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <main className="centered-container">
      {notice && (
        <div className="auth-notice">
          <p>{notice}</p>
        </div>
      )}
      <Image src={Artboard_3} width={200} alt="CDGA Logo" />
      <h1>Welcome to CDGA Proposal Agent</h1>
      <p className="status-message">{STATUS_MESSAGES[statusIndex]}</p>
      <a
        href="https://api.zenovo.ai/api/login"
        className="btn btn-primary"
        aria-label="Login with Google"
      >
        Sign in with Google
      </a>
    </main>
  )
}
