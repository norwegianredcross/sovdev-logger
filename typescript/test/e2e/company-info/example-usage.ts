#!/usr/bin/env tsx

/**
 * 🚀 Example Usage of Norwegian Geo-Services Library
 *
 * This program demonstrates how to use the Norwegian Geo-Services Library
 * to lookup Norwegian addresses and companies.
 *
 * @author Terje Christensen (terchris)
 * @version 0.1.1
 */

import { NorwegianGeoServices, LibraryInfo } from './norwegian-geo-services/index.js';
import { TestEnv } from './norwegian-geo-services/shared/env-config.js';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

// Load .env file directly in Node.js
try {
  const envPath = join(process.cwd(), '.env');
  const envContent = readFileSync(envPath, 'utf8');
  const lines = envContent.split('\n');
  let loadedCount = 0;

  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine && !trimmedLine.startsWith('#')) {
      const equalIndex = trimmedLine.indexOf('=');
      if (equalIndex > 0) {
        const key = trimmedLine.substring(0, equalIndex).trim();
        const value = trimmedLine.substring(equalIndex + 1).trim();
        if (key && value) {
          process.env[key] = value;
          loadedCount++;
        }
      }
    }
  }
  console.log(`✅ Loaded .env file successfully (${loadedCount} variables)`);
} catch (error) {
  console.log('⚠️  Could not load .env file:', error instanceof Error ? error.message : String(error));
}

async function main() {
  console.log('🇳🇴 Norwegian Geo-Services Library Demo');
  console.log('=====================================\n');

  // Show environment configuration being used
  console.log('🔧 Environment Configuration');
  console.log('--------------------------');
  const testCompaniesList = TestEnv.getCompanies(['937891377', '971277882', '914749360']);
  const testAddressesAll = TestEnv.getAddresses([
    { query: 'Karl Johans gate 1, Oslo', maxResults: 5, includeCoordinates: true }
  ]);
  console.log(`ENV TEST_COMPANIES_LIST: ${process.env.TEST_COMPANIES_LIST || '(missing)'}`);
  console.log(`ENV TEST_ADDRESSES_JSON: ${process.env.TEST_ADDRESSES_JSON || '(missing)'}`);
  console.log(`Parsed companies (${testCompaniesList.length}): [${testCompaniesList.join(', ')}]`);
  console.log(`Parsed addresses (${testAddressesAll.length}): [${testAddressesAll.map((a: any) => a.query).join(' | ')}]`);
  console.log();

  try {
    // Example 1: Address Lookup
    console.log('📍 Address Lookup Example');
    console.log('------------------------');

    // Loop through all test addresses and print results incrementally
    for (const addrInput of testAddressesAll as any[]) {
      console.log(`➡️  Searching address: "${addrInput.query}"`);
      const addressResult = await NorwegianGeoServices.services.addressLookup.searchAddresses(addrInput);
      console.log(`   Found: ${addressResult.metadata.totalFound} (source: ${addressResult.source})`);
      addressResult.addresses.slice(0, 3).forEach((addr, i) => {
        console.log(`     ${i + 1}. ${addr.addressText}, ${addr.postalCode} ${addr.postTown}`);
        if (addr.coordinates) {
          console.log(`        📍 ${addr.coordinates.lat}, ${addr.coordinates.lon}`);
        }
      });
      console.log();
    }

    // Example 2: Company Lookup
    console.log('🏢 Company Lookup Example');
    console.log('-----------------------');

    // Loop through companies and print results incrementally
    for (const org of testCompaniesList) {
      console.log(`➡️  Looking up company: ${org}`);
      try {
        const companyResult = await NorwegianGeoServices.services.companyLookup.lookupCompany(org);
        console.log(`   Name: ${companyResult.company.navn}`);
        console.log(`   Status: ${companyResult.statusDescription} | Active: ${companyResult.isActive ? '✅' : '❌'}`);
        console.log(`   Sector: ${companyResult.sector} | Risk: ${companyResult.riskLevel}`);
        if (companyResult.company.forretningsadresse?.adresse) {
          const addr = companyResult.company.forretningsadresse.adresse[0];
          console.log(`   Address: ${addr.adresse}, ${addr.postnummer} ${addr.poststed}`);
        }
      } catch (error) {
        console.log(`   ❌ Lookup failed: ${error instanceof Error ? error.message : String(error)}`);
      }
      console.log();
    }

    // Example 3: Using Direct API Access
    console.log('🔧 Direct API Access Example');
    console.log('---------------------------');

    const directAddresses = await NorwegianGeoServices.apis.geonorge.searchAddresses({
      query: 'Bergen',
      maxResults: 3
    });

    console.log(`Direct Geonorge API found ${directAddresses.length} addresses:`);
    directAddresses.forEach((addr, i) => {
      console.log(`  ${i + 1}. ${addr.adressetekst || addr.addressText || 'No address text available'}`);
    });

    console.log('\n');

    // Batch summary removed; incremental outputs above are sufficient

  } catch (error) {
    console.error('❌ Error:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// Library info
console.log(`📚 Library Info:`);
console.log(`   Name: ${LibraryInfo.name}`);
console.log(`   Version: ${LibraryInfo.version}`);
console.log(`   Author: ${LibraryInfo.author}`);
console.log();

// Run the demo
main().catch(console.error);
