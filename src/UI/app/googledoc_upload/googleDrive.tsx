export async function uploadToGoogleDocs(proposalText: string, state: object): Promise<string | null> {
  const refresh_token = localStorage.getItem("refresh_token");

  if (!refresh_token) {
    alert("Google refresh token missing. Please log in or configure it first.");
    return null;
  }

  console.log("State being sent:", state)

  const response = await fetch("http://127.0.0.1:8000/save-to-drive", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      state: state,             
      refresh_token: refresh_token,
    }),
  });

  const data = await response.json();
  return response.ok ? data.view_link : null;
}
