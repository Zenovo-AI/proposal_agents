// // components/panels/upload.tsx
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
//       const res = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/ingress-file", {
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

import { useState } from "react"

type UploadPanelProps = {
  onBack: () => void
}

const UploadPanel = ({ onBack }: UploadPanelProps) => {
  const [files, setFiles] = useState<File[]>([])
  const [webLinks, setWebLinks] = useState<string[]>([])
  const [uploadStatus, setUploadStatus] = useState("")
  const [currentLink, setCurrentLink] = useState("")

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const handleAddWebLink = () => {
    if (currentLink.trim() !== "") {
      setWebLinks((prev) => [...prev, currentLink.trim()])
      setCurrentLink("")
    }
  }

  const handleFileUpload = async () => {
    if (files.length === 0 && webLinks.length === 0) return

    const formData = new FormData()
    files.forEach((file) => {
      formData.append("files", file) 
    })
    webLinks.forEach((link) => {
      formData.append("web_links", link)
    })

    setUploadStatus("⏳ Uploading files and web links...")

    try {
      const res = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/ingress-file", {
        method: "POST",
        body: formData,
        credentials: "include",
      })

      if (res.ok) {
        setUploadStatus("✅ Upload successful!")
        setFiles([])
        setWebLinks([])
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
        <p>Select files to upload and/or add web links:</p>

        {/* File input */}
        <input type="file" onChange={handleFileChange} multiple />
        <ul>
          {files.map((file, idx) => (
            <li key={idx}>{file.name}</li>
          ))}
        </ul>

        {/* Web link input */}
        <div className="web-link-input-wrapper">
          <input
            type="url"
            placeholder="Enter a web link"
            value={currentLink}
            onChange={(e) => setCurrentLink(e.target.value)}
            className="web-link-input"
          />
          <button onClick={handleAddWebLink}>Add Link</button>
        </div>
        <ul>
          {webLinks.map((link, idx) => (
            <li key={idx}>{link}</li>
          ))}
        </ul>

        {/* Upload */}
        <button onClick={handleFileUpload} disabled={files.length === 0 && webLinks.length === 0}>
          Upload
        </button>

        <p>{uploadStatus}</p>
        <button onClick={onBack}>⬅ Back</button>
      </div>
    </div>
  )
}

export default UploadPanel
