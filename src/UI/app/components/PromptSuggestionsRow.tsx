/**
 * PromptSuggestionsRow Component
 * ------------------------------
 * This component displays a row of pre-defined prompt suggestions as clickable buttons.
 * 
 * Props:
 * - onPromptClick (function): A callback function that is triggered when a prompt button is clicked. It receives the prompt string as an argument.
 * 
 * Internal Logic:
 * - Contains a fixed list of sample prompts related to CDGA (the organization).
 * - Maps each prompt to a PromptSuggestionButton component.
 * - When a user clicks a button, the corresponding prompt text is passed to the onPromptClick handler.
 * 
 * Example Usage:
 * <PromptSuggestionsRow onPromptClick={handlePrompt} />
 * 
 * Styling:
 * - The row is styled using the "prompt-suggestion-row" CSS class.
 * 
 * Purpose:
 * - To help users quickly engage with the chatbot by offering relevant, clickable example questions.
 */

import { useEffect, useState } from "react";
import PromptSuggestionButton from "./PromptSuggestionButton";

type PromptSuggestionsRowProps = {
  onPromptClick: (prompt: string) => void;
  rfqId?: string;
};

const PromptSuggestionsRow = ({
  onPromptClick,
  rfqId,
}: PromptSuggestionsRowProps) => {
  const [prompts, setPrompts] = useState<string[]>([]);

  useEffect(() => {
    console.log("🌱 PromptSuggestionsRow received rfqId:", rfqId);

    const fetchPrompts = async () => {
      const body = { rfq_id: rfqId ?? null };
      console.log("→ sending body:", body);

      try {
        const res = await fetch("http://localhost:8000/api/prompt-suggestions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(body),
        });
        const data = await res.json();
        setPrompts(data.prompts || []);
      } catch (err) {
        console.error("Error fetching prompt suggestions:", err);
        setPrompts([]);
      }
    };

    fetchPrompts();
  }, [rfqId]);

  return (
    <div className="prompt-suggestion-row">
      {prompts.map((prompt, index) => (
        <PromptSuggestionButton
          key={`suggestion-${index}`}
          text={prompt}
          onClick={() => onPromptClick(prompt)}
        />
      ))}
    </div>
  );
};

export default PromptSuggestionsRow;




// const PromptSuggestionsRow = ({ onPromptClick }: { onPromptClick: (prompt: string) => void }) => {
//     const [prompts, setPrompts] = useState<string[]>([])

//     useEffect(() => {
//         const fetchPrompts = async () => {
//             try {
//                 const res = await fetch("http://localhost:8000/prompt-suggestions", {
//                 credentials: "include"
//                 })
//                 const data = await res.json()
//                 setPrompts(data.prompts)
//             } catch (err) {
//                 console.error("Failed to fetch prompts", err)
//             }
//         }

//         fetchPrompts()
//     }, [])

//     return (
//         <div className="prompt-suggestion-row">
//             {prompts.map((prompt, index) =>
//                 <PromptSuggestionButton
//                     key={`suggestion-${index}`}
//                     text={prompt}
//                     onClick={() => onPromptClick(prompt)}
//                 />
//             )}
//         </div>
//     )
// }

// export default PromptSuggestionsRow
