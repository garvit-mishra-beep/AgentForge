export default function Loading() {
  return (
    <div className="fixed top-0 left-0 right-0 z-[60] h-0.5">
      <div className="h-full bg-primary animate-pulse rounded-full" style={{ width: "30%" }} />
    </div>
  );
}
