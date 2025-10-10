/* BRREG API functions
 * Pure API calls to Norwegian Business Registry (Brønnøysundregistrene)
 * Official API documentation: https://data.brreg.no/enhetsregisteret/api/docs/index.html
 * 
 * Author: Terje Christensen (terchris)
 * GitHub: https://github.com/terchris
 */

import axios from 'axios';
import {
    // Type definitions
    BrregAPIResponse,
    BrregAPIEnhet,

    // Functions
    createLogSystemObject,
    logger
} from "./index.js";

const LOGGER_SYSTEM = "brreg";
const BRREG_ENHETER_URL = "https://data.brreg.no/enhetsregisteret/api/enheter/";

/** getBrregOrgByOrganisasjonsnummer
 * Direct lookup in the BRREG database for a given organization number
 * @param {string} orgNumber - the organization number to lookup (must be 9 digits)
 * @returns {BrregAPIEnhet} - the BRREG record or empty object if not found
 * 
 * The data returned is described here https://data.brreg.no/enhetsregisteret/api/docs/index.html#enheter-oppslag
 */
export async function getBrregOrgByOrganisasjonsnummer(orgNumber: string): Promise<BrregAPIEnhet> {

    const functionName = "getBrregOrgByOrganisasjonsnummer";
    let brregRequestURL: string;
    let brregRecord: BrregAPIEnhet = {};
    let axiosResponse: any = {};

    var myVariables = {
        "orgNumber": orgNumber,
        "response": "not set"
    };

    if (orgNumber) {
        brregRequestURL = BRREG_ENHETER_URL + orgNumber;

        try {
            axiosResponse = await axios.get(brregRequestURL);

            if (null != axiosResponse.data.organisasjonsnummer) { // there is a result set            
                brregRecord = axiosResponse.data; // return the one that is there
            } else {
                let logMessage = "ParameterMissing: no organisasjonsnummer.";
                myVariables.response = JSON.stringify(axiosResponse);
                let logObject = createLogSystemObject(functionName, null, myVariables, LOGGER_SYSTEM);
                logger.info(logMessage, logObject);
            }

        }
        catch (e) {
            myVariables.response = JSON.stringify(axiosResponse);
            let logMessage = "catchError";
            let logObject = createLogSystemObject(functionName, e, myVariables, LOGGER_SYSTEM);
            logger.error(logMessage, logObject);
        }
    }

    return brregRecord;
}

/** searchBrregByName
 * Search BRREG by organization name (fuzzy search)
 * @param {string} orgName - the name of the organization to search for
 * @returns {BrregAPIEnhet[]} - array of organizations that match the name - if none found returns an empty array
 * 
 * Returns an array of organizations based on BRREG fuzzy search - probably a page of 20 organizations
 * The data returned is described here https://data.brreg.no/enhetsregisteret/api/docs/index.html#enheter-oppslag
 */
