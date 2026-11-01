/**
 * Visitor counts come from GoatCounter, which sets no cookies and keeps no personal data; its dashboard shows
 * pages, countries, referrers, browsers and screen sizes. The site stays static, so nothing is collected until
 * a GoatCounter site code is set (NEXT_PUBLIC_GOATCOUNTER, in the Pages workflow).
 */
export const GOATCOUNTER_CODE = process.env.NEXT_PUBLIC_GOATCOUNTER ?? "";

export const goatcounterEndpoint = (code: string) => `https://${code}.goatcounter.com/count`;
export const dashboardUrl = (code: string) => `https://${code}.goatcounter.com`;
