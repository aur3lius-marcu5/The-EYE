export default function Card({ className = '', children, ...props }) {
  return (
    <div className={`gothic-card ${className}`} {...props}>
      {children}
    </div>
  );
}
