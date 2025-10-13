/**
 * 🏢 BRREG Utils - Validation & normalization for Norwegian Business Registry
 * 
 * Utilities for validating organization numbers, normalizing company data, etc.
 */

import { BrregError } from '../shared/errors.js';
import {
  CompanyBasicInfo,
  CompanyDetailedInfo,
  BusinessAddress
} from './types.js';

/**
 * Norwegian organization number validation and utilities
 */
export class OrganizationNumberValidator {
  
  /**
   * Validate Norwegian organization number (9 digits with Modulus 11 check)
   */
  static validate(orgNumber: string): boolean {
    // Remove any non-digits
    const cleaned = orgNumber.replace(/\D/g, '');
    
    // Must be exactly 9 digits
    if (cleaned.length !== 9) {
      return false;
    }

    // Convert to array of numbers
    const digits = cleaned.split('').map(Number);
    
    // Modulus 11 validation
    const weights = [3, 2, 7, 6, 5, 4, 3, 2];
    const sum = digits.slice(0, 8).reduce((acc, digit, index) => {
      return acc + (digit * weights[index]);
    }, 0);

    const remainder = sum % 11;
    const checkDigit = remainder === 0 ? 0 : 11 - remainder;
    
    // If checkDigit is 10, the number is invalid
    if (checkDigit === 10) {
      return false;
    }

    return checkDigit === digits[8];
  }

  /**
   * Normalize organization number to standard format (9 digits)
   */
  static normalize(orgNumber: string): string {
    const cleaned = orgNumber.replace(/\D/g, '');
    
    if (!this.validate(orgNumber)) {
      throw new BrregError(
        `Invalid organization number: ${orgNumber}`,
        'INVALID_ORG_NUMBER',
        400,
        { originalInput: orgNumber, cleaned }
      );
    }

    return cleaned;
  }

  /**
   * Format organization number for display (XXX XXX XXX)
   */
  static format(orgNumber: string): string {
    const normalized = this.normalize(orgNumber);
    return `${normalized.slice(0, 3)} ${normalized.slice(3, 6)} ${normalized.slice(6, 9)}`;
  }

  /**
   * Generate check digit for the first 8 digits
   */
  static generateCheckDigit(firstEightDigits: string): number {
    if (firstEightDigits.length !== 8 || !/^\d{8}$/.test(firstEightDigits)) {
      throw new Error('Must provide exactly 8 digits');
    }

    const digits = firstEightDigits.split('').map(Number);
    const weights = [3, 2, 7, 6, 5, 4, 3, 2];
    
    const sum = digits.reduce((acc, digit, index) => {
      return acc + (digit * weights[index]);
    }, 0);

    const remainder = sum % 11;
    const checkDigit = remainder === 0 ? 0 : 11 - remainder;
    
    if (checkDigit === 10) {
      throw new Error('Invalid number sequence - check digit would be 10');
    }

    return checkDigit;
  }
}

/**
 * Company data normalization utilities
 */
export class CompanyDataNormalizer {

  /**
   * Normalize company basic info
   */
  static normalizeBasicInfo(company: CompanyBasicInfo): CompanyBasicInfo {
    return {
      ...company,
      organisasjonsnummer: OrganizationNumberValidator.normalize(company.organisasjonsnummer),
      navn: this.normalizeCompanyName(company.navn),
      forretningsadresse: company.forretningsadresse ? 
        this.normalizeAddress(company.forretningsadresse) : undefined,
      postadresse: company.postadresse ? 
        this.normalizeAddress(company.postadresse) : undefined
    };
  }

  /**
   * Normalize company detailed info
   */
  static normalizeDetailedInfo(company: CompanyDetailedInfo): CompanyDetailedInfo {
    const basicNormalized = this.normalizeBasicInfo(company);
    
    return {
      ...basicNormalized,
      hjemmeside: company.hjemmeside ? this.normalizeWebsite(company.hjemmeside) : undefined,
      telefon: company.telefon ? this.normalizePhoneNumber(company.telefon) : undefined,
      epost: company.epost ? this.normalizeEmail(company.epost) : undefined
    };
  }