export async function searchBrregByName(orgName: string): Promise<BrregAPIEnhet[]> {

    const functionName = "searchBrregByName";
    let brregRequestURL: string;
    let foundOrganizationsArray: BrregAPIEnhet[] = [];
    let axiosResponse: any = {};

    let myVariables = {
        "orgName": orgName,
        "response": "not set"
    };

    if (orgName) {
        let encodedOrgName = encodeURIComponent(orgName);
        brregRequestURL = BRREG_ENHETER_URL + "?navn=" + encodedOrgName;

        try {
            axiosResponse = await axios.get(brregRequestURL);

            if (null != axiosResponse.data.page) { // there is a result set            
                if (axiosResponse.data.hasOwnProperty('_embedded')) {
                    if (axiosResponse.data._embedded.hasOwnProperty('enheter')) {
                        foundOrganizationsArray = axiosResponse.data._embedded.enheter;
                    } else {
                        let logMessage = "DataIntegrety: no enheter.";
                        myVariables.response = JSON.stringify(axiosResponse);
                        let logObject = createLogSystemObject(functionName, null, myVariables, LOGGER_SYSTEM);
                        logger.info(logMessage, logObject);
                    }
                } else {
                    let logMessage = "DataIntegrety: no _embedded.";
                    myVariables.response = JSON.stringify(axiosResponse);
                    let logObject = createLogSystemObject(functionName, null, myVariables, LOGGER_SYSTEM);
                    logger.info(logMessage, logObject);
                }
            } else {
                let logMessage = "DataIntegrety: no page.";
                myVariables.response = JSON.stringify(axiosResponse);
                let logObject = createLogSystemObject(functionName, null, myVariables, LOGGER_SYSTEM);
                logger.info(logMessage, logObject);
            }

        }
        catch (e) {
            myVariables.response = JSON.stringify(axiosResponse);
            let logMessage = "catchError";
            let logObject = createLogSystemObject(functionName, e, myVariables, LOGGER_SYSTEM);
            logger.error(logMessage, logObject);
        }
    } else {
        foundOrganizationsArray = []; // return an empty array
    }

    return foundOrganizationsArray;
}

/** searchBrregByWebsite
 * Search BRREG by website/domain name
 * @param {string} domainName - the domain name to search for (e.g., "example.com")
 * @returns {BrregAPIResponse} - the full response object from BRREG - if none found returns an empty object
 * 
 * The data returned is described here https://data.brreg.no/enhetsregisteret/api/docs/index.html#enheter-oppslag
 */
export async function searchBrregByWebsite(domainName: string): Promise<BrregAPIResponse> {

    const functionName = "searchBrregByWebsite";
    let brregRequestURL: string;
    let brregResponseObject: BrregAPIResponse = {};
    let axiosResponse: any = {};

    let myVariables = {
        "domainName": domainName,
        "response": "not set"
    };

    if (domainName) {
        brregRequestURL = BRREG_ENHETER_URL + "?hjemmeside=" + domainName;

        try {
            axiosResponse = await axios.get(brregRequestURL);

            if (axiosResponse.data.page.totalElements > 0) { // there is a result set            
                brregResponseObject = axiosResponse.data; // return the response
            }

        }
        catch (e) {
            myVariables.response = JSON.stringify(axiosResponse);
            let logMessage = "catchError";
            let logObject = createLogSystemObject(functionName, e, myVariables, LOGGER_SYSTEM);
            logger.error(logMessage, logObject);
        }
    }

    return brregResponseObject;
}

/** getBrregFullResponseByName
 * Get full BRREG API response by organization name
 * @param {string} organizationName - the name of the organization to search for
 * @returns {BrregAPIResponse} - the whole BRREG response object - if none found returns an empty object
 * 
 * The data returned is described here https://data.brreg.no/enhetsregisteret/api/docs/index.html#enheter-oppslag
 */
export async function getBrregFullResponseByName(organizationName: string): Promise<BrregAPIResponse> {

    const functionName = "getBrregFullResponseByName";
    let brregRequestURL: string;
    let brregResponse: BrregAPIResponse = {};
    let axiosResponse: any = {};

    const myVariables = {
        "organizationName": organizationName,
        "response": "not set"
    };

    if (organizationName) {
        let encodedOrgName = encodeURIComponent(organizationName);
        brregRequestURL = BRREG_ENHETER_URL + "?navn=" + encodedOrgName;

        try {
            axiosResponse = await axios.get(brregRequestURL);

            if (axiosResponse.data.page.totalElements > 0) { // there is a result set            
                brregResponse = axiosResponse.data; // return the full response
            }

        }
        catch (e) {
            myVariables.response = JSON.stringify(axiosResponse);
            let logMessage = "catchError";
            let logObject = createLogSystemObject(functionName, e, myVariables, LOGGER_SYSTEM);
            logger.error(logMessage, logObject);
        }
    }

    return brregResponse;
}
