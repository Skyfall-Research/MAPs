module.exports = {
    plugins: [
        require('@tailwindcss/typography'),
    ],
    theme: {
        extend: {
            colors: {
                skyfall: {
                    bg: "#161616",
                    card: "#262626",
                    cardforeground: "#333333",
                }
            },
            fontFamily: {
                mono: ["JetBrains Mono", "monospace"],
                monocraft: ["Monocraft", "sans-serif"],
                spacemono: ["SpaceMono", "Courier New", "monospace"],
            },
        }
    }
}