module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  parser: "@typescript-eslint/parser",
  plugins: ["react-refresh"],
  ignorePatterns: ["dist", "node_modules"],
  rules: {
    "react-refresh/only-export-components": "off",
    "@typescript-eslint/no-explicit-any": "off",
  },
};
