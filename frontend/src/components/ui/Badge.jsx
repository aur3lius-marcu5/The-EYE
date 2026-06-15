export default function Badge({ variant = 'gold', children }) {
  return (
    <span className={`gothic-badge gothic-badge-${variant}`}>
      {children}
    </span>
  );
}
