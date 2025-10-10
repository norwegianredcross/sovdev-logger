/* Geonorge API functions
 * Official Norwegian geographical data service
 * https://ws.geonorge.no/adresser/v1/
 */

import axios from 'axios';
import {
    // Type definitions
    Geonorgeadresse,
    GeonorgeKommuneinfo,

    // Functions  
    createLogSystemObject,
    logger,
} from "./index.js";

const LOGGER_SYSTEM = "geonorge";

/** getGeonorgeLocationByPostAddress
 *  takes road and zipcode and returns ONE (the first, and only) object as described in the "Adresse REST-API"
 *  https://ws.geonorge.no/adresser/v1/
 * @param {string} road
 * @param {string} zipcode
 * @returns {Geonorgeadresse} foundReonorgeRecord - one record or empty if not found
 *   
 * TEST URL https://ws.geonorge.no/adresser/v1/sok?adressetekst=vestengkleiva%203&postnummer=1385"
 * 
 * some doc here https://kartkatalog.geonorge.no/metadata/44eeffdc-6069-4000-a49b-2d6bfc59ac61
 */
export async function getGeonorgeLocationByPostAddress(road: string, zipcode: string): Promise<Geonorgeadresse> {

    const GEONORGE_ADRESS_URL = "https://ws.geonorge.no/adresser/v1/sok?";
    const functionName = "getGeonorgeLocationByPostAddress";

    var myVariables = {
        GEONORGE_ADRESS_URL: GEONORGE_ADRESS_URL,
        road: road,
        zipcode: zipcode,
        "response": "not set"
    };

    let foundReonorgeRecord: Geonorgeadresse = {};
    let axiosResponse: any = {};

    if (road && zipcode) { // only try to search if there are parameters
        road = encodeURIComponent(road); // encode it correctly
        let geonorgeRequestURL = GEONORGE_ADRESS_URL + "adressetekst=" + road + "&postnummer=" + zipcode

        try {
            axiosResponse = await axios.get(geonorgeRequestURL);

            if (null != axiosResponse.data.metadata) { // there is a result set

                if (axiosResponse.data.metadata.hasOwnProperty('totaltAntallTreff')) {
                    let numResponses = parseInt(axiosResponse.data.metadata.totaltAntallTreff);
                    if (numResponses == 1) { //only valid if there is just one response
                        foundReonorgeRecord = axiosResponse.data.adresser[0]; // return the one that is there
                    }
                } else {
                    let logMessage = "DataIntegrety: no totaltAntallTreff:" + JSON.stringify(axiosResponse);
                    let logObject = createLogSystemObject(functionName, null, myVariables, LOGGER_SYSTEM);
                    logger.info(logMessage, logObject);
                }
            } else {
                let logMessage = "DataIntegrety: no metadata:" + JSON.stringify(axiosResponse);
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
    return foundReonorgeRecord;
}

/** getGeonorgeFylkeByKommunenummer
 * takes a kommune number and returns the kummune info record
 * @param {string} kommunenummer
 * @returns {GeonorgeKommuneinfo} foundReonorgeRecord - one record or empty if not found
 * 
 * TEST URL https://ws.geonorge.no/kommuneinfo/v1/kommuner/3025
 */
export async function getGeonorgeFylkeByKommunenummer(kommunenummer: string): Promise<GeonorgeKommuneinfo> {

    const GEONORGE_ADRESS_URL = "https://ws.geonorge.no/kommuneinfo/v1/kommuner/";
    const functionName = "getGeonorgeFylkeByKommunenummer";

    var myVariables = {
        GEONORGE_ADRESS_URL: GEONORGE_ADRESS_URL,
        kommunenummer: kommunenummer,
        "response": "not set"
    };

    let geonorgeRequestURL = GEONORGE_ADRESS_URL + kommunenummer
    let kommuneinfoRecord: GeonorgeKommuneinfo = {};

    let axiosResponse: any = {};

    try {
        axiosResponse = await axios.get(geonorgeRequestURL);

        if (null != axiosResponse.data.fylkesnavn) { // there is a result set
            kommuneinfoRecord = axiosResponse.data; // return the record
        } else {
            let logMessage = "DataIntegrety: no fylkesnavn:" + JSON.stringify(axiosResponse);
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

    return kommuneinfoRecord;
}
