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


import PromptSuggestionButton from "./PromptSuggestionButton"

const PromptSuggestionsRow = ({ onPromptClick }: { onPromptClick: (prompt: string) => void }) => {
    const prompts = [
        "Who are CDGA’s primary international clients?",
        "What sectors does CDGA specialize in?",
        "Can you generate a proposal for a power infrastructure project in East Africa?",
        "What experience does CDGA have with remote or conflict zone operations?"
      ]
      
    return (
        <div className="prompt-suggestion-row">
            {prompts.map((prompt, index) => 
                <PromptSuggestionButton
                    key={`suggestion-${index}`}
                    text={prompt}
                    onClick={() => onPromptClick(prompt)}
                />)}
        </div>
    )
}

export default PromptSuggestionsRow