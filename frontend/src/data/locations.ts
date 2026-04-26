export interface LocationOption {
  id: string;
  label: string;
  emoji?: string;
}

export const BD_DIVISIONS: LocationOption[] = [
  { id: 'dhaka',       label: 'Dhaka',       emoji: '🏙️' },
  { id: 'chittagong',  label: 'Chittagong',  emoji: '⚓' },
  { id: 'sylhet',      label: 'Sylhet',      emoji: '🍃' },
  { id: 'rajshahi',    label: 'Rajshahi',    emoji: '🍇' },
  { id: 'khulna',      label: 'Khulna',      emoji: '🌿' },
  { id: 'barishal',    label: 'Barishal',    emoji: '🌊' },
  { id: 'mymensingh',  label: 'Mymensingh',  emoji: '🎓' },
  { id: 'rangpur',     label: 'Rangpur',     emoji: '🌾' },
];

export const POPULAR_CITIES: LocationOption[] = [
  { id: "cox's bazar",   label: "Cox's Bazar",   emoji: '🏖️' },
  { id: 'comilla',       label: 'Comilla',        emoji: '🏛️' },
  { id: 'gazipur',       label: 'Gazipur',        emoji: '🏭' },
  { id: 'narayanganj',   label: 'Narayanganj',    emoji: '⚓' },
  { id: 'tangail',       label: 'Tangail',        emoji: '🏘️' },
  { id: 'bogura',        label: 'Bogura',         emoji: '🏺' },
  { id: 'jessore',       label: 'Jessore',        emoji: '🌸' },
  { id: 'brahmanbaria',  label: 'Brahmanbaria',   emoji: '🕌' },
];

export const ALL_LOCATIONS: LocationOption[] = [
  ...BD_DIVISIONS,
  ...POPULAR_CITIES,
];
