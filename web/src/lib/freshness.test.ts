import { describe, expect, it } from "vitest";
import { CARS, FX, carName } from "./market";
import { TABLE, exactAgeYears } from "./tax";

// Checks against today's date, so they are skipped in the normal test run (which must not break as time
// passes) and run monthly by .github/workflows/freshness.yml. A failure there emails the repo owner.
const TODAY = new Date();
const DAY = 24 * 3600 * 1000;
const FX_MAX_DAYS = 120;

describe.runIf(process.env.FRESHNESS)("site freshness", () => {
  it("lists no car too old to import as recon today (roll the model years forward each January)", () => {
    const tooOld = CARS.filter((c) => exactAgeYears(c.year, TODAY) > TABLE.reconAgeLimitYears);
    expect(tooOld.map(carName)).toEqual([]);
  });

  it("uses the tax year in force today (a new budget takes effect each 1 July)", () => {
    const endYear = 2000 + Number(TABLE.fiscalYear.split("-")[1]);
    expect(TODAY.getTime(), `FY${TABLE.fiscalYear} ended 30 June ${endYear}`).toBeLessThan(new Date(endYear, 6, 1).getTime());
  });

  it(`has exchange rates under ${FX_MAX_DAYS} days old`, () => {
    const days = Math.floor((TODAY.getTime() - new Date(FX.asOf).getTime()) / DAY);
    expect(days, `rates set ${FX.asOf}`).toBeLessThanOrEqual(FX_MAX_DAYS);
  });
});
