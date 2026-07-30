export const spring = { type: "spring", stiffness: 400, damping: 30 } as const;
export const softSpring = { type: "spring", stiffness: 260, damping: 26 } as const;
export const tapProps = {
  whileHover: { y: -1 },
  whileTap: { scale: 0.97 },
  transition: spring,
} as const;
