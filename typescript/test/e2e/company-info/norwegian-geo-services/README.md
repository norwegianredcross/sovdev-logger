# Norwegian Geo-Services Library

A comprehensive TypeScript library for Norwegian geographical and business registry services.

## 📁 Architecture

This library follows a **modular, API-first architecture** with clear separation of concerns:

```
norwegian-geo-services/
├── geonorge/           # Official Norwegian Mapping Authority address API
│   ├── client.ts       # API client implementation
│   ├── types.ts        # Geonorge-specific types
│   └── index.ts        # Module exports
│
├── kartverket/         # Additional mapping services
│   ├── client.ts       # API client implementation
│   ├── types.ts        # Kartverket-specific types
│   └── index.ts        # Module exports
│
├── brreg/              # Norwegian Business Registry
│   ├── client.ts       # API client implementation
│   ├── types.ts        # BRREG-specific types
│   ├── utils.ts        # Validators, normalizers, utilities
│   └── index.ts        # Module exports
│
├── services/           # High-level orchestration layer
│   ├── address-lookup.ts   # Combines Geonorge + Kartverket
│   ├── company-lookup.ts   # Enhanced BRREG access
│   └── index.ts            # Service exports
│
├── shared/             # Shared utilities
│   ├── types.ts        # Common types (NorwegianAddress, etc.)
│   ├── errors.ts       # Error classes
│   └── index.ts        # Shared exports
│
└── index.ts            # Main library entry point
```

## 🎯 Design Principles

### 1. **Modularity**
Each API service is a standalone module that can be used independently:
- Import only what you need
- Tree-shakeable for smaller bundles
- Easy to test and mock

### 2. **Separation of Concerns**
- **API Clients** (`/geonorge`, `/kartverket`, `/brreg`): Pure API interactions
- **Services** (`/services`): Business logic and orchestration
- **Shared** (`/shared`): Common utilities and types

### 3. **Independent Services**
Each API folder represents a separate external service:
- **Geonorge**: Official Norwegian address API
- **Kartverket**: Alternative mapping services
- **BRREG**: Business registry lookup

This allows:
- Using each API independently
- Future extraction into separate npm packages
- Clear dependencies (services depend on APIs, not vice versa)

## 📖 Usage Examples

### Simple Usage (Recommended)

```typescript
import { addressLookup, companyLookup } from './norwegian-geo-services/services';

// Address lookup with smart fallback
const result = await addressLookup.searchAddresses({
  query: 'Karl Johans gate 1, Oslo'
});

// Company lookup with business intelligence
const company = await companyLookup.lookupCompany('971277882');
console.log(`${company.company.navn} - ${company.statusDescription}`);
```

### Direct API Access (Advanced)

```typescript
import { geonorgeApi } from './norwegian-geo-services/geonorge';
import { brregApi } from './norwegian-geo-services/brreg';

// Direct Geonorge API access
const addresses = await geonorgeApi.searchAddresses({
  query: 'Oslo',
  maxResults: 10,
  includeCoordinates: true
});

// Direct BRREG API access
const company = await brregApi.getCompany('971277882');
```

### Using the Convenience Object

```typescript
import { NorwegianGeoServices } from './norwegian-geo-services';

// Access everything through one object
const addresses = await NorwegianGeoServices.services.addressLookup.searchAddresses({
  query: 'Oslo'
});

const company = await NorwegianGeoServices.services.companyLookup.lookupCompany('971277882');

// Or use API clients directly
const geonorgeResults = await NorwegianGeoServices.apis.geonorge.searchAddresses({
  query: 'Oslo'
});
```

## 🔧 Benefits of This Architecture

1. **Independent API Modules**
   - Use only what you need
   - Clear boundaries between external services
   - Can be extracted to separate packages

2. **Type-Safe**
   - Comprehensive TypeScript definitions
   - Module-specific types
   - Shared common types

3. **Testable**
   - Mock individual modules
   - Test services independently
   - Clear dependency injection

4. **Scalable**
   - Add new API modules easily
   - Extend services without touching API clients
   - Shared utilities for common patterns

5. **Tree-Shakeable**
   - Import only what you use
   - Smaller bundle sizes
   - Better performance

6. **Future-Proof**
   - Can extract modules to separate npm packages
   - Easy to version independently
   - Clear upgrade paths

## 🆚 Why Not Group by Business Domain?

**Alternative Approach (NOT used):**
```
address/           # Business domain
  ├── geonorge-client.ts
  └── kartverket-client.ts
```

**Why API-based modules are better:**

1. **Clear Service Boundaries**: Geonorge and Kartverket are separate external services with different endpoints, SLAs, and lifecycles
2. **Independent Evolution**: Each API can be updated/versioned independently
3. **Flexible Composition**: Services layer can combine APIs in different ways without coupling
4. **Package Extraction**: Easy to extract `@norwegian-geo/geonorge` as a standalone package
5. **Reusability**: Other projects might only need BRREG, not address lookup

## 📝 Migration Notes

This is version 2.0.0 of the library, refactored from a business-domain structure to an API-based structure for better modularity and maintainability.

### Breaking Changes from 1.x
- Import paths have changed
- Some APIs consolidated into services layer
- Removed lodash and axios dependencies (using native Node.js)

## 🚀 Future Enhancements

Potential additions:
- Rate limiting per API
- Persistent caching layer
- Retry strategies per service
- API health monitoring
- Package extraction for individual modules

## 📚 Related Documentation

- [Geonorge API Docs](https://ws.geonorge.no/adresser/v1)
- [BRREG API Docs](https://data.brreg.no/enhetsregisteret/api/docs/index.html)
- [Kartverket Services](https://www.kartverket.no/)

