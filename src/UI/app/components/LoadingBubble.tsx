/**
 * LoadingBubble Component
 * -----------------------
 * This component shows a loading animation (usually when the chatbot is generating a response).
 * 
 * How it works:
 * - It returns a <div> with the class "loader".
 * - The "loader" class is styled using CSS to create a visual animation (e.g., spinning dots or pulsing).
 * 
 * This component is typically displayed right after the user sends a message and is waiting for the bot to reply.
 * 
 * Example usage:
 * <LoadingBubble />
 */


const LoadingBubble = () => {
    return (
      <div className="assistant bubble">
        <div className="loader"></div>
        <span style={{ fontSize: '0.8rem', color: '#888' }}>typing…</span>
      </div>
    )
  }
  

export default LoadingBubble