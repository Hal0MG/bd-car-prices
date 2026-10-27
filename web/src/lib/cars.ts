import type { CarModel } from "./market";

type Row = [make: string, model: string, year: number, cc: number, fuel: CarModel["fuel"], body: CarModel["body"], exampleFob: number];

// Example FOB prices are rough auction-level starting points, not quotes.
// Every car here is built in Japan.
const JAPAN: Row[] = [
  // Toyota
  ["Toyota", "Axio", 2021, 1496, "petrol", "car", 1_300_000],
  ["Toyota", "Axio Hybrid", 2022, 1496, "hybrid", "car", 1_450_000],
  ["Toyota", "Fielder", 2021, 1496, "petrol", "car", 1_350_000],
  ["Toyota", "Fielder Hybrid", 2021, 1496, "hybrid", "car", 1_550_000],
  ["Toyota", "Premio", 2021, 1496, "petrol", "car", 1_900_000],
  ["Toyota", "Allion", 2021, 1496, "petrol", "car", 1_850_000],
  ["Toyota", "Aqua", 2022, 1490, "hybrid", "car", 1_550_000],
  ["Toyota", "Yaris Hybrid", 2022, 1490, "hybrid", "car", 1_600_000],
  ["Toyota", "Prius", 2022, 1797, "hybrid", "car", 2_100_000],
  ["Toyota", "Prius Alpha", 2021, 1797, "hybrid", "car", 1_700_000],
  ["Toyota", "Corolla Touring Hybrid", 2022, 1797, "hybrid", "car", 1_900_000],
  ["Toyota", "Corolla Cross Hybrid", 2022, 1797, "hybrid", "car", 2_500_000],
  ["Toyota", "Yaris Cross Hybrid", 2022, 1490, "hybrid", "car", 2_000_000],
  ["Toyota", "Raize", 2022, 996, "petrol", "car", 1_600_000],
  ["Toyota", "C-HR", 2022, 1196, "petrol", "car", 1_900_000],
  ["Toyota", "C-HR Hybrid", 2022, 1797, "hybrid", "car", 2_150_000],
  ["Toyota", "Harrier", 2022, 1986, "petrol", "car", 3_000_000],
  ["Toyota", "Harrier Hybrid", 2022, 2487, "hybrid", "car", 3_800_000],
  ["Toyota", "RAV4", 2022, 1986, "petrol", "car", 2_700_000],
  ["Toyota", "RAV4 Hybrid", 2022, 2487, "hybrid", "car", 3_300_000],
  ["Toyota", "Camry Hybrid", 2022, 2487, "hybrid", "car", 2_800_000],
  ["Toyota", "Crown Crossover", 2023, 2487, "hybrid", "car", 4_200_000],
  ["Toyota", "Land Cruiser Prado TX", 2022, 2693, "petrol", "car", 4_800_000],
  ["Toyota", "Noah", 2022, 1986, "petrol", "microbus", 2_700_000],
  ["Toyota", "Noah Hybrid", 2022, 1797, "hybrid", "microbus", 3_100_000],
  ["Toyota", "Voxy Hybrid", 2022, 1797, "hybrid", "microbus", 3_200_000],
  ["Toyota", "Esquire Hybrid", 2021, 1797, "hybrid", "microbus", 2_300_000],
  ["Toyota", "HiAce", 2022, 2754, "diesel", "microbus", 3_500_000],
  // Honda
  ["Honda", "Fit e:HEV", 2022, 1496, "hybrid", "car", 1_600_000],
  ["Honda", "Grace Hybrid", 2021, 1496, "hybrid", "car", 1_300_000],
  ["Honda", "Insight", 2021, 1496, "hybrid", "car", 1_900_000],
  ["Honda", "Vezel e:HEV", 2022, 1496, "hybrid", "car", 2_400_000],
  ["Honda", "Civic", 2022, 1496, "petrol", "car", 2_600_000],
  ["Honda", "CR-V e:HEV", 2022, 1993, "hybrid", "car", 3_000_000],
  // Nissan
  ["Nissan", "Note e-Power", 2022, 1198, "hybrid", "car", 1_500_000],
  ["Nissan", "Kicks e-Power", 2022, 1198, "hybrid", "car", 1_800_000],
  ["Nissan", "X-Trail e-Power", 2023, 1497, "hybrid", "car", 3_400_000],
  ["Nissan", "Serena e-Power", 2022, 1433, "hybrid", "microbus", 2_600_000],
  // Mitsubishi
  ["Mitsubishi", "Outlander PHEV", 2022, 2359, "phev", "car", 3_800_000],
  ["Mitsubishi", "Eclipse Cross PHEV", 2022, 2359, "phev", "car", 2_900_000],
  // Mazda
  ["Mazda", "CX-5 2.0 Petrol", 2022, 1997, "petrol", "car", 2_300_000],
  ["Mazda", "CX-5 2.2 Diesel", 2022, 2188, "diesel", "car", 2_500_000],
  // Subaru
  ["Subaru", "Forester e-Boxer", 2022, 1995, "hybrid", "car", 2_400_000],
  ["Subaru", "XV e-Boxer", 2022, 1995, "hybrid", "car", 2_000_000],
  // Lexus
  ["Lexus", "NX 350h", 2022, 2487, "hybrid", "car", 5_000_000],
  ["Lexus", "RX 350h", 2023, 2487, "hybrid", "car", 6_500_000],
  // Suzuki
  ["Suzuki", "Swift", 2022, 1242, "petrol", "car", 1_000_000],
];

// Bangladesh only admits used cars from their country of origin, so every car
// here is built in the UK (Solihull, Halewood, Oxford, Sunderland, Burnaston).
const UK: Row[] = [
  ["Land Rover", "Range Rover Evoque", 2022, 1997, "diesel", "car", 24_000],
  ["Land Rover", "Range Rover Velar", 2022, 1997, "diesel", "car", 33_000],
  ["Land Rover", "Range Rover Sport", 2022, 2997, "diesel", "car", 60_000],
  ["Land Rover", "Discovery Sport", 2022, 1997, "diesel", "car", 25_000],
  ["Jaguar", "F-Pace", 2022, 1997, "diesel", "car", 30_000],
  ["Jaguar", "XE", 2022, 1997, "diesel", "car", 20_000],
  ["Mini", "Cooper", 2022, 1499, "petrol", "car", 15_000],
  ["Mini", "Clubman", 2022, 1499, "petrol", "car", 17_000],
  ["Nissan", "Qashqai", 2022, 1332, "petrol", "car", 18_000],
  ["Nissan", "Juke", 2022, 999, "petrol", "car", 14_000],
  ["Toyota", "Corolla Hybrid (UK-built)", 2022, 1798, "hybrid", "car", 17_000],
];

const toModel = (origin: CarModel["origin"], builtIn: CarModel["builtIn"]) =>
  ([make, model, year, cc, fuel, body, exampleFob]: Row): CarModel =>
    ({ make, model, year, cc, fuel, body, origin, builtIn, exampleFob });

export const CARS: CarModel[] = [...JAPAN.map(toModel("japan", "Japan")), ...UK.map(toModel("uk", "UK"))];
