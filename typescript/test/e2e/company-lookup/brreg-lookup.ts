/* BRREG lookup orchestration functions
 * High-level functions that coordinate between API calls and utilities with intelligent fallback strategies
 * 
 * Author: Terje Christensen (terchris)
 * GitHub: https://github.com/terchris
 */

// Import types
import {
    BrregAPIResponse,
    BrregAPIEnhet,
} from "./index.js";

// Import API functions
import {
    getBrregOrgByOrganisasjonsnummer,
    searchBrregByName,
    searchBrregByWebsite,
    getBrregFullResponseByName
} from "./brreg-api.js";

// Import utility functions
import {
    validateOrgNumber,
    normalizeCompanyName,
    prepareSearchTerm,
    selectBestMatch,
    isValidDomainName,
    cleanDomainName
} from "./brreg-utils.js";

/** findCompanyByOrgNumber
 * Find a company by organization number with validation
 * @param {string} orgNumber - the organization number to lookup
 * @returns {BrregAPIEnhet} - the company record or empty object if not found/invalid
 */
export async function findCompanyByOrgNumber(orgNumber: string): Promise<BrregAPIEnhet> {
    const validation = validateOrgNumber(orgNumber);
    
    if (!validation.isValid) {
        return {}; // Invalid organization number
    }

    return await getBrregOrgByOrganisasjonsnummer(validation.cleanedNumber);
}

/** findCompanyByName
 * Intelligent single company lookup by name
 * Uses smart matching to return exactly one company if there's an exact match after normalization
 * @param {string} companyName - the name of the company to search for
 * @returns {BrregAPIEnhet} - the best matching company or empty object if no exact match
 */
export async function findCompanyByName(companyName: string): Promise<BrregAPIEnhet> {
    if (!companyName) {
        return {};
    }

    const preparedSearchTerm = prepareSearchTerm(companyName);
    const companiesArray = await searchBrregByName(preparedSearchTerm);

    if (companiesArray.length === 0) {
        return {}; // No companies found
    }

    // Use smart selection to find the best match
    return selectBestMatch(companyName, companiesArray);
}

/** searchCompaniesByName
 * Search for multiple companies by name with preprocessing
 * @param {string} companyName - the name of the company to search for
 * @returns {BrregAPIEnhet[]} - array of companies that match the name - if none found returns an empty array
 */
export async function searchCompaniesByName(companyName: string): Promise<BrregAPIEnhet[]> {
    if (!companyName) {
        return [];
    }

    const preparedSearchTerm = prepareSearchTerm(companyName);
    return await searchBrregByName(preparedSearchTerm);
}

/** findCompanyByWebsite
 * Find companies by website/domain name with domain validation and cleaning
 * @param {string} website - the website/domain to search for
 * @returns {BrregAPIResponse} - the full BRREG response object or empty object if not found/invalid
 */
export async function findCompanyByWebsite(website: string): Promise<BrregAPIResponse> {
    if (!website) {
        return {};
    }

    const cleanedDomain = cleanDomainName(website);
    
    if (!isValidDomainName(cleanedDomain)) {
        return {}; // Invalid domain name
    }

    return await searchBrregByWebsite(cleanedDomain);
}

/** getCompanyFullResponseByName
 * Get the complete BRREG API response for a company name search
 * @param {string} companyName - the name of the company to search for
 * @returns {BrregAPIResponse} - the complete BRREG response object or empty object if not found
 */
export async function getCompanyFullResponseByName(companyName: string): Promise<BrregAPIResponse> {
    if (!companyName) {
        return {};
    }

    const preparedSearchTerm = prepareSearchTerm(companyName);
    return await getBrregFullResponseByName(preparedSearchTerm);
}

/** findCompaniesMultipleStrategies
 * Advanced lookup using multiple strategies in order of preference
 * Tries organization number first, then exact name match, then fuzzy search
 * @param {string} searchTerm - the search term (could be org number, company name, etc.)
 * @returns {object} - { strategy: string, result: BrregAPIEnhet, allMatches?: BrregAPIEnhet[] }
 */
export async function findCompaniesMultipleStrategies(searchTerm: string): Promise<{
    strategy: string;
    result: BrregAPIEnhet;
    allMatches?: BrregAPIEnhet[];
}> {
    
    if (!searchTerm) {
        return {
            strategy: "none",
            result: {}
        };
    }

    // Strategy 1: Try as organization number
    const orgValidation = validateOrgNumber(searchTerm);
    if (orgValidation.isValid) {
        const orgResult = await getBrregOrgByOrganisasjonsnummer(orgValidation.cleanedNumber);
        if (Object.keys(orgResult).length > 0) {
            return {
                strategy: "organization_number",
                result: orgResult
            };
        }
    }

    // Strategy 2: Try exact name match
    const exactMatch = await findCompanyByName(searchTerm);
    if (Object.keys(exactMatch).length > 0) {
        return {
            strategy: "exact_name_match",
            result: exactMatch
        };
    }

    // Strategy 3: Fuzzy search - return all matches
    const allMatches = await searchCompaniesByName(searchTerm);
    if (allMatches.length > 0) {
        return {
            strategy: "fuzzy_search",
            result: allMatches[0], // Return first match as primary result
            allMatches: allMatches
        };
    }

    // No matches found
    return {
        strategy: "no_match",
        result: {}
    };
}
