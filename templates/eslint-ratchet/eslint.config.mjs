// Shared anti-pattern rules for a product repo. Copy and extend; do not weaken
// a rule to make a diff pass — lower the ratchet after the fixes land.
export default [
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    rules: {
      "no-implicit-coercion": "error",
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-empty": ["error", { allowEmptyCatch: false }],
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error"
    }
  }
];
