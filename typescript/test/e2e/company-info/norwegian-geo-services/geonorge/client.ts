/**
 * 📍 Geonorge API Client
 * 
 * Client for the official Norwegian Mapping Authority (Kartverket) address API
 * Official API: https://ws.geonorge.no/adresser/v1
 */

import https from 'https';
import { URL } from 'url';
import {
  NorwegianAddress,
  AddressSearchParams,
  AddressValidationResult,
  ApiClientConfig
} from '../shared/types.js';
import { GeonorgeError } from '../shared/errors.js';
import { GeonorgeSearchResponse } from './types.js';

export class GeonorgeApiClient {
  private readonly config: ApiClientConfig;

  constructor(config?: Partial<ApiClientConfig>) {
    this.config = {
      baseUrl: 'https://ws.geonorge.no/adresser/v1',
      timeout: 10000,
      retryAttempts: 3,
      retryDelay: 1000,
      userAgent: 'Norwegian-Geo-Services-Library/1.0.0',
      ...config
    };
  }

  /**
   * Search for Norwegian addresses
   */
  async searchAddresses(params: AddressSearchParams): Promise<NorwegianAddress[]> {
    const url = new URL(`${this.config.baseUrl}/sok`);
    
    // Add search parameters
    url.searchParams.set('sok', params.query);
    if (params.municipality) url.searchParams.set('kommunenummer', params.municipality);
    if (params.county) url.searchParams.set('fylkesnummer', params.county);
    if (params.maxResults) url.searchParams.set('treffPerSide', params.maxResults.toString());
    if (params.includeCoordinates) url.searchParams.set('utkoordsys', '4258'); // ETRS89

    try {
      const response = await this.httpGet<GeonorgeSearchResponse>(url.toString());
      return this.convertToNorwegianAddresses(response.adresser, params.includeCoordinates);
    } catch (error) {
      throw new GeonorgeError(
        'Address search failed',
        'GEONORGE_SEARCH_ERROR',
        error instanceof Error && 'statusCode' in error ? (error as any).statusCode : undefined,
        { searchParams: params },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Get exact address by coordinates (reverse geocoding)
   */
  async getAddressByCoordinates(lat: number, lon: number): Promise<NorwegianAddress | null> {
    const url = new URL(`${this.config.baseUrl}/punkt`);
    url.searchParams.set('lat', lat.toString());
    url.searchParams.set('lon', lon.toString());
    url.searchParams.set('koordsys', '4258'); // ETRS89
    url.searchParams.set('treffPerSide', '1');

    try {
      const response = await this.httpGet<GeonorgeSearchResponse>(url.toString());
      const addresses = this.convertToNorwegianAddresses(response.adresser, true);
      return addresses.length > 0 ? addresses[0] : null;
    } catch (error) {
      throw new GeonorgeError(
        'Reverse geocoding failed',
        'GEONORGE_REVERSE_GEOCODING_ERROR',
        error instanceof Error && 'statusCode' in error ? (error as any).statusCode : undefined,
        { coordinates: { lat, lon } },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Validate and suggest address corrections
   */
  async validateAddress(addressText: string): Promise<AddressValidationResult> {
    try {
      const searchResults = await this.searchAddresses({
        query: addressText,
        maxResults: 5,
        includeCoordinates: true
      });

      if (searchResults.length === 0) {
        return {
          isValid: false,
          suggestions: [],
          validationErrors: ['No matching addresses found']
        };
      }

      // Check for exact match
      const exactMatch = searchResults.find(addr => 
        addr.addressText.toLowerCase() === addressText.toLowerCase()
      );

      if (exactMatch) {
        return {
          isValid: true,
          normalizedAddress: exactMatch,
          suggestions: searchResults.slice(0, 3) // Provide a few alternatives
        };
      }

      // No exact match, provide suggestions
      return {
        isValid: false,
        suggestions: searchResults.slice(0, 5),
        validationErrors: ['Address not found exactly as entered']
      };

    } catch (error) {
      return {
        isValid: false,
        suggestions: [],
        validationErrors: [
          `Validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
        ]
      };
    }
  }

  /**
   * Convert Geonorge response to standardized format
   */
  private convertToNorwegianAddresses(
    geonorgeAddresses: GeonorgeSearchResponse['adresser'],
    includeCoordinates: boolean = false
  ): NorwegianAddress[] {
    return geonorgeAddresses.map(addr => {
      const norwegianAddress: NorwegianAddress = {
        addressText: addr.adressetekst,
        postalCode: addr.postnummer,
        postTown: addr.poststed,
        municipality: addr.kommunenavn,
        municipalityNumber: addr.kommunenummer,
        county: addr.fylkesnavn,
        countyNumber: addr.fylkesnummer,
        country: 'Norge'
      };

      if (includeCoordinates && addr.representasjonspunkt) {
        norwegianAddress.coordinates = {
          lat: addr.representasjonspunkt.lat,
          lon: addr.representasjonspunkt.lon,
          coordinateSystem: addr.representasjonspunkt.epsg
        };
      }

      return norwegianAddress;
    });
  }

  /**
   * HTTP GET implementation with retry logic
   */
  private async httpGet<T>(url: string): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 1; attempt <= this.config.retryAttempts!; attempt++) {
      try {
        return await this.performHttpGet<T>(url);
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // Don't retry on 4xx errors (client errors)
        if ('statusCode' in lastError && typeof (lastError as any).statusCode === 'number' && (lastError as any).statusCode >= 400 && (lastError as any).statusCode < 500) {
          throw lastError;
        }

        // Wait before retrying (exponential backoff)
        if (attempt < this.config.retryAttempts!) {
          await this.delay(this.config.retryDelay! * Math.pow(2, attempt - 1));
        }
      }
    }

    throw lastError || new Error('Max retry attempts reached');
  }

  /**
   * Perform a single HTTP GET request
   */
  private performHttpGet<T>(url: string): Promise<T> {
    return new Promise((resolve, reject) => {
      const request = https.get(url, {
        timeout: this.config.timeout,
        headers: {
          'User-Agent': this.config.userAgent!,
          'Accept': 'application/json',
          ...this.config.headers
        }
      }, (response) => {
        let data = '';
        
        response.on('data', (chunk) => {
          data += chunk;
        });

        response.on('end', () => {
          try {
            if (response.statusCode! >= 200 && response.statusCode! < 300) {
              const parsed = JSON.parse(data);
              resolve(parsed);
            } else {
              const error = new Error(`HTTP ${response.statusCode}: ${data}`) as any;
              error.statusCode = response.statusCode;
              error.responseBody = data;
              reject(error);
            }
          } catch (parseError) {
            const error = new Error(`Failed to parse JSON response: ${parseError}`) as any;
            error.statusCode = response.statusCode;
            error.responseBody = data;
            reject(error);
          }
        });
      });

      request.on('error', (error) => {
        reject(error);
      });

      request.on('timeout', () => {
        request.destroy();
        reject(new Error(`Request timeout after ${this.config.timeout}ms`));
      });
    });
  }

  /**
   * Utility function for delays
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export a default instance for convenience
export const geonorgeApi = new GeonorgeApiClient();

