import React from 'react'

interface TypeaheadPromptsProps {
  input: string
  suggestions: string[]
  onSelect: (suggestion: string) => void
}

const TypeaheadPrompts: React.FC<TypeaheadPromptsProps> = ({
  input,
  suggestions,
  onSelect,
}) => {
  const filteredSuggestions = suggestions.filter(suggestion =>
    suggestion.toLowerCase().includes(input.toLowerCase())
  )

  if (!input || filteredSuggestions.length === 0) return null

  return (
    <div className="typeahead-suggestions">
      {filteredSuggestions.map((suggestion, index) => (
        <button
          key={index}
          onClick={() => onSelect(suggestion)}
          className="suggestion-item"
        >
          {suggestion}
        </button>
      ))}
    </div>
  )
}

export default TypeaheadPrompts