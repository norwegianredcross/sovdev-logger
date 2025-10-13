#!/usr/bin/env tsx

/**
 * 🏢 Example: Company Address Verification Flow
 *
 * Staged execution per company:
 *   1) Load input, print parsed org numbers
 *   2) Lookup company in BRREG, print core info
 *   3) Extract and normalize company address
 *   4) Verify address via Kartverket first
 *   5) If not found, verify via Geonorge
 *   6) Print per-company outcome (no global summary)
 */

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { NorwegianGeoServices } from './norwegian-geo-services/index.js';
import { TestEnv } from './norwegian-geo-services/shared/env-config.js';

// Minimal .env loader (same approach as example-usage)
try {
  const envPath = join(process.cwd(), '.env');
  const envContent = readFileSync(envPath, 'utf8');
  const lines = envContent.split('\n');
  let loadedCount = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const idx = trimmed.indexOf('=');
    if (idx > 0) {
      const key = trimmed.substring(0, idx).trim();
      const value = trimmed.substring(idx + 1).trim();
      if (key && value) {
        process.env[key] = value;
        loadedCount++;
      }
    }
  }
  console.log(`✅ Loaded .env file (${loadedCount} vars)`);
} catch {
  console.log('⚠️  No .env file found or could not be read');
}

type CompanyAddressInput = {
  query: string;
  maxResults?: number;
  includeCoordinates?: boolean;
};

function formatBrregAddress(addr: any): string {
  if (!addr) return '(missing)';
  const street = Array.isArray(addr.adresse) ? addr.adresse.join(' ') : addr.adresse;
  const postnr = addr.postnummer || addr.postnr || '';
  const poststed = addr.poststed || '';
  const land = addr.land || '';
  return [street, postnr, poststed, land].filter(Boolean).join(', ');
}

function normalizeBrregAddress(company: any): CompanyAddressInput | null {
  const business = company?.forretningsadresse;
  const postal = company?.postadresse;

  const pick = (addr: any) => {
    if (!addr) return null;
    // Prefer full line when present; otherwise construct from parts
    const street = Array.isArray(addr.adresse) ? addr.adresse[0] : addr.adresse;
    const postnr = addr.postnummer || addr.postnr || '';
    const poststed = addr.poststed || '';
    const parts = [street, postnr, poststed].filter(Boolean);
    if (parts.length === 0) return null;
    return { query: parts.join(', ').replace(/\s+/g, ' ').trim(), maxResults: 3 };
  };

  return pick(business) || pick(postal) || null;
}

async function verifyWithKartverket(addr: CompanyAddressInput) {
  // Placeholder Kartverket client returns [] currently
  const results = await NorwegianGeoServices.apis.kartverket.searchAddresses(addr);
  const found = Array.isArray(results) && results.length > 0;
  return {
    source: 'kartverket' as const,
    found,
    top: found ? results[0] : null,
    results
  };
}

async function verifyWithGeonorge(addr: CompanyAddressInput) {
  const results = await NorwegianGeoServices.apis.geonorge.searchAddresses(addr);
  const found = Array.isArray(results) && results.length > 0;
  return {
    source: 'geonorge' as const,
    found,
    top: found ? results[0] : null,
    results
  };
}

async function main() {
  console.log('🏢 Company Address Verification');
  console.log('==============================');

  // Stage 1: Load input
  // Prefer BRREG updates if BRREG_UPDATES_SINCE is provided; otherwise fallback to env TEST_COMPANIES_LIST
  let orgsSource = 'env';
  let orgs = TestEnv.getCompanies([]);
  const since = process.env.BRREG_UPDATES_SINCE; // e.g. 2024-01-01T00:00:00
  if (since) {
    try {
      const pageSize = parseInt(process.env.BRREG_UPDATES_PAGE_SIZE || '100');
      const maxPages = parseInt(process.env.BRREG_UPDATES_MAX_PAGES || '1');
      const limit = parseInt(process.env.BRREG_UPDATES_LIMIT || '0');

      const updates = await NorwegianGeoServices.apis.brreg.getUpdatesSince(since, { pageSize, maxPages });
      const uniqueOrgNrs = new Set<string>();
      for (const u of updates) {
        if (u?.organisasjonsnummer) uniqueOrgNrs.add(u.organisasjonsnummer);
      }
      let list = Array.from(uniqueOrgNrs);
      if (limit > 0) list = list.slice(0, limit);
      if (list.length > 0) {
        orgs = list;
        orgsSource = 'brreg-updates';
      }
    } catch (err) {
      console.log('⚠️  BRREG updates fetch failed, falling back to env companies:', err instanceof Error ? err.message : String(err));
    }
  }
  console.log('Stage 1 - Input');
  console.log(`ENV TEST_COMPANIES_LIST: ${process.env.TEST_COMPANIES_LIST || '(missing)'}`);
  console.log(`ENV BRREG_UPDATES_SINCE: ${process.env.BRREG_UPDATES_SINCE || '(missing)'}`);
  if (since) {
    console.log(`ENV BRREG_UPDATES_PAGE_SIZE: ${process.env.BRREG_UPDATES_PAGE_SIZE || '100'}`);
    console.log(`ENV BRREG_UPDATES_MAX_PAGES: ${process.env.BRREG_UPDATES_MAX_PAGES || '1'}`);
    console.log(`ENV BRREG_UPDATES_LIMIT: ${process.env.BRREG_UPDATES_LIMIT || '(none)'}`);
  }
  console.log(`Parsed org numbers (${orgs.length}) [source=${orgsSource}]: [${orgs.join(', ')}]`);
  console.log();

  for (const org of orgs) {
    console.log(`— Company: ${org}`);

    // Stage 2: BRREG lookup
    try {
      const company = await NorwegianGeoServices.apis.brreg.getCompany(org);
      console.log('  Stage 2 - BRREG');
      console.log(`    Name: ${company.navn}`);
      console.log(`    Org: ${company.organisasjonsnummer}`);
      console.log(`    Status: ${company.organisasjonsform?.beskrivelse || 'Unknown'}`);
      if (company.forretningsadresse) {
        console.log(`    Forretningsadresse: ${formatBrregAddress(company.forretningsadresse)}`);
      }
      if (company.postadresse) {
        console.log(`    Postadresse:       ${formatBrregAddress(company.postadresse)}`);
      }

      // Stage 3: Extract address
      const addrInput = normalizeBrregAddress(company);
      if (!addrInput) {
        console.log('  Stage 3 - Address');
        console.log('    ❌ No usable address found in BRREG');
        console.log();
        continue; // next company
      }
      console.log('  Stage 3 - Address');
      console.log(`    Query: ${addrInput.query}`);

      // Stage 4: Kartverket verification first
      console.log('  Stage 4 - Kartverket');
      const kv = await verifyWithKartverket(addrInput);
      if (kv.found) {
        console.log('    ✅ Match found via Kartverket');
        (kv.results || []).slice(0, 3).forEach((a: any, i: number) =>
          console.log(`    ${i === 0 ? '->' : '   '} ${a.addressText || a.adressetekst || 'Address text unavailable'}`)
        );
        console.log();
        continue; // Done for this company
      } else {
        console.log('    ❌ No match via Kartverket');
      }

      // Stage 5: Geonorge fallback
      console.log('  Stage 5 - Geonorge');
      const gn = await verifyWithGeonorge(addrInput);
      if (gn.found) {
        console.log('    ✅ Match found via Geonorge');
        (gn.results || []).slice(0, 3).forEach((a: any, i: number) =>
          console.log(`    ${i === 0 ? '->' : '   '} ${a.addressText || a.adressetekst || 'Address text unavailable'}`)
        );
      } else {
        console.log('    ❌ No match via Geonorge');
      }
      console.log();
    } catch (error) {
      console.log('  Stage 2 - BRREG');
      console.log(`    ❌ BRREG lookup failed: ${error instanceof Error ? error.message : String(error)}`);
      console.log();
      // proceed to next company
    }
  }
}

main().catch(err => {
  console.error('❌ Fatal error:', err instanceof Error ? err.message : String(err));
  process.exit(1);
});


