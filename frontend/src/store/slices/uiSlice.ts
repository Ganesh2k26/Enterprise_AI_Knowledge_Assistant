import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface UIState {
  theme: "light" | "dark";
  sidebarCollapsed: boolean;
}

const storedTheme = (localStorage.getItem("theme") as "light" | "dark" | null) ?? "dark";

const initialState: UIState = {
  theme: storedTheme,
  sidebarCollapsed: false,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleTheme: (state) => {
      state.theme = state.theme === "dark" ? "light" : "dark";
      localStorage.setItem("theme", state.theme);
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
  },
});

export const { toggleTheme, setSidebarCollapsed } = uiSlice.actions;
export default uiSlice.reducer;
