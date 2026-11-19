import "../../styles/components/MetricCard.css";

export function MetricCard({
  label,
  value,
  hint,
  tone,
  icon,
}: {
  label: string;
  value: number | string;
  hint?: string;
  tone: "green" | "amber" | "orange" | "red" | "brand";
  icon: React.ReactNode;
}) {
  return (
    <div className={`pt-metric-card tone-${tone}`}>
      <div className="pt-metric-top">
        <div className="pt-metric-icon">{icon}</div>
        <span className="pt-metric-label">{label}</span>
      </div>
      <div className="pt-metric-body">
        <span className="pt-metric-value">{value}</span>
        {hint && <span className="pt-metric-hint">{hint}</span>}
      </div>
    </div>
  );
}
