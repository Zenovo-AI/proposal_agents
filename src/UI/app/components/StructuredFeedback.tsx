import React from 'react'

interface FeedbackOption {
  type: 'approve' | 'revise'
  label: string
  description?: string
}

interface FeedbackOptionsProps {
  options: FeedbackOption[]
  onSelect: (feedback: string) => void
}

const FeedbackOptions: React.FC<FeedbackOptionsProps> = ({ options, onSelect }) => {
  return (
    <div className="feedback-options">
      {options.map((option, index) => (
        <div key={index} className="feedback-option">
          <button
            onClick={() => onSelect(option.type)}
            className={`feedback-button ${option.type}`}
          >
            {option.type === 'approve' ? '✓' : '✎'} {option.label}
          </button>
          {option.description && (
            <p className="feedback-description">{option.description}</p>
          )}
        </div>
      ))}
    </div>
  )
}

export default FeedbackOptions