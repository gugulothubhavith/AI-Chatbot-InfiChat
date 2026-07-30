import { create } from "zustand";

type PaletteState = {
  open: boolean;
  setOpen: (v: boolean) => void;
  toggle: () => void;
};

export const usePaletteStore = create<PaletteState>((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
  toggle: () => set((s) => ({ open: !s.open })),
}));
