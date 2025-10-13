/**
 * 📍 Kartverket API - Type Definitions
 * 
 * Kartverket-specific types and interfaces
 * Note: This is based on unofficial Kartverket API endpoints
 */

export interface KartverketSearchResponse {
  features: {
    geometry: {
      coordinates: [number, number];
    };
    properties: {
      address: string;
      postal_code: string;
      city: string;
      municipality: string;
      county: string;
    };
  }[];
}

export interface KartverketPropertyInfo {
  propertyId: string;
  municipality: string;
  cadastralNumber: {
    gnr: number;
    bnr: number;
    fnr?: number;
    snr?: number;
  };
  address?: string;
  area?: number;
}

export interface KartverketElevation {
  lat: number;
  lon: number;
  elevation: number;
  coordinateSystem: string;
}

export interface KartverketTopographicInfo {
  lat: number;
  lon: number;
  elevation?: number;
  terrain?: string;
  landCover?: string;
}

