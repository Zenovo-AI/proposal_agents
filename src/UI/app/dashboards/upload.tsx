// components/panels/upload.tsx
"use client"

import { useState } from "react"

type UploadPanelProps = {
  onBack: () => void
}

const UploadPanel = ({ onBack }: UploadPanelProps) => {
  const [file, setFile] = useState<File | null>(null)
  const [webLink, setWebLink] = useState<string | null>(null)
  const [uploadStatus, setUploadStatus] = useState("")

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) setFile(selected)
  }

  const handleFileUpload = async () => {
    if (!file && !webLink) return

    const formData = new FormData()
    if (file) formData.append("file", file)
    if (webLink) formData.append("web_link", webLink)

    setUploadStatus("⏳ Uploading file/web link...")

    try {
      const res = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/ingress-file", {
        method: "POST",
        body: formData,
        credentials: "include",
      })

      if (res.ok) {
        setUploadStatus("✅ Upload successful!")
      } else {
        setUploadStatus("❌ Upload failed. Try again.")
      }
    } catch (error) {
      console.error("Upload error:", error)
      setUploadStatus("❌ Upload failed. Check the console.")
    }
  }

  return (
    <div className="center-wrapper">
      <div className="upload-section">
        <p>Select a file to upload or enter a web link:</p>
        <input type="file" onChange={handleFileChange} />
        <input
          type="url"
          placeholder="Enter a web link"
          onChange={(e) => setWebLink(e.target.value)}
          className="web-link-input"
        />
        <button onClick={handleFileUpload} disabled={!file && !webLink}>
          Upload
        </button>
        <p>{uploadStatus}</p>
        <button onClick={onBack}>⬅ Back</button>
      </div>
    </div>
  )
}

export default UploadPanel
