import type { WasteType } from '../types';
import { wasteTypeColors, wasteTypeLabels, colors } from '../config/theme';
import './FilterPills.css';

interface FilterPillsProps {
  activeFilter: WasteType | null;
  onFilterChange: (type: WasteType | null) => void;
}

const filters: { label: string; value: WasteType | null }[] = [
  { label: 'Tutti', value: null },
  { label: wasteTypeLabels.organic, value: 'organic' },
  { label: wasteTypeLabels.paper, value: 'paper' },
  { label: wasteTypeLabels.plastic, value: 'plastic' },
  { label: wasteTypeLabels.glass, value: 'glass' },
  { label: wasteTypeLabels.mixed, value: 'mixed' },
];

export default function FilterPills({ activeFilter, onFilterChange }: FilterPillsProps) {
  return (
    <div className="filter-pills">
      {filters.map(({ label, value }) => {
        const isActive = activeFilter === value;
        const pillColor = value ? wasteTypeColors[value] : colors.primaryDark;

        return (
          <button
            key={label}
            className={`pill ${isActive ? 'pill-active' : ''}`}
            style={isActive ? { backgroundColor: pillColor, color: '#fff', borderColor: pillColor } : {}}
            onClick={() => onFilterChange(value)}
          >
            {value && <span className="pill-dot" style={{ backgroundColor: isActive ? '#fff' : pillColor }} />}
            {label}
          </button>
        );
      })}
    </div>
  );
}
