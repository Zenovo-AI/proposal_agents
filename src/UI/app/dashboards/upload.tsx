// "use client"

// import { useState } from "react"

// type UploadPanelProps = {
//   onBack: () => void
// }

// const UploadPanel = ({ onBack }: UploadPanelProps) => {
//   const [file, setFile] = useState<File | null>(null)
//   const [webLink, setWebLink] = useState<string | null>(null)
//   const [uploadStatus, setUploadStatus] = useState("")

//   const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     const selected = e.target.files?.[0]
//     if (selected) setFile(selected)
//   }

//   const handleFileUpload = async () => {
//     if (!file && !webLink) return

//     const formData = new FormData()
//     if (file) formData.append("file", file)
//     if (webLink) formData.append("web_link", webLink)

//     setUploadStatus("⏳ Uploading file/web link...")

//     try {
//       const res = await fetch("http://localhost:8000/ingress-file", {
//         method: "POST",
//         body: formData,
//         credentials: "include",
//       })

//       if (res.ok) {
//         setUploadStatus("✅ Upload successful!")
//       } else {
//         setUploadStatus("❌ Upload failed. Try again.")
//       }
//     } catch (error) {
//       console.error("Upload error:", error)
//       setUploadStatus("❌ Upload failed. Check the console.")
//     }
//   }

//   return (
//     <div className="center-wrapper">
//       <div className="upload-section">
//         <p>Select a file to upload or enter a web link:</p>
//         <input type="file" onChange={handleFileChange} />
//         <input
//           type="url"
//           placeholder="Enter a web link"
//           onChange={(e) => setWebLink(e.target.value)}
//           className="web-link-input"
//         />
//         <button onClick={handleFileUpload} disabled={!file && !webLink}>
//           Upload
//         </button>
//         <p>{uploadStatus}</p>
//         <button onClick={onBack}>⬅ Back</button>
//       </div>
//     </div>
//   )
// }

// export default UploadPanel



"use client"

import { useEffect, useState } from "react"
import ChatPanel from "./chat"

type UploadPanelProps = {
  onBack: () => void
}

type User = {
  email: string
  name: string
  picture: string
}


const UploadPanel = ({ onBack }: UploadPanelProps) => {
  const [files, setFiles] = useState<File[]>([])
  const [webLinks, setWebLinks] = useState<string[]>([""])
  const [uploadStatus, setUploadStatus] = useState("")
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [user, setUser] = useState<User | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const handleWebLinkChange = (index: number, value: string) => {
    const updated = [...webLinks]
    updated[index] = value
    setWebLinks(updated)
  }

  const addWebLinkField = () => {
    setWebLinks([...webLinks, ""])
  }

  const handleFileUpload = async () => {
    if (files.length === 0 && webLinks.every((link) => link.trim() === "")) return

    const formData = new FormData()
    files.forEach((file) => formData.append("files", file))
    webLinks
      .filter((link) => link.trim() !== "")
      .forEach((link) => formData.append("web_links", link))

    setUploadStatus("⏳ Uploading files/web links...")
    setUploadSuccess(false)

    try {
      const res = await fetch("http://localhost:8000/api/ingress-file", {
        method: "POST",
        body: formData,
        credentials: "include",
      })

      if (res.ok) {
        setUploadStatus("✅ Upload successful!")
        setUploadSuccess(true)
      } else {
        setUploadStatus("❌ Upload failed. Try again.")
      }
    } catch (error) {
      console.error("Upload error:", error)
      setUploadStatus("❌ Upload failed. Check the console.")
    }
  }

  useEffect(() => {
    const storedUser = localStorage.getItem("user")
    if (storedUser) {
      setUser(JSON.parse(storedUser))
    }
  }, [])

  if (showChat && user) {
    return <ChatPanel user={user} onBack={onBack} />
  }

  return (
    <div className="center-wrapper">
      <div className="upload-section">
        <p>Select one or more files to upload and/or enter web links:</p>

        <input type="file" multiple onChange={handleFileChange} />

        <div>
          {webLinks.map((link, index) => (
            <input
              key={index}
              type="url"
              value={link}
              placeholder={`Enter web link ${index + 1}`}
              onChange={(e) => handleWebLinkChange(index, e.target.value)}
              className="web-link-input"
              style={{ display: "block", marginTop: "0.5rem" }}
            />
          ))}
          <button
            type="button"
            onClick={addWebLinkField}
            style={{
              marginTop: "0.5rem",
              fontSize: "0.875rem",
              color: "#555",
              border: "1px dashed #aaa",
              padding: "0.25rem 0.5rem",
              borderRadius: "4px",
              background: "#f9f9f9",
            }}
          >
            ➕ Add Another Web Link
          </button>
        </div>

        <button
          onClick={handleFileUpload}
          disabled={files.length === 0 && webLinks.every((w) => w.trim() === "")}
          style={{
            marginTop: "1rem",
            padding: "0.5rem 1rem",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "6px",
          }}
        >
          Upload
        </button>

        <p>{uploadStatus}</p>

        {uploadSuccess && (
          <button
            onClick={() => setShowChat(true)}
            style={{
              marginTop: "1rem",
              backgroundColor: "#28a745",
              color: "white",
              padding: "0.5rem 1rem",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
            }}
          >
            💬 Go to Chat
          </button>
        )}

        <button onClick={onBack} style={{ marginTop: "1rem" }}>
          ⬅ Back
        </button>
      </div>
    </div>
  )
}

export default UploadPanel
