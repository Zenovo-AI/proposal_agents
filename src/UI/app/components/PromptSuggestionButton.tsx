/**
 * PromptSuggestionButton Component
 * --------------------------------
 * This component renders a single clickable button that suggests a prompt for the user to try.
 *
 * Props:
 * - text (string): The text to be displayed on the button (e.g., a sample question).
 * - onClick (function): A function to run when the button is clicked. Usually, this sends the prompt to the chatbot.
 *
 * Example usage:
 * <PromptSuggestionButton text="Draft a proposal for CTBTO" onClick={handlePromptClick} />
 *
 * Styling:
 * - The button uses the "prompt-suggestion-button" CSS class for styling.
 *
 * Purpose:
 * - Used to help users get started with example prompts in the chatbot interface.
 */


import React from 'react';

interface PromptSuggestionButtonProps {
    text: string;
    onClick: () => void;
}

const PromptSuggestionButton: React.FC<PromptSuggestionButtonProps> = ({ text, onClick }) => {
    return (
        <button 
            className="prompt-suggestion-button"
            onClick={onClick}
        >
            {text}
        </button>
    )
}

export default PromptSuggestionButton