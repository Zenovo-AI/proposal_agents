// export async function uploadToGoogleDocs(proposalText: string, state: object): Promise<string | null> {
//   const refresh_token = localStorage.getItem("refresh_token");

//   if (!refresh_token) {
//     alert("Google refresh token missing. Please log in or configure it first.");
//     return null;
//   }

//   console.log("State being sent:", state)

//   const response = await fetch("http://localhost:8000/save-to-drive", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({
//       state: state,             
//       refresh_token: refresh_token,
//     }),
//   });

//   const data = await response.json();
//   return response.ok ? data.view_link : null;
// }



interface UploadProposalOptions {
  proposalText: string;
  state: object;
  rfq_id: string;
  is_winning: boolean;
}

export async function uploadToGoogleDocs({
  state,
  rfq_id,
  is_winning,
}: UploadProposalOptions): Promise<string | null> {
  const refresh_token = localStorage.getItem("refresh_token");

  if (!refresh_token) {
    alert("Google refresh token missing. Please log in or configure it first.");
    return null;
  }

  console.log("Payload being sent to FastAPI:", {
    state,
    refresh_token,
    rfq_id,
    is_winning,
  });

  try {
    const response = await fetch("https://proposal-generator-app-b2pah.ondigitalocean.app/save-to-drive", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        state,
        refresh_token,
        rfq_id,
        is_winning,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      console.error("Failed to upload proposal:", data);
      return null;
    }

    return data.view_link;
  } catch (error) {
    console.error("Unexpected error uploading proposal:", error);
    return null;
  }
}
