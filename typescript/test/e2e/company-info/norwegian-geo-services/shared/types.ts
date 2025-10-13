/**
 * 📋 Norwegian Geo-Services Library - Shared Core Types
 * 
 * Common type definitions shared across all services
 */

// === COMMON API TYPES ===

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  error?: string;
  timestamp: Date;
}

export interface PaginatedResponse<T> extends ApiResponse<T> {
  pagination?: {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

// === API CLIENT CONFIGURATION ===

export interface ApiClientConfig {
  baseUrl: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  userAgent?: string;
  headers?: Record<string, string>;
}

// === LOGGING INTEGRATION ===

export interface LogContext {
  correlationId?: string;
  userId?: string;
  sessionId?: string;
  requestId?: string;
}

// === COMMON ADDRESS TYPES ===

export interface NorwegianAddress {
  addressText: string;
  postalCode: string;
  postTown: string;
  municipality: string;
  municipalityNumber: string;
  county: string;
  countyNumber: string;
  country: string;
  coordinates?: {
    lat: number;
    lon: number;
    coordinateSystem: string;
  };
}

export interface AddressSearchParams {
  query: string;
  municipality?: string;
  county?: string;
  maxResults?: number;
  includeCoordinates?: boolean;
}

export interface AddressValidationResult {
  isValid: boolean;
  normalizedAddress?: NorwegianAddress;
  suggestions?: NorwegianAddress[];
  validationErrors?: string[];
}

