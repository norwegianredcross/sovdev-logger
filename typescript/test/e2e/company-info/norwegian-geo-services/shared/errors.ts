/**
 * 🚨 Norwegian Geo-Services Library - Error Handling
 * 
 * Custom error classes for better error handling across all services
 */

export interface ServiceError extends Error {
  code: string;
  statusCode?: number;
  details?: Record<string, any>;
  originalError?: Error;
}

export class NorwegianGeoServiceError extends Error implements ServiceError {
  public code: string;
  public statusCode?: number;
  public details?: Record<string, any>;
  public originalError?: Error;

  constructor(
    message: string,
    code: string,
    statusCode?: number,
    details?: Record<string, any>,
    originalError?: Error
  ) {
    super(message);
    this.name = 'NorwegianGeoServiceError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    this.originalError = originalError;
  }
}

// Specific error classes for each service

export class GeonorgeError extends NorwegianGeoServiceError {
  constructor(
    message: string,
    code: string,
    statusCode?: number,
    details?: Record<string, any>,
    originalError?: Error
  ) {
    super(message, code, statusCode, details, originalError);
    this.name = 'GeonorgeError';
  }
}

export class KartverketError extends NorwegianGeoServiceError {
  constructor(
    message: string,
    code: string,
    statusCode?: number,
    details?: Record<string, any>,
    originalError?: Error
  ) {
    super(message, code, statusCode, details, originalError);
    this.name = 'KartverketError';
  }
}

export class BrregError extends NorwegianGeoServiceError {
  constructor(
    message: string,
    code: string,
    statusCode?: number,
    details?: Record<string, any>,
    originalError?: Error
  ) {
    super(message, code, statusCode, details, originalError);
    this.name = 'BrregError';
  }
}