  /**
   * Normalize company name
   */
  private static normalizeCompanyName(name: string): string {
    return name.trim()
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .replace(/\.$/, ''); // Remove trailing period if present
  }

  /**
   * Normalize business address
   */
  private static normalizeAddress(address: BusinessAddress): BusinessAddress {
    if (!address) return address;

    return {
      ...address,
      postnummer: address.postnummer?.replace(/\D/g, ''), // Keep only digits in postal code
      poststed: address.poststed?.trim().toUpperCase(),
      kommune: address.kommune?.trim(),
      land: address.land?.trim()
    };
  }

  /**
   * Normalize website URL
   */
  private static normalizeWebsite(website: string): string {
    let normalized = website.trim().toLowerCase();
    
    // Add protocol if missing
    if (!normalized.startsWith('http://') && !normalized.startsWith('https://')) {
      normalized = 'https://' + normalized;
    }

    try {
      const url = new URL(normalized);
      return url.toString();
    } catch {
      // If URL is invalid, return original
      return website;
    }
  }

  /**
   * Normalize Norwegian phone number
   */
  private static normalizePhoneNumber(phone: string): string {
    // Remove all non-digits
    const digits = phone.replace(/\D/g, '');
    
    // Norwegian phone numbers
    if (digits.length === 8) {
      // Standard Norwegian mobile/landline
      return `+47 ${digits.slice(0, 2)} ${digits.slice(2, 5)} ${digits.slice(5, 8)}`;
    } else if (digits.length === 10 && digits.startsWith('47')) {
      // Already has country code
      return `+47 ${digits.slice(2, 4)} ${digits.slice(4, 7)} ${digits.slice(7, 10)}`;
    }
    
    // Return original if format is unclear
    return phone;
  }

  /**
   * Normalize email address
   */
  private static normalizeEmail(email: string): string {
    return email.trim().toLowerCase();
  }
}

/**
 * Business status utilities
 */
export class BusinessStatusUtils {

  /**
   * Check if company is active and operational
   */
  static isActive(company: CompanyDetailedInfo): boolean {
    return !company.konkurs && 
           !company.underAvvikling && 
           !company.underTvangsavviklingEllerTvangsopplosning;
  }

  /**
   * Get human-readable status
   */
  static getStatusDescription(company: CompanyDetailedInfo): string {
    if (company.konkurs) return 'Konkurs (Bankruptcy)';
    if (company.underAvvikling) return 'Under avvikling (Being dissolved)';
    if (company.underTvangsavviklingEllerTvangsopplosning) return 'Under tvangsavvikling (Forced dissolution)';
    return 'Aktiv (Active)';
  }

  /**
   * Get business risk level based on status
   */
  static getRiskLevel(company: CompanyDetailedInfo): 'LOW' | 'MEDIUM' | 'HIGH' {
    if (company.konkurs || company.underTvangsavviklingEllerTvangsopplosning) {
      return 'HIGH';
    }
    if (company.underAvvikling) {
      return 'MEDIUM';
    }
    return 'LOW';
  }
}

/**
 * Business sector classification utilities
 */
export class BusinessSectorUtils {

