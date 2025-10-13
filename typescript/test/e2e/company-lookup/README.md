# 📦 Norwegian Geo-Services Library

A comprehensive TypeScript library for Norwegian geographical and business registry services, designed for the Norwegian Red Cross and other organizations working with Norwegian data.

## 🏗️ Architecture Overview

The library is split into two main modules with a clean, layered architecture:

```
📦 Norwegian Geo-Services Library
├── 📋 types.ts              - Shared type definitions
├── 📍 Address Lookup Library:
│   ├── geonorge.ts          - Official Geonorge API client
│   ├── kartverket.ts        - Unofficial Kartverket API client (placeholder)
│   ├── address-utils.ts     - Address parsing & validation utilities  
│   └── address-lookup.ts    - Orchestration layer
└── 🏢 BRREG Business Registry Library:
    ├── brreg-api.ts         - Pure BRREG API calls
    ├── brreg-utils.ts       - Validation & normalization
    └── brreg-lookup.ts      - Orchestration layer
```

## 🚀 Quick Start

### Basic Company Lookup

```typescript
import { NorwegianGeoServices } from './norwegian-geo-services';

// Simple company lookup
const result = await NorwegianGeoServices.brregLookup.lookupCompany('971277882');
console.log(`${result.company.navn} - ${result.statusDescription}`);

// Batch lookup with analytics
const batchResult = await NorwegianGeoServices.brregLookup.batchLookup([
  '971277882', // Norwegian Red Cross
  '915933149', // Red Cross Emergency Response
  '916201478'  // Norwegian People's Aid
]);

console.log(`Success rate: ${batchResult.summary.successRate}%`);
```

### Address Lookup

```typescript
// Search for addresses
const addresses = await NorwegianGeoServices.addressLookup.searchAddresses({
  query: 'Drammensveien 1, Oslo',
  includeCoordinates: true,
  maxResults: 5
});

// Validate an address
const validation = await NorwegianGeoServices.addressLookup.validateAddress(
  'Drammensveien 1, 0255 Oslo'
);

// Reverse geocoding
const address = await NorwegianGeoServices.addressLookup.getAddressFromCoordinates(
  59.9139, 10.7522
);
```

## 🔧 Advanced Features

### Validation Utilities

```typescript
import { OrganizationNumberValidator, PostalCodeValidator } from './norwegian-geo-services';

// Organization number validation
const isValid = OrganizationNumberValidator.validate('971277882');
const formatted = OrganizationNumberValidator.format('971277882'); // "971 277 882"

// Postal code validation
const isValidPostal = PostalCodeValidator.validate('0255');
const postTown = PostalCodeValidator.getPostTown('0255'); // "Oslo"
```

### Business Intelligence

```typescript
const companyResult = await NorwegianGeoServices.brregLookup.lookupCompany('971277882');

console.log('Business Analysis:');
console.log(`- Active: ${companyResult.isActive}`);
console.log(`- Risk Level: ${companyResult.riskLevel}`);
console.log(`- Sector: ${companyResult.sector}`);
console.log(`- Status: ${companyResult.statusDescription}`);
```

### Caching & Performance

```typescript
// Lookup with caching options
const result = await NorwegianGeoServices.brregLookup.lookupCompany('971277882', {
  useCache: true,
  cacheExpiredSeconds: 3600,
  validateInput: true,
  normalizeOutput: true
});

// Check cache statistics
const stats = NorwegianGeoServices.brregLookup.getCacheStats();
console.log(`Cached entries: ${stats.size}`);
```

## 📊 Current Implementation

The current implementation (`company-lookup.ts`) uses a straightforward approach:

```typescript
// Direct API calls with manual error handling
const companyData = await fetchCompanyData(orgNumber);
const response = {
  navn: companyData.navn,
  organisasjonsform: companyData.organisasjonsform?.beskrivelse
};
```

This simple approach is ideal for testing and validating the sovdev-logger implementation. For production applications, consider the architectural patterns described below for more robust error handling, caching, and business intelligence features.

## 🏢 BRREG Business Registry Features

- ✅ **Company Lookup**: Get detailed company information
- ✅ **Batch Processing**: Process multiple companies efficiently  
- ✅ **Search**: Find companies by name, location, sector
- ✅ **Validation**: Validate organization numbers (Modulus 11)
- ✅ **Business Intelligence**: Active status, risk assessment, sector classification
- ✅ **Caching**: In-memory caching with TTL
- ✅ **Retry Logic**: Robust error handling with exponential backoff
- ✅ **Rate Limiting**: API-friendly request throttling

## 📍 Address Lookup Features

- ✅ **Address Search**: Find Norwegian addresses via Geonorge
- ✅ **Address Validation**: Validate and normalize addresses
- ✅ **Reverse Geocoding**: Get addresses from coordinates
- ✅ **Postal Code Lookup**: Comprehensive postal code utilities
- ✅ **Geographic Utilities**: Distance calculation, coordinate validation
- 🚧 **Kartverket Integration**: Placeholder for unofficial APIs

## 🔒 Error Handling

The library includes comprehensive error handling with specific error types:

```typescript
import { NorwegianGeoServiceError } from './norwegian-geo-services';

try {
  await NorwegianGeoServices.brregLookup.lookupCompany('invalid-number');
} catch (error) {
  if (error instanceof NorwegianGeoServiceError) {
    console.log(`Error: ${error.message}`);
    console.log(`Code: ${error.code}`);
    console.log(`Status: ${error.statusCode}`);
    console.log(`Details:`, error.details);
  }
}
```

## 🧪 Testing with Real Data

The library is tested with real Norwegian organizations:

- **971277882**: Norges Røde Kors (Norwegian Red Cross)
- **915933149**: Røde Kors Hjelpekorps (Red Cross Emergency Response)
- **916201478**: Norsk Folkehjelp (Norwegian People's Aid)
- **974652846**: Invalid test number for error handling

## 📈 Performance Considerations

- **Caching**: Automatic in-memory caching reduces API calls
- **Batch Processing**: Efficient concurrent processing with rate limiting
- **Validation**: Client-side validation prevents unnecessary API calls
- **Retry Logic**: Exponential backoff for reliable operation
- **Connection Pooling**: Reuses HTTPS connections for better performance

## 🔧 Configuration

### API Client Configuration

```typescript
import { BrregApiClient } from './norwegian-geo-services/brreg/brreg-api';

const customClient = new BrregApiClient({
  timeout: 15000,
  retryAttempts: 5,
  retryDelay: 2000,
  userAgent: 'MyApp/1.0.0'
});
```

### Logging Integration

The library integrates seamlessly with the sovdev-logger for structured logging:

```typescript
const result = await NorwegianGeoServices.brregLookup.lookupCompany('971277882', {
  logContext: {
    correlationId: 'user-session-123',
    userId: 'user-456',
    requestId: 'req-789'
  }
});
```

## 🚀 Future Enhancements

1. **Enhanced Kartverket Integration**: Implement actual unofficial Kartverket APIs
2. **Address Autocomplete**: Real-time address suggestions
3. **Geographic Analysis**: Advanced spatial operations
4. **Data Export**: Export functionality for batch results
5. **Web Components**: Ready-to-use UI components
6. **GraphQL API**: Modern API interface layer

## 📝 License

MIT License - Norwegian Red Cross

## 🤝 Contributing

This library is designed to be modular and extensible. Each service follows the same pattern:
1. **API Layer**: Pure API interactions
2. **Utils Layer**: Validation and normalization
3. **Orchestration Layer**: Business logic and caching

When adding new services, follow this established pattern for consistency.
