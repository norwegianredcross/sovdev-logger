/* BRREG utility functions
 * Validation and normalization utilities for Norwegian business data
 * 
 * Author: Terje Christensen (terchris)
 * GitHub: https://github.com/terchris
 */

import {
    companyName2displayName
} from "./index.js";

/** validateOrgNumber
 * Validates and cleans a Norwegian organization number
 * @param {string} orgNumber - the organization number to validate
 * @returns {object} - { isValid: boolean, cleanedNumber: string }
 */
export function validateOrgNumber(orgNumber: string): { isValid: boolean; cleanedNumber: string } {
    let cleanedNumber = "";
    let isValid = false;

    if (orgNumber) {
        cleanedNumber = orgNumber.toString(); // make sure we are dealing with a string
        cleanedNumber = cleanedNumber.trim(); // trim spaces at beginning and end
        cleanedNumber = cleanedNumber.replace(/\D/g, ''); // remove non numeric characters

        if (cleanedNumber.length === 9) { // length must be 9 numbers
            isValid = true;
        }
    }

    return {
        isValid,
        cleanedNumber
    };
}

/** normalizeCompanyName
 * Normalizes a company name for comparison by removing suffixes and standardizing format
 * @param {string} companyName - the company name to normalize
 * @returns {string} - normalized company name
 */
export function normalizeCompanyName(companyName: string): string {
    if (!companyName) return "";

    let normalized = companyName.toString(); // ensure string
    normalized = companyName2displayName(normalized); // remove AS, IKS, ASA etc
    normalized = normalized.toUpperCase().trim();

    return normalized;
}

/** prepareSearchTerm
 * Prepares a search term for BRREG API calls
 * @param {string} searchTerm - the search term to prepare
 * @returns {string} - prepared and encoded search term
 */
export function prepareSearchTerm(searchTerm: string): string {
    if (!searchTerm) return "";

    let prepared = searchTerm.toString(); // ensure string
    prepared = prepared.toUpperCase().trim();

    return prepared;
}

/** selectBestMatch
 * Selects the best matching company from an array based on name comparison
 * @param {string} searchName - the original search name
 * @param {Array} companies - array of company objects with 'navn' property
 * @returns {object} - the best matching company or empty object if no exact match
 */
export function selectBestMatch(searchName: string, companies: any[]): any {
    if (!searchName || !companies || companies.length === 0) {
        return {};
    }

    const normalizedSearchName = normalizeCompanyName(searchName);
    const exactMatches: any[] = [];

    // Find exact matches after normalization
    for (let i = 0; i < companies.length; i++) {
        const companyName = companies[i].navn ?? "";
        const normalizedCompanyName = normalizeCompanyName(companyName);

        if (normalizedSearchName === normalizedCompanyName) {
            exactMatches.push(companies[i]);
        }
    }

    // Only return a match if there's exactly one exact match
    if (exactMatches.length === 1) {
        return exactMatches[0];
    } else {
        // Multiple matches or no exact matches - return empty object
        return {};
    }
}

/** isValidDomainName
 * Basic validation for domain names
 * @param {string} domain - the domain name to validate
 * @returns {boolean} - true if the domain appears valid
 */
export function isValidDomainName(domain: string): boolean {
    if (!domain || typeof domain !== 'string') {
        return false;
    }

    // Basic domain validation - contains at least one dot and no spaces
    const trimmed = domain.trim();
    return trimmed.length > 0 && 
           trimmed.includes('.') && 
           !trimmed.includes(' ') &&
           trimmed.length <= 253; // Maximum domain length
}

/** cleanDomainName
 * Cleans and normalizes a domain name
 * @param {string} domain - the domain name to clean
 * @returns {string} - cleaned domain name
 */
export function cleanDomainName(domain: string): string {
    if (!domain) return "";

    let cleaned = domain.toString().trim().toLowerCase();
    
    // Remove protocol if present
    cleaned = cleaned.replace(/^https?:\/\//, '');
    cleaned = cleaned.replace(/^www\./, '');
    
    // Remove trailing slash and path
    cleaned = cleaned.split('/')[0];
    
    return cleaned;
}
