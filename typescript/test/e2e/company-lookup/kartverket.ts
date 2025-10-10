/* Kartverket API functions
 * Uses undocumented API from Norwegian Mapping Authority
 * https://seeiendom.kartverket.no/api/soekEtterEiendom
 * 
 * Author: Terje Christensen (terchris)
 * GitHub: https://github.com/terchris
 */

import axios from 'axios';
import _ from 'lodash';
import {
    // Type definitions
    Kartverketeiendom,
    KartverketeiendomExtended,

    // Functions  
    createLogSystemObject,
    logger,
} from "./index.js";

// Import utility functions (will be created in address-utils.ts)
import {
    getRoadName,
    getRoadNumberAndLetter,
    removeLetterFromRoadNumber,
    getZipcodeFromKartverketAddress,
    getRoadNameAndNumberFromKartverketAddress,
} from "./address-utils.js";

const LOGGER_SYSTEM = "kartverket";

/** getKartverketAdressByRoadAndZipcode
 The API handeled by getGeonorgeLocationByPostAddress requires an exact address. Meaning that 
"ulvenveien 90" and "ulvenveien 90 A" is not an existing address. 
The API requires "ulvenveien 90A" to becorrectly identified as "ulvenveien 90".

This function uses a undocumented search used by the web page https://seeiendom.kartverket.no/
to find an address based on the road and zipcode.
* @param {*} road
* @param {*} zipcode
* @returns {KartverketeiendomExtended} foundKartverketArray - an array if found or empty array if not found

 Request:
 https://seeiendom.kartverket.no/api/soekEtterEiendom?searchstring=ulvenveien%2090,%20oslo
 
 Result:
 [ {
  "id" : 284583359,
  "kommunenavn" : "OSLO",
  "kommunenr" : "0301",
  "gaardsnr" : 122,
  "bruksnr" : 55,
  "festenr" : 0,
  "seksjonsnr" : 0,
  "veiadresse" : "ULVENVEIEN 90A, 0581 OSLO"
}, {
  "id" : 284583359,
  "kommunenavn" : "OSLO",
  "kommunenr" : "0301",
  "gaardsnr" : 122,
  "bruksnr" : 55,
  "festenr" : 0,
  "seksjonsnr" : 0,
  "veiadresse" : "ULVENVEIEN 90B, 0581 OSLO"
} ]

 */
export async function getKartverketAdressByRoadAndZipcode(searchRoad: string, zipcode: string): Promise<KartverketeiendomExtended[]> {

    const KARTVERKET_ADRESS_URL = "https://seeiendom.kartverket.no/api/soekEtterEiendom?";

    const functionName = "getKartverketAdressByRoadAndZipcode";
    var myVariables = {
        KARTVERKET_ADRESS_URL: KARTVERKET_ADRESS_URL,
        searchRoad: searchRoad,
        zipcode: zipcode,
        "response": "not set"
    };

    let kartverketAdressResponseArray: Kartverketeiendom[] = [];
    let foundKartverketArray: KartverketeiendomExtended[] = [];

    if (searchRoad && zipcode) { // only try to search if there are parameters
        let roadEncoded = encodeURIComponent(searchRoad); // encode it correctly
        let kartverketRequestURL = KARTVERKET_ADRESS_URL + "searchstring=" + roadEncoded;

        let axiosResponse: any = {};

        try {
            axiosResponse = await axios.get(kartverketRequestURL);

            if (null != axiosResponse.data) { // there is a result set
                kartverketAdressResponseArray = axiosResponse.data; // return the record
            } else {
                let logMessage = "DataMisssing: err getKartverketAdressByRoadAndZipcode no data:" + JSON.stringify(axiosResponse);
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

        if (_.isEmpty(kartverketAdressResponseArray)) {
            kartverketAdressResponseArray = [];
        } else {

            //separate road name and number in the searchRoad input
            let searchRoadName = getRoadName(searchRoad);
            let searchRoadNumberAndLetter = getRoadNumberAndLetter(searchRoad);
            let searchRoadNumber = removeLetterFromRoadNumber(searchRoadNumberAndLetter);

            //loop data and find the one with the correct zipcode and road name
            for (let i = 0; i < kartverketAdressResponseArray.length; i++) {
                let address = kartverketAdressResponseArray[i].veiadresse ?? "";
                let kartverketRoadNameAndNumber = getRoadNameAndNumberFromKartverketAddress(address);
                let kartverketRoadName = getRoadName(kartverketRoadNameAndNumber);
                let kartverketRoadNumberAndLetter = getRoadNumberAndLetter(kartverketRoadNameAndNumber);
                let kartverketRoadNumber = removeLetterFromRoadNumber(kartverketRoadNumberAndLetter);
                let kartverketZipcode = getZipcodeFromKartverketAddress(address);

                if (kartverketZipcode == zipcode) { // first of all. it must be the same zipcode
                    if (searchRoadName.toLowerCase() == kartverketRoadName.toLowerCase()) { // then the road name must be the same

                        if (searchRoadNumberAndLetter == kartverketRoadNumberAndLetter) { // then the road number and letter must be the same
                            // in this case we are searching with a road number and letter. And it is an exact match
                            let foundRecord: KartverketeiendomExtended = {
                                id: kartverketAdressResponseArray[i].id,
                                kommunenavn: kartverketAdressResponseArray[i].kommunenavn,
                                kommunenr: kartverketAdressResponseArray[i].kommunenr,
                                gaardsnr: kartverketAdressResponseArray[i].gaardsnr,
                                bruksnr: kartverketAdressResponseArray[i].bruksnr,
                                festenr: kartverketAdressResponseArray[i].festenr,
                                seksjonsnr: kartverketAdressResponseArray[i].seksjonsnr,
                                veiadresse: kartverketAdressResponseArray[i].veiadresse,

                                roadNameAndNumber: kartverketRoadNameAndNumber,
                                roadName: kartverketRoadName,
                                roadNumberAndLetter: kartverketRoadNumberAndLetter,
                                roadNumber: kartverketRoadNumber,
                                zipcode: kartverketZipcode
                            }
                            foundKartverketArray.push(foundRecord);
                        }
                        else {
                            if (searchRoadNumber == kartverketRoadNumber) { // then the road number must be the same
                                // in this case we are searching with a road number. But NOT a letter. And it is an exact match
                                let foundRecord = {
                                    id: kartverketAdressResponseArray[i].id,
                                    kommunenavn: kartverketAdressResponseArray[i].kommunenavn,
                                    kommunenr: kartverketAdressResponseArray[i].kommunenr,
                                    gaardsnr: kartverketAdressResponseArray[i].gaardsnr,
                                    bruksnr: kartverketAdressResponseArray[i].bruksnr,
                                    festenr: kartverketAdressResponseArray[i].festenr,
                                    seksjonsnr: kartverketAdressResponseArray[i].seksjonsnr,
                                    veiadresse: kartverketAdressResponseArray[i].veiadresse,

                                    roadNameAndNumber: kartverketRoadNameAndNumber,
                                    roadName: kartverketRoadName,
                                    roadNumberAndLetter: kartverketRoadNumberAndLetter,
                                    roadNumber: kartverketRoadNumber,
                                    zipcode: kartverketZipcode
                                }
                                foundKartverketArray.push(foundRecord);
                            }
                        }
                    }
                }
            } //end loop
        }

    }

    return foundKartverketArray;
}
