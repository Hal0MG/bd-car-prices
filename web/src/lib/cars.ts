import type { CarModel, Country, Origin, Segment } from "./market";

/** The last item is where the car was built, when that isn't the list's default. */
type Row = [make: string, model: string, year: number, cc: number, fuel: CarModel["fuel"], segment: Segment, exampleFob: number, builtIn?: Country];

// Example FOB prices are rough used-market starting points in the source
// currency, not quotes.
//
// Lists are grouped by where the car is bought. Bangladesh only admits
// right-hand-drive cars, and Germany sells left-hand drive, so German brands
// are listed as UK-market cars (priced in pounds) with their build country.

const JAPAN: Row[] = [
  // Toyota
  ["Toyota", "Axio", 2021, 1496, "petrol", "sedan", 1_300_000],
  ["Toyota", "Axio Hybrid", 2022, 1496, "hybrid", "sedan", 1_450_000],
  ["Toyota", "Fielder", 2021, 1496, "petrol", "wagon", 1_350_000],
  ["Toyota", "Fielder Hybrid", 2021, 1496, "hybrid", "wagon", 1_550_000],
  ["Toyota", "Premio", 2021, 1496, "petrol", "sedan", 1_900_000],
  ["Toyota", "Allion", 2021, 1496, "petrol", "sedan", 1_850_000],
  ["Toyota", "Aqua", 2022, 1490, "hybrid", "hatchback", 1_550_000],
  ["Toyota", "Yaris Hybrid", 2022, 1490, "hybrid", "hatchback", 1_600_000],
  ["Toyota", "GR Yaris", 2022, 1618, "petrol", "hatchback", 4_500_000],
  ["Toyota", "Prius", 2022, 1797, "hybrid", "hatchback", 2_100_000],
  ["Toyota", "Prius Alpha", 2021, 1797, "hybrid", "wagon", 1_700_000],
  ["Toyota", "Corolla Touring Hybrid", 2022, 1797, "hybrid", "wagon", 1_900_000],
  ["Toyota", "Corolla Cross Hybrid", 2022, 1797, "hybrid", "suv", 2_500_000],
  ["Toyota", "Yaris Cross Hybrid", 2022, 1490, "hybrid", "suv", 2_000_000],
  ["Toyota", "Raize", 2022, 996, "petrol", "suv", 1_600_000],
  ["Toyota", "C-HR", 2022, 1196, "petrol", "suv", 1_900_000],
  ["Toyota", "C-HR Hybrid", 2022, 1797, "hybrid", "suv", 2_150_000],
  ["Toyota", "Harrier", 2022, 1986, "petrol", "suv", 3_000_000],
  ["Toyota", "Harrier Hybrid", 2022, 2487, "hybrid", "suv", 3_800_000],
  ["Toyota", "RAV4", 2022, 1986, "petrol", "suv", 2_700_000],
  ["Toyota", "RAV4 Hybrid", 2022, 2487, "hybrid", "suv", 3_300_000],
  ["Toyota", "Camry Hybrid", 2022, 2487, "hybrid", "sedan", 2_800_000],
  ["Toyota", "Crown Crossover", 2023, 2487, "hybrid", "sedan", 4_200_000],
  ["Toyota", "Land Cruiser Prado TX", 2022, 2693, "petrol", "suv", 4_800_000],
  ["Toyota", "GR86", 2022, 2387, "petrol", "coupe", 3_000_000],
  ["Toyota", "Noah", 2022, 1986, "petrol", "minivan", 2_700_000],
  ["Toyota", "Noah Hybrid", 2022, 1797, "hybrid", "minivan", 3_100_000],
  ["Toyota", "Voxy Hybrid", 2022, 1797, "hybrid", "minivan", 3_200_000],
  ["Toyota", "Esquire Hybrid", 2021, 1797, "hybrid", "minivan", 2_300_000],
  ["Toyota", "HiAce", 2022, 2754, "diesel", "minivan", 3_500_000],
  // Honda
  ["Honda", "Fit e:HEV", 2022, 1496, "hybrid", "hatchback", 1_600_000],
  ["Honda", "Grace Hybrid", 2021, 1496, "hybrid", "sedan", 1_300_000],
  ["Honda", "Insight", 2021, 1496, "hybrid", "sedan", 1_900_000],
  ["Honda", "Vezel e:HEV", 2022, 1496, "hybrid", "suv", 2_400_000],
  ["Honda", "Civic", 2022, 1496, "petrol", "hatchback", 2_600_000],
  ["Honda", "Civic Type R", 2023, 1995, "petrol", "hatchback", 6_000_000],
  ["Honda", "CR-V e:HEV", 2022, 1993, "hybrid", "suv", 3_000_000],
  ["Honda", "S660", 2022, 658, "petrol", "convertible", 2_300_000],
  // Nissan
  ["Nissan", "Note e-Power", 2022, 1198, "hybrid", "hatchback", 1_500_000],
  ["Nissan", "Kicks e-Power", 2022, 1198, "hybrid", "suv", 1_800_000],
  ["Nissan", "X-Trail e-Power", 2023, 1497, "hybrid", "suv", 3_400_000],
  ["Nissan", "Serena e-Power", 2022, 1433, "hybrid", "minivan", 2_600_000],
  ["Nissan", "Fairlady Z", 2023, 2997, "petrol", "coupe", 6_000_000],
  ["Nissan", "GT-R", 2022, 3799, "petrol", "coupe", 14_000_000],
  // Mitsubishi
  ["Mitsubishi", "Outlander PHEV", 2022, 2359, "phev", "suv", 3_800_000],
  ["Mitsubishi", "Eclipse Cross PHEV", 2022, 2359, "phev", "suv", 2_900_000],
  // Mazda
  ["Mazda", "CX-5 2.0 Petrol", 2022, 1997, "petrol", "suv", 2_300_000],
  ["Mazda", "CX-5 2.2 Diesel", 2022, 2188, "diesel", "suv", 2_500_000],
  ["Mazda", "MX-5 Roadster", 2022, 1496, "petrol", "convertible", 2_600_000],
  ["Mazda", "MX-5 RF", 2022, 1997, "petrol", "convertible", 3_200_000],
  // Subaru
  ["Subaru", "Forester e-Boxer", 2022, 1995, "hybrid", "suv", 2_400_000],
  ["Subaru", "XV e-Boxer", 2022, 1995, "hybrid", "suv", 2_000_000],
  ["Subaru", "BRZ", 2022, 2387, "petrol", "coupe", 2_900_000],
  // Lexus
  ["Lexus", "NX 350h", 2022, 2487, "hybrid", "suv", 5_000_000],
  ["Lexus", "RX 350h", 2023, 2487, "hybrid", "suv", 6_500_000],
  ["Lexus", "LC 500 Convertible", 2022, 4968, "petrol", "convertible", 11_000_000],
  // Suzuki and Daihatsu
  ["Suzuki", "Swift", 2022, 1242, "petrol", "hatchback", 1_000_000],
  ["Daihatsu", "Copen", 2022, 658, "petrol", "convertible", 1_600_000],
];

