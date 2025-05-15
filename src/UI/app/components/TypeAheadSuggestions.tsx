// this script is a React component that provides typeahead suggestions based on user input. 
//  filters a list of suggestions and displays them in a dropdown menu. 
// When a suggestion is clicked, it calls the onSelect function passed as a prop and hides the suggestions.
// The component uses React hooks to manage the visibility of the suggestions and to filter them based on the input.
// The component is designed to be reusable and can be used in various contexts where typeahead functionality is needed.

import React, { useState, useEffect } from 'react'

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
  const [isVisible, setIsVisible] = useState(false)

  const filteredSuggestions = suggestions.filter(suggestion =>
    suggestion.toLowerCase().includes(input.toLowerCase())
  )

  useEffect(() => {
    setIsVisible(input.length > 0 && filteredSuggestions.length > 0)
  }, [input, filteredSuggestions.length])

  if (!isVisible) return null

  return (
    <div className="suggestions">
      {filteredSuggestions.map((suggestion, index) => (
        <button
          key={index}
          className="suggestionItem"
          onClick={() => {
            onSelect(suggestion)
            setIsVisible(false)
          }}
        >
          {suggestion}
        </button>
      ))}
    </div>
  )
}

export default TypeaheadPrompts
