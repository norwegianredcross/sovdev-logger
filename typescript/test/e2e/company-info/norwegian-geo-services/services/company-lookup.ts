/**
 * 🏢 Company Lookup Service
 * 
 * High-level orchestration service for Norwegian Business Registry
 * Provides enhanced company data with business intelligence
 */

import { LogContext } from '../shared/types.js';
import { BrregError } from '../shared/errors.js';
import { 
  CompanyDetailedInfo, 
  CompanySearchParams,
  CompanySearchResult 
} from '../brreg/types.js';
import { BrregApiClient, brregApi } from '../brreg/client.js';
import {
  OrganizationNumberValidator,
  CompanyDataNormalizer,
  BusinessStatusUtils,
  BusinessSectorUtils
} from '../brreg/utils.js';

export interface CompanyLookupOptions {
  validateInput?: boolean;
  normalizeOutput?: boolean;
  logContext?: LogContext;
}

export interface CompanyLookupResult {
  company: CompanyDetailedInfo;
  isActive: boolean;
  statusDescription: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  sector: string;
  normalizedData: CompanyDetailedInfo;
}

export interface BatchLookupResult {
  successful: Map<string, CompanyLookupResult>;
  failed: Map<string, Error>;
  summary: {
    totalRequested: number;
    successCount: number;
    failureCount: number;
    successRate: number;
  };
}

/**
 * High-level company lookup service
 * Orchestrates BRREG API with validation and business intelligence
 */
export class CompanyLookupService {
  private readonly apiClient: BrregApiClient;

  constructor(apiClient?: BrregApiClient) {
    this.apiClient = apiClient || brregApi;
  }

  /**
   * Lookup a single company with full processing and business intelligence
   */
  async lookupCompany(
    organisasjonsnummer: string,
    options: CompanyLookupOptions = {}
  ): Promise<CompanyLookupResult> {
    const opts = {
      validateInput: true,
      normalizeOutput: true,
      ...options
    };

    try {
      // Validate input if requested
      let normalizedOrgNumber = organisasjonsnummer;
      if (opts.validateInput) {
        normalizedOrgNumber = OrganizationNumberValidator.normalize(organisasjonsnummer);
      }

      // Fetch company data
      const company = await this.apiClient.getCompany(normalizedOrgNumber);

      // Normalize output if requested
      const normalizedData = opts.normalizeOutput ? 
        CompanyDataNormalizer.normalizeDetailedInfo(company) : company;

      // Add business intelligence
      const isActive = BusinessStatusUtils.isActive(company);
      const statusDescription = BusinessStatusUtils.getStatusDescription(company);
      const riskLevel = BusinessStatusUtils.getRiskLevel(company);
      const sector = company.naeringskode1?.kode ? 
        BusinessSectorUtils.getMainSector(company.naeringskode1.kode) : 'Unknown';

      return {
        company,
        isActive,
        statusDescription,
        riskLevel,
        sector,
        normalizedData
      };

    } catch (error) {
      throw new BrregError(
        `Failed to lookup company ${organisasjonsnummer}`,
        'COMPANY_LOOKUP_FAILED',
        error instanceof BrregError ? error.statusCode : undefined,
        { organisasjonsnummer, options: opts },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Search for companies
   */
  async searchCompanies(
    params: CompanySearchParams,
    options: CompanyLookupOptions = {}
  ): Promise<CompanySearchResult> {
    try {
      return await this.apiClient.searchCompanies(params);
    } catch (error) {
      throw new BrregError(
        'Company search failed',
        'COMPANY_SEARCH_FAILED',
        error instanceof BrregError ? error.statusCode : undefined,
        { searchParams: params },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Check if a company exists
   */
  async companyExists(organisasjonsnummer: string): Promise<boolean> {
    try {
      return await this.apiClient.companyExists(organisasjonsnummer);
    } catch (error) {
      throw new BrregError(
        'Company existence check failed',
        'COMPANY_EXISTS_CHECK_FAILED',
        error instanceof BrregError ? error.statusCode : undefined,
        { organisasjonsnummer },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Batch lookup multiple companies
   */
  async batchLookup(
    organisasjonsnummer: string[],
    options: CompanyLookupOptions = {}
  ): Promise<BatchLookupResult> {
    const successful = new Map<string, CompanyLookupResult>();
    const failed = new Map<string, Error>();

    const results = await this.apiClient.getCompaniesBatch(organisasjonsnummer);

    for (const [orgNr, result] of results) {
      if (result instanceof Error) {
        failed.set(orgNr, result);
      } else {
        try {
          const lookupResult = await this.processCompanyData(result, options);
          successful.set(orgNr, lookupResult);
        } catch (error) {
          failed.set(orgNr, error instanceof Error ? error : new Error(String(error)));
        }
      }
    }

    const totalRequested = organisasjonsnummer.length;
    const successCount = successful.size;
    const failureCount = failed.size;
    const successRate = (successCount / totalRequested) * 100;

    return {
      successful,
      failed,
      summary: {
        totalRequested,
        successCount,
        failureCount,
        successRate
      }
    };
  }

  /**
   * Process company data to add business intelligence
   */
  private async processCompanyData(
    company: CompanyDetailedInfo,
    options: CompanyLookupOptions
  ): Promise<CompanyLookupResult> {
    const normalizedData = options.normalizeOutput ? 
      CompanyDataNormalizer.normalizeDetailedInfo(company) : company;

    const isActive = BusinessStatusUtils.isActive(company);
    const statusDescription = BusinessStatusUtils.getStatusDescription(company);
    const riskLevel = BusinessStatusUtils.getRiskLevel(company);
    const sector = company.naeringskode1?.kode ? 
      BusinessSectorUtils.getMainSector(company.naeringskode1.kode) : 'Unknown';

    return {
      company,
      isActive,
      statusDescription,
      riskLevel,
      sector,
      normalizedData
    };
  }
}

// Export a default instance for convenience
export const companyLookup = new CompanyLookupService();