// Built in the UK: Solihull, Halewood, Oxford, Sunderland, Burnaston, Crewe,
// Goodwood, Gaydon, St Athan, Woking, Hethel.
const UK: Row[] = [
  ["Land Rover", "Range Rover", 2022, 2997, "diesel", "suv", 95_000],
  ["Land Rover", "Range Rover Sport", 2022, 2997, "diesel", "suv", 60_000],
  ["Land Rover", "Range Rover Velar", 2022, 1997, "diesel", "suv", 33_000],
  ["Land Rover", "Range Rover Evoque", 2022, 1997, "diesel", "suv", 24_000],
  ["Land Rover", "Discovery Sport", 2022, 1997, "diesel", "suv", 25_000],
  ["Jaguar", "F-Pace", 2022, 1997, "diesel", "suv", 30_000],
  ["Jaguar", "XE", 2022, 1997, "diesel", "sedan", 20_000],
  ["Bentley", "Continental GT V8", 2022, 3996, "petrol", "coupe", 160_000],
  ["Bentley", "Continental GTC V8", 2022, 3996, "petrol", "convertible", 170_000],
  ["Bentley", "Flying Spur V8", 2022, 3996, "petrol", "sedan", 150_000],
  ["Bentley", "Bentayga V8", 2022, 3996, "petrol", "suv", 140_000],
  ["Rolls-Royce", "Ghost", 2022, 6749, "petrol", "sedan", 230_000],
  ["Rolls-Royce", "Cullinan", 2022, 6749, "petrol", "suv", 280_000],
  ["Aston Martin", "Vantage", 2022, 3982, "petrol", "coupe", 95_000],
  ["Aston Martin", "DBX", 2022, 3982, "petrol", "suv", 130_000],
  ["McLaren", "GT", 2022, 3994, "petrol", "coupe", 140_000],
  ["McLaren", "Artura", 2023, 2993, "phev", "coupe", 170_000],
  ["Lotus", "Emira", 2023, 3456, "petrol", "coupe", 80_000],
  ["Mini", "Cooper", 2022, 1499, "petrol", "hatchback", 15_000],
  ["Mini", "Clubman", 2022, 1499, "petrol", "wagon", 17_000],
  ["Nissan", "Qashqai", 2022, 1332, "petrol", "suv", 18_000],
  ["Nissan", "Juke", 2022, 999, "petrol", "suv", 14_000],
  ["Toyota", "Corolla Hybrid (UK-built)", 2022, 1798, "hybrid", "hatchback", 17_000],

  // German brands as right-hand-drive UK-market cars.
  ["Mercedes-Benz", "C 200", 2022, 1496, "petrol", "sedan", 32_500, "Germany"],
  ["Mercedes-Benz", "E 200", 2022, 1991, "petrol", "sedan", 34_500, "Germany"],
  ["Mercedes-Benz", "S 500", 2022, 2999, "petrol", "sedan", 82_000, "Germany"],
  ["Mercedes-Benz", "GLC 200", 2023, 1999, "petrol", "suv", 43_000, "Germany"],
  ["Mercedes-Benz", "C 300 Cabriolet", 2022, 1991, "petrol", "convertible", 36_000, "Germany"],
  ["Mercedes-Benz", "AMG GT", 2022, 3982, "petrol", "coupe", 94_500, "Germany"],
  ["BMW", "320i", 2022, 1998, "petrol", "sedan", 27_500, "Germany"],
  ["BMW", "530e", 2022, 1998, "phev", "sedan", 32_500, "Germany"],
  ["BMW", "740i", 2023, 2998, "petrol", "sedan", 82_000, "Germany"],
  ["BMW", "X1 sDrive18i", 2023, 1499, "petrol", "suv", 32_500, "Germany"],
  ["BMW", "M4 Convertible", 2022, 2993, "petrol", "convertible", 69_000, "Germany"],
  ["BMW", "i4 eDrive40", 2022, 0, "ev", "sedan", 38_500, "Germany"],
  ["Volkswagen", "Golf GTI", 2022, 1984, "petrol", "hatchback", 27_500, "Germany"],
  ["Volkswagen", "Passat", 2022, 1984, "petrol", "sedan", 23_000, "Germany"],
  ["Volkswagen", "Tiguan", 2022, 1395, "petrol", "suv", 24_000, "Germany"],
  ["Volkswagen", "ID.4", 2022, 0, "ev", "suv", 27_500, "Germany"],
  ["Audi", "A4", 2022, 1984, "petrol", "sedan", 27_500, "Germany"],
  ["Audi", "A6", 2022, 1984, "petrol", "sedan", 34_500, "Germany"],
  ["Audi", "A5 Cabriolet", 2022, 1984, "petrol", "convertible", 36_000, "Germany"],
  ["Audi", "e-tron GT", 2022, 0, "ev", "sedan", 69_000, "Germany"],
  ["Audi", "R8 V10", 2022, 5204, "petrol", "coupe", 129_000, "Germany"],
  ["Porsche", "911 Carrera", 2022, 2981, "petrol", "coupe", 99_000, "Germany"],
  ["Porsche", "718 Boxster", 2022, 1988, "petrol", "convertible", 56_000, "Germany"],
  ["Porsche", "Macan", 2022, 1984, "petrol", "suv", 51_500, "Germany"],
  ["Porsche", "Panamera", 2022, 2894, "petrol", "sedan", 82_000, "Germany"],
  ["Porsche", "Taycan", 2022, 0, "ev", "sedan", 69_000, "Germany"],

  // Not built in Germany or the UK, but sold new in the UK as right-hand drive.
  ["BMW", "X5 xDrive40i", 2022, 2998, "petrol", "suv", 48_000, "USA"],
  ["BMW", "Z4 sDrive20i", 2022, 1998, "petrol", "convertible", 35_000, "Austria"],
  ["Toyota", "GR Supra", 2022, 2998, "petrol", "coupe", 48_000, "Austria"],
  ["Audi", "Q3", 2022, 1498, "petrol", "suv", 27_000, "Hungary"],
  ["Audi", "Q5", 2022, 1984, "petrol", "suv", 38_000, "Mexico"],
  ["Audi", "Q7", 2022, 2995, "petrol", "suv", 50_000, "Slovakia"],
  ["Porsche", "Cayenne", 2022, 2995, "petrol", "suv", 62_000, "Slovakia"],
];

const toModel = (origin: Origin, defaultBuiltIn: Country) =>
  ([make, model, year, cc, fuel, segment, exampleFob, builtIn = defaultBuiltIn]: Row): CarModel => ({
    make, model, year, cc, fuel, segment, origin, builtIn, exampleFob,
    body: segment === "minivan" ? "microbus" : "car",
  });

export const CARS: CarModel[] = [
  ...JAPAN.map(toModel("japan", "Japan")),
  ...UK.map(toModel("uk", "UK")),
];
