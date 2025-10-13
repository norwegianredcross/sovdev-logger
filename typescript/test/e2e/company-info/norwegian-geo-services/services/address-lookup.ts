/**
 * 📍 Address Lookup Service
 * 
 * High-level orchestration service combining Geonorge and Kartverket APIs
 * Provides smart fallback and result combination strategies
 */

import { NorwegianAddress, AddressSearchParams, LogContext } from '../shared/types.js';
import { NorwegianGeoServiceError } from '../shared/errors.js';
import { GeonorgeApiClient, geonorgeApi } from '../geonorge/index.js';
import { KartverketApiClient, kartverketApi } from '../kartverket/index.js';

export interface AddressLookupOptions {
  validateInput?: boolean;
  normalizeOutput?: boolean;
  includeCoordinates?: boolean;
  preferredProvider?: 'geonorge' | 'kartverket' | 'auto';
  logContext?: LogContext;
}

export interface AddressLookupResult {
  addresses: NorwegianAddress[];
  source: 'geonorge' | 'kartverket' | 'combined';
  metadata: {
    totalFound: number;
    searchQuery: string;
    processingTimeMs: number;
  };
}

/**
 * High-level address lookup service
 * Orchestrates multiple address APIs for best results
 */
export class AddressLookupService {
  private readonly geonorgeClient: GeonorgeApiClient;
  private readonly kartverketClient: KartverketApiClient;

  constructor(
    geonorgeClient?: GeonorgeApiClient,
    kartverketClient?: KartverketApiClient
  ) {
    this.geonorgeClient = geonorgeClient || geonorgeApi;
    this.kartverketClient = kartverketClient || kartverketApi;
  }

  /**
   * Search for addresses using the best available provider
   */
  async searchAddresses(
    params: AddressSearchParams,
    options: AddressLookupOptions = {}
  ): Promise<AddressLookupResult> {
    const startTime = Date.now();
    const opts = {
      preferredProvider: 'auto' as const,
      includeCoordinates: false,
      ...options
    };

    try {
      let addresses: NorwegianAddress[];
      let source: 'geonorge' | 'kartverket' | 'combined';

      // Choose provider based on preference
      if (opts.preferredProvider === 'geonorge') {
        addresses = await this.geonorgeClient.searchAddresses({
          ...params,
          includeCoordinates: opts.includeCoordinates
        });
        source = 'geonorge';
      } else if (opts.preferredProvider === 'kartverket') {
        addresses = await this.kartverketClient.searchAddresses({
          ...params,
          includeCoordinates: opts.includeCoordinates
        });
        source = 'kartverket';
      } else {
        // Auto mode - try Geonorge first (official API), fallback to Kartverket
        try {
          addresses = await this.geonorgeClient.searchAddresses({
            ...params,
            includeCoordinates: opts.includeCoordinates
          });
          source = 'geonorge';
        } catch (error) {
          console.warn('Geonorge search failed, trying Kartverket:', error);
          addresses = await this.kartverketClient.searchAddresses({
            ...params,
            includeCoordinates: opts.includeCoordinates
          });
          source = 'kartverket';
        }
      }

      return {
        addresses,
        source,
        metadata: {
          totalFound: addresses.length,
          searchQuery: params.query,
          processingTimeMs: Date.now() - startTime
        }
      };

    } catch (error) {
      throw new NorwegianGeoServiceError(
        'Address search failed',
        'ADDRESS_SEARCH_FAILED',
        error instanceof NorwegianGeoServiceError ? error.statusCode : undefined,
        { searchParams: params, options: opts },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Get address by coordinates (reverse geocoding)
   * Uses Geonorge as primary source
   */
  async getAddressByCoordinates(lat: number, lon: number): Promise<NorwegianAddress | null> {
    try {
      return await this.geonorgeClient.getAddressByCoordinates(lat, lon);
    } catch (error) {
      throw new NorwegianGeoServiceError(
        'Reverse geocoding failed',
        'REVERSE_GEOCODING_FAILED',
        error instanceof NorwegianGeoServiceError ? error.statusCode : undefined,
        { coordinates: { lat, lon } },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Validate an address
   * Uses Geonorge for validation
   */
  async validateAddress(addressText: string) {
    try {
      return await this.geonorgeClient.validateAddress(addressText);
    } catch (error) {
      throw new NorwegianGeoServiceError(
        'Address validation failed',
        'VALIDATION_FAILED',
        error instanceof NorwegianGeoServiceError ? error.statusCode : undefined,
        { addressText },
        error instanceof Error ? error : undefined
      );
    }
  }
}

// Export a default instance for convenience
export const addressLookup = new AddressLookupService();