  /**
   * Get main sector from NACE code
   */
  static getMainSector(naceCode: string): string {
    const code = naceCode.split('.')[0]; // Take only the main code before decimal
    const sectorMap: Record<string, string> = {
      '01': 'Agriculture, Forestry and Fishing',
      '02': 'Agriculture, Forestry and Fishing',
      '03': 'Agriculture, Forestry and Fishing',
      '05': 'Mining and Quarrying',
      '06': 'Mining and Quarrying',
      '07': 'Mining and Quarrying',
      '08': 'Mining and Quarrying',
      '09': 'Mining and Quarrying',
      '10': 'Manufacturing',
      '11': 'Manufacturing',
      '12': 'Manufacturing',
      '13': 'Manufacturing',
      '14': 'Manufacturing',
      '15': 'Manufacturing',
      '16': 'Manufacturing',
      '17': 'Manufacturing',
      '18': 'Manufacturing',
      '19': 'Manufacturing',
      '20': 'Manufacturing',
      '21': 'Manufacturing',
      '22': 'Manufacturing',
      '23': 'Manufacturing',
      '24': 'Manufacturing',
      '25': 'Manufacturing',
      '26': 'Manufacturing',
      '27': 'Manufacturing',
      '28': 'Manufacturing',
      '29': 'Manufacturing',
      '30': 'Manufacturing',
      '31': 'Manufacturing',
      '32': 'Manufacturing',
      '33': 'Manufacturing',
      '35': 'Electricity, Gas, Steam and Air Conditioning Supply',
      '36': 'Water Supply; Sewerage, Waste Management',
      '37': 'Water Supply; Sewerage, Waste Management',
      '38': 'Water Supply; Sewerage, Waste Management',
      '39': 'Water Supply; Sewerage, Waste Management',
      '41': 'Construction',
      '42': 'Construction',
      '43': 'Construction',
      '45': 'Wholesale and Retail Trade',
      '46': 'Wholesale and Retail Trade',
      '47': 'Wholesale and Retail Trade',
      '49': 'Transportation and Storage',
      '50': 'Transportation and Storage',
      '51': 'Transportation and Storage',
      '52': 'Transportation and Storage',
      '53': 'Transportation and Storage',
      '55': 'Accommodation and Food Service Activities',
      '56': 'Accommodation and Food Service Activities',
      '58': 'Information and Communication',
      '59': 'Information and Communication',
      '60': 'Information and Communication',
      '61': 'Information and Communication',
      '62': 'Information and Communication',
      '63': 'Information and Communication',
      '64': 'Financial and Insurance Activities',
      '65': 'Financial and Insurance Activities',
      '66': 'Financial and Insurance Activities',
      '68': 'Real Estate Activities',
      '69': 'Professional, Scientific and Technical Activities',
      '70': 'Professional, Scientific and Technical Activities',
      '71': 'Professional, Scientific and Technical Activities',
      '72': 'Professional, Scientific and Technical Activities',
      '73': 'Professional, Scientific and Technical Activities',
      '74': 'Professional, Scientific and Technical Activities',
      '75': 'Professional, Scientific and Technical Activities',
      '77': 'Administrative and Support Service Activities',
      '78': 'Administrative and Support Service Activities',
      '79': 'Administrative and Support Service Activities',
      '80': 'Administrative and Support Service Activities',
      '81': 'Administrative and Support Service Activities',
      '82': 'Administrative and Support Service Activities',
      '84': 'Public Administration and Defence',
      '85': 'Education',
      '86': 'Human Health and Social Work Activities',
      '87': 'Human Health and Social Work Activities',
      '88': 'Human Health and Social Work Activities',
      '90': 'Arts, Entertainment and Recreation',
      '91': 'Arts, Entertainment and Recreation',
      '92': 'Arts, Entertainment and Recreation',
      '93': 'Arts, Entertainment and Recreation',
      '94': 'Other Service Activities',
      '95': 'Other Service Activities',
      '96': 'Other Service Activities',
      '97': 'Other Service Activities',
      '98': 'Other Service Activities',
      '99': 'Other Service Activities'
    };

    return sectorMap[code] || 'Unknown Sector';
  }

  /**
   * Check if company is in specific sectors
   */
  static isInSector(company: CompanyDetailedInfo, sectors: string[]): boolean {
    if (!company.naeringskode1?.kode) return false;
    
    const companySector = this.getMainSector(company.naeringskode1.kode);
    return sectors.includes(companySector);
  }
}

