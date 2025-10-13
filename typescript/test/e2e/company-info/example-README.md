# 🇳🇴 Norwegian Geo-Services Library - Example Usage

This directory contains a comprehensive example program demonstrating how to use the **Norwegian Geo-Services Library** for Norwegian geographical and business registry services.

## 🚀 Quick Start

### Prerequisites

- **Node.js** >= 18.0.0
- **TypeScript** support (tsx or ts-node)

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Run the example:**
   ```bash
   npm start
   ```

### Alternative: Using tsx directly

```bash
npx tsx example-usage.ts
```

## 📋 What This Example Demonstrates

### 1. Address Lookup Service
- **Smart address search** with fallback between Geonorge and Kartverket APIs
- **Coordinate inclusion** for precise location data
- **Result metadata** showing source and performance metrics

```typescript
const addressResult = await NorwegianGeoServices.services.addressLookup.searchAddresses({
  query: 'Karl Johans gate 1, Oslo',
  maxResults: 5,
  includeCoordinates: true
});
```

### 2. Company Lookup Service
- **Enhanced company data** with business intelligence
- **Status analysis** and risk assessment
- **Sector classification** and activity validation

```typescript
const companyResult = await NorwegianGeoServices.services.companyLookup.lookupCompany('937891377');
console.log(`${companyResult.company.navn} - ${companyResult.statusDescription}`);
```

### 3. Direct API Access
- **Low-level API access** for advanced use cases
- **Individual API clients** for specific services
- **Custom configuration** options

```typescript
const directAddresses = await NorwegianGeoServices.apis.geonorge.searchAddresses({
  query: 'Bergen',
  maxResults: 3
});
```

### 4. Batch Operations
- **Multiple company lookups** in a single operation
- **Error handling** and success rate reporting
- **Performance optimization** for bulk operations

```typescript
const batchResults = await NorwegianGeoServices.services.companyLookup.batchLookup(orgNumbers);
```

## 🏗️ Architecture Overview

The example showcases the library's **modular architecture**:

- **📦 API Modules**: Independent clients for each Norwegian service
  - `geonorge` - Official Norwegian Mapping Authority
  - `kartverket` - Alternative mapping services
  - `brreg` - Norwegian Business Registry

- **🎯 Service Layer**: High-level orchestration with smart fallbacks
  - `addressLookup` - Combines multiple address APIs
  - `companyLookup` - Enhanced business data services

- **🔧 Convenience Object**: Single entry point for all functionality
  ```typescript
  import { NorwegianGeoServices } from './norwegian-geo-services';
  ```

## 📊 Sample Output

```
🇳🇴 Norwegian Geo-Services Library Demo
=====================================

📚 Library Info:
   Name: Norwegian Geo-Services Library
   Version: 0.1.1
   Author: Terje Christensen (terchris)

📍 Address Lookup Example
------------------------
Found 15 addresses
Source: geonorge
Top results:
  1. Karl Johans gate 1, 0154 Oslo
     📍 59.9127, 10.7461

🏢 Company Lookup Example
-----------------------
Company: SpareBank 1 Østlandet
Organization Number: 937891377
Status: Active
Active: ✅
Sector: Banking and Finance
Risk Level: LOW

🔧 Direct API Access Example
---------------------------
Direct Geonorge API found 3 addresses:
  1. Vestre Torggate 9, 5015 Bergen
  2. Lars Hilles gate 30, 5008 Bergen
  3. Christies gate 13, 5015 Bergen
```

## 🔧 Development Commands

```bash
# Run the example
npm start

# Run in watch mode (restarts on file changes)
npm run dev

# Type checking only
npx tsc --noEmit example-usage.ts

# Linting
npm run lint

# Format code
npm run format
```

## 📝 Configuration

The example uses **environment variables** for API configuration. Make sure to set:

- `GEONORGE_BASE_URL` - Geonorge API endpoint
- `BRREG_BASE_URL` - BRREG API endpoint
- `KARTVERKET_BASE_URL` - Kartverket API endpoint

Default values are provided for development.

## 🚨 Error Handling

The example includes comprehensive error handling:

- **Network errors** - API connectivity issues
- **Validation errors** - Invalid input parameters
- **Rate limiting** - API quota exceeded
- **Service unavailable** - External service downtime

## 📚 Learn More

- [Main Library README](../norwegian-geo-services/README.md) - Complete documentation
- [Geonorge API Docs](https://ws.geonorge.no/adresser/v1)
- [BRREG API Docs](https://data.brreg.no/enhetsregisteret/api/docs/index.html)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/) - Language reference

---

**Created by:** Terje Christensen (terchris)
**Version:** 0.1.1
**License:** MIT
