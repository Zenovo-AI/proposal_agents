/**
 * Bubble Component
 * ----------------
 * This component displays an individual chat message inside a styled bubble.
 * 
 * Props:
 * - message: An object containing:
 *   - content (string): The text of the message.
 *   - role (string): The sender of the message (e.g., "user" or "assistant").
 * 
 * How it works:
 * - The message content is shown inside a <div>.
 * - The <div> has two CSS classes:
 *   1. One for the role (e.g., "user" or "assistant") to style messages differently.
 *   2. A shared "bubble" class that gives it the bubble appearance.
 * 
 * Example usage:
 * <Bubble message={{ content: "Hello!", role: "user" }} />
 * 
 * This component is used in the chat interface to display each chat entry.
 */


interface Message {
    content: string;
    role: string;
}

const Bubble = ({ message }: { message: Message }) => {
    const { content, role} = message
    return (
        <div className={`${role} bubble`}>{content}</div>
    )
}

export default Bubble