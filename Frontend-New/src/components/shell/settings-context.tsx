import { createContext, useContext } from "react";

export const SettingsContext = createContext<{
  open: boolean;
  setOpen: (v: boolean) => void;
}>({ open: false, setOpen: () => {} });

export const useSettingsDialog = () => useContext(SettingsContext);
