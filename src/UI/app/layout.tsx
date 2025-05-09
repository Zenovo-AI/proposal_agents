/**
 * Root Layout Component
 * ---------------------
 * This file sets up the base HTML layout and metadata for the entire app.
 *
 * import "./global.css"
 *     - Loads the global CSS file so that styling applies consistently across all pages.
 *
 * export const metadata
 *     - Defines the page title and description for SEO and browser display.
 *     - `title`: Appears in the browser tab.
 *     - `description`: Helps search engines understand the purpose of the app.
 *
 * RootLayout Component
 * --------------------
 * - Accepts `children` as a prop: this represents all nested UI elements.
 * - Wraps the entire application in standard HTML and sets the language to English.
 * - The `<body>` tag contains the actual content passed into the app (via `children`).
 *
 * export default RootLayout
 *     - Makes this layout component available for use in the app.
 */


import "./global.css"   // this will apply the styling to everything
import { ReactNode } from "react"

export const metadata = {
    title: "Proposal Assistant",
    description: "Your expert partner for crafting high-quality technical proposals tailored to the needs of international engineering and consultancy projects.",
}

const RootLayout = ({ children }: { children: ReactNode }) => {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    )
}

export default RootLayout