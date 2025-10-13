/**
 * 📦 Norwegian Geo-Services Library
 * 
 * A comprehensive TypeScript library for Norwegian geographical and business registry services
 * 
 * @author Terje Christensen (terchris)
 * @version 0.1.1
 * 
 * Architecture:
 * - Modular design with independent API clients (Geonorge, Kartverket, BRREG)
 * - High-level services for common use cases
 * - Shared types and error handling
 * 
 * Usage Examples:
 * 
 * ```typescript
 * // Direct API access (for advanced users)
 * import { geonorgeApi } from './norwegian-geo-services/geonorge';
 * const addresses = await geonorgeApi.searchAddresses({ query: 'Oslo' });
 * 
 * // High-level services (recommended for most users)
 * import { addressLookup, companyLookup } from './norwegian-geo-services/services';
 * const result = await addressLookup.searchAddresses({ query: 'Oslo' });
 * const company = await companyLookup.lookupCompany('971277882');
 * 
 * // Convenience object (everything in one place)
 * import { NorwegianGeoServices } from './norwegian-geo-services';
 * const addresses = await NorwegianGeoServices.services.addressLookup.searchAddresses(...);
 * ```
 */

// === SHARED TYPES AND ERRORS ===
export * from './shared/index.js';

// === API MODULES ===
// Each module is independently usable and can be imported separately

// Geonorge (Official Norwegian Mapping Authority address API)
export * from './geonorge/index.js';

// Kartverket (Additional mapping services)
export * from './kartverket/index.js';

// BRREG (Norwegian Business Registry)
export * from './brreg/index.js';

// === HIGH-LEVEL SERVICES ===
// Orchestration layer combining multiple APIs
export * from './services/index.js';

// === CONVENIENCE EXPORTS ===

import { geonorgeApi } from './geonorge/client.js';
import { kartverketApi } from './kartverket/client.js';
import { brregApi } from './brreg/client.js';
import { addressLookup } from './services/address-lookup.js';
import { companyLookup } from './services/company-lookup.js';

/**
 * Convenience object grouping all services and APIs
 * 
 * @example
 * ```typescript
 * import { NorwegianGeoServices } from './norwegian-geo-services';
 * 
 * // Use high-level services
 * const addresses = await NorwegianGeoServices.services.addressLookup.searchAddresses({
 *   query: 'Karl Johans gate 1, Oslo'
 * });
 * 
 * const company = await NorwegianGeoServices.services.companyLookup.lookupCompany('971277882');
 * 
 * // Or access API clients directly
 * const geonorgeResults = await NorwegianGeoServices.apis.geonorge.searchAddresses({
 *   query: 'Oslo',
 *   maxResults: 10
 * });
 * ```
 */
export const NorwegianGeoServices = {
  /**
   * High-level services (recommended)
   * These provide smart orchestration, validation, and error handling
   */
  services: {
    addressLookup,
    companyLookup
  },

  /**
   * Direct API clients (for advanced use)
   * Lower-level access to individual APIs
   */
  apis: {
    geonorge: geonorgeApi,
    kartverket: kartverketApi,
    brreg: brregApi
  }
} as const;

/**
 * Library metadata and information
 */
export const LibraryInfo = {
  name: 'Norwegian Geo-Services Library',
  version: '0.1.1',
  description: 'Comprehensive TypeScript library for Norwegian geographical and business registry services',
  author: 'Terje Christensen (terchris)',
  
  // Architecture
  architecture: {
    type: 'modular',
    modules: ['geonorge', 'kartverket', 'brreg', 'services', 'shared'],
    approach: 'API-first with service orchestration layer'
  },

  // Supported services
  services: {
    address: {
      providers: ['geonorge', 'kartverket'],
      features: ['search', 'validation', 'reverse-geocoding', 'postal-code-lookup'],
      primaryProvider: 'geonorge'
    },
    business: {
      providers: ['brreg'],
      features: ['company-lookup', 'batch-lookup', 'search', 'validation', 'status-check', 'sector-classification'],
      primaryProvider: 'brreg'
    }
  },
  
  // Coverage areas
  coverage: {
    country: 'Norway',
    includes: ['mainland', 'svalbard', 'jan-mayen'],
    coordinateSystems: ['WGS84', 'ETRS89', 'UTM']
  },

  // Benefits of this architecture
  benefits: [
    'Independent API modules - use only what you need',
    'Tree-shakeable - smaller bundle sizes',
    'Easy to test - mock individual modules',
    'Future-proof - can extract modules to separate packages',
    'Clear separation of concerns - API vs orchestration',
    'Type-safe - comprehensive TypeScript definitions'
  ]
} as const;

