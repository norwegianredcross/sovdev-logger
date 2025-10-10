/* Address lookup orchestration functions
 * Coordinates between Geonorge and Kartverket services with intelligent fallback strategies
 * 
 * Author: Terje Christensen (terchris)
 * GitHub: https://github.com/terchris
 */

import _ from 'lodash';

// Import types and utilities
import {
    LocationObject,
    Geonorgeadresse,
    KartverketeiendomExtended,
    getNested,
    addCommentToRecord,
} from "./index.js";

// Import service functions
import { getGeonorgeLocationByPostAddress } from "./geonorge.js";
import { getKartverketAdressByRoadAndZipcode } from "./kartverket.js";

// Import utility functions
import {
    fixRoadName,
    correctRoadnameAndLetter,
    removeLetterFromRoadname,
} from "./address-utils.js";

/** getGeonorgeLocationByLocationObject
 * The location object is a json object that contains the location information.
 * It has visitingAddress and postalAddress
 
* @param {object} locationObject - the location object
* @returns {Geonorgeadresse} geonorgeRecord - empty if not found

 The strategy for finding the location is:
 //1. Try to get geonorgeRecord by calling getGeonorgeLocationByPostAddress with the address in visitingAddress
 //2. Try to get geonorgeRecord by calling getGeonorgeLocationByPostAddress with the address in postalAddress
 //3. Try to get geonorgeRecod by fuzzy searching using the address in visitingAddress
 //4. Try to get geonorgeRecod by fuzzy searching using the address in postalAddress
 //5. Try to get geonorgeRecod by fuzzy searching using the corrected address in visitingAddress
 //6. Remove letter from the road number and try to get geonorgeRecord by calling getGeonorgeLocationByPostAddress
 //7. same as 5. but for the postalAddress
 //8. same as 6. but for the postalAddress

 if geonorgeRecord is found then a comment is added to the geonorgeRecord telling how we found it (step 1-8)

 */
export async function getGeonorgeLocationByLocationObject(locationObject: LocationObject): Promise<Geonorgeadresse> {

    let geonorgeRecord: Geonorgeadresse = {};

    let tmpVisitStreet: string = getNested(locationObject, "visitingAddress", "street") ?? "";
    let tmpVisitPostcode: string = getNested(locationObject, "visitingAddress", "postcode") ?? "";
    let tmpPostalStreet: string = getNested(locationObject, "postalAddress", "street") ?? "";
    let tmpPostalPostcode: string = getNested(locationObject, "postalAddress", "postcode") ?? "";

    //1. Try to get geonorgeRecord by calling getGeonorgeLocationByPostAddress with the address in visitingAddress
    if (tmpVisitStreet) {
        geonorgeRecord = await getGeonorgeLocationByPostAddress(fixRoadName(tmpVisitStreet), tmpVisitPostcode);
        if (!_.isEmpty(geonorgeRecord)) {
            geonorgeRecord = addCommentToRecord(geonorgeRecord, "1. visitingAddress: direct");
        }
    }

    // if there is no geonorgeRecord we will keep trying    
    if (_.isEmpty(geonorgeRecord)) {

        //2. Try to get geonorgeRecord by calling getGeonorgeLocationByPostAddress with the address in postalAddress
        if (tmpPostalStreet) {    // if there is a postalAddress, we will try using it
            geonorgeRecord = await getGeonorgeLocationByPostAddress(fixRoadName(tmpPostalStreet), tmpPostalPostcode);
            if (!_.isEmpty(geonorgeRecord)) {
                geonorgeRecord = addCommentToRecord(geonorgeRecord, "2. postalAddress: direct");
            }
        }

        if (_.isEmpty(geonorgeRecord)) {          // still no geonorgeRecord
            // we will try to get the address from kartverket by calling getKartverketAdressByRoadAndZipcode
            // this is a more fuzzy search and will return  "Havnegata 19B" and other letters when we search with "Havnegata 19" 

            //3. Try to get geonorgeRecod by fuzzy searching using the address in visitingAddress
            if (tmpVisitStreet) {
                geonorgeRecord = await loopKartverketWithRoadANDZipcode(tmpVisitStreet, tmpVisitPostcode);
                if (!_.isEmpty(geonorgeRecord)) {
                    geonorgeRecord = addCommentToRecord(geonorgeRecord, "3. visitingAddress: kartverket search");
                }
            }
            if (_.isEmpty(geonorgeRecord)) {  // still no geonorgeRecord
                //4. Try to get geonorgeRecod by fuzzy searching using the address in postalAddress
                if (tmpPostalStreet) {
                    geonorgeRecord = await loopKartverketWithRoadANDZipcode(tmpPostalStreet, tmpPostalPostcode);
                    if (!_.isEmpty(geonorgeRecord)) {
                        geonorgeRecord = addCommentToRecord(geonorgeRecord, "4. postalAddress: kartverket search");
                    }
                }
            }
        }

        if (_.isEmpty(geonorgeRecord)) { // still no geonorgeRecord

            if (tmpVisitStreet) { //blank street is trouble - so test for it) {
                //5. Try to get geonorgeRecod by fuzzy searching using the corrected address in visitingAddress
                // There are cases when the original search street is "Havnegata 19JUST RUBBISH" 
                // we have corrected it to "Havnegata 19"     
                //                            
                let searchRoad = correctRoadnameAndLetter(fixRoadName(tmpVisitStreet));

                // we will first see if the road number and letter syntax is correct
                if (tmpVisitStreet.toUpperCase() != searchRoad.toUpperCase()) { // only do a new search if the street is not the same as the searchRoad (case3. above)
                    // this is the case where the original street is "Havnegata 19JUST RUBBISH" and we have corrected it to "Havnegata 19"
                    geonorgeRecord = await loopKartverketWithRoadANDZipcode(searchRoad, tmpVisitPostcode);
                    if (!_.isEmpty(geonorgeRecord)) {
                        geonorgeRecord = addCommentToRecord(geonorgeRecord, "5. visitingAddress: kartverket search. corrected street");
                    }
                }
                if (_.isEmpty(geonorgeRecord)) { // still no geonorgeRecord
                    //6. Remove letter from the road number and try to get geonorgeRecord by calling getGeonorgeLocationByPostAddress
                    // there are cases where the input address is  "street": "Havnegata 19A"
                    // but the address is realy "street": "Havnegata 19B"
                    // we will remove the letter "A" from the road number and try again

                    let searchRoad = removeLetterFromRoadname(fixRoadName(tmpVisitStreet));

                    if (tmpVisitStreet.toUpperCase() != searchRoad.toUpperCase()) { // only do a new search if the street is not the same as the roadNumberWithoutLetter
                        geonorgeRecord = await loopKartverketWithRoadANDZipcode(searchRoad, tmpVisitPostcode);
                        if (!_.isEmpty(geonorgeRecord)) {
                            geonorgeRecord = addCommentToRecord(geonorgeRecord, "6. visitingAddress: kartverket search. removed letter on roadnumber");
                        }
                    }
                }
            }

            if (_.isEmpty(geonorgeRecord)) { // still no geonorgeRecord - lets do the same for the postalAddress

                if (tmpPostalStreet) {
                    //7. same as 5. but for the postalAddress
                    let searchRoad = correctRoadnameAndLetter(fixRoadName(tmpPostalStreet));

                    // we will first see if the road number and letter syntax is correct
                    if (tmpPostalStreet.toUpperCase() != searchRoad.toUpperCase()) { // only do a new search if the street is not the same as the searchRoad
                        // this is the case where the original street is "Havnegata 19JUST RUBBISH" and we have corrected it to "Havnegata 19"
                        geonorgeRecord = await loopKartverketWithRoadANDZipcode(searchRoad, tmpPostalPostcode);
                        if (!_.isEmpty(geonorgeRecord)) {
                            geonorgeRecord = addCommentToRecord(geonorgeRecord, "7. postalAddress: kartverket search. corrected street");
                        }
                    }
                    if (_.isEmpty(geonorgeRecord)) { // still no geonorgeRecord
                        //8. same as 6. but for the postalAddress
                        let searchRoad = removeLetterFromRoadname(fixRoadName(tmpPostalStreet));

                        if (tmpPostalStreet.toUpperCase() != searchRoad.toUpperCase()) { // only do a new search if the street is not the same as the searchRoad
                            geonorgeRecord = await loopKartverketWithRoadANDZipcode(searchRoad, tmpPostalPostcode);
                            if (!_.isEmpty(geonorgeRecord)) {
                                geonorgeRecord = addCommentToRecord(geonorgeRecord, "8. postalAddress: kartverket search. removed letter on roadnumber");
                            }
                        }
                    }
                }
            }
        }
    }
    return geonorgeRecord;
}

/** getAddressByRoadANDZipcode
 * Getting an address ia harder than it seems. This is what we will do in order to end up 
 * with a valid address.
* @param {string} roadName - the road name
* @param {string} zipcode - the zipcode
* @returns {object} - the geonorgeRecord
 
 1. Fix the way road numbers and letters are written.
 2. Try to get geonorgeRecord by calling getGeonorgeLocationByPostAddress
 3. If that fails, try to get the address from kartverket by calling getKartverketAdressByRoadAndZipcode
 4. If we get a array of addresses from kartverket, we will loop the addresses and try to get a geonorgeRecord by calling getGeonorgeLocationByPostAddress
    5. If we get a geonorgeRecord, we will return that.
 
 */
export async function getAddressByRoadANDZipcode(roadName: string, zipcode: string): Promise<Geonorgeadresse> {

    let geonorgeRecord: Geonorgeadresse = {};

    //1. Fix the way road numbers and letters are written.
    roadName = fixRoadName(roadName);

    //2. Try to get geonorgeRecord by calling getGeonorgeLocationByPostAddress
    geonorgeRecord = await getGeonorgeLocationByPostAddress(roadName, zipcode);

    //3. If that fails, try to get the address from kartverket by calling getKartverketAdressByRoadAndZipcode
    if (_.isEmpty(geonorgeRecord)) {
        let kartverketArray: KartverketeiendomExtended[] = await getKartverketAdressByRoadAndZipcode(roadName, zipcode);
        if (!_.isEmpty(kartverketArray)) {
            //4. If we get a array of addresses from kartverket, we will loop the addresses and try to get a geonorgeRecord by calling getGeonorgeLocationByPostAddress
            for (let i = 0; i < kartverketArray.length; i++) {
                let kartverketRecord: KartverketeiendomExtended = kartverketArray[i];
                geonorgeRecord = await getGeonorgeLocationByPostAddress(kartverketRecord.roadName!, kartverketRecord.zipcode!);
                if (!_.isEmpty(geonorgeRecord)) {
                    break; //if there is a record - then we have found it - so stop looping
                }
            }
        }
    }

    return geonorgeRecord;
}

/** loopKartverketWithRoadANDZipcode
 * take road and zipcode and loop and do the fuzzy search using getKartverketAdressByRoadAndZipcode
 * test all results from getKartverketAdressByRoadAndZipcode by using getGeonorgeLocationByPostAddress
 * and return the first one that exists in geonorge.
 * return "none" if no geonorgeRecord is found - or a valid geonorgeRecord
 */
async function loopKartverketWithRoadANDZipcode(road: string, zipcode: string): Promise<Geonorgeadresse> {

    let geonorgeRecord: Geonorgeadresse = {};
    let kartverketArray: KartverketeiendomExtended[] = await getKartverketAdressByRoadAndZipcode(fixRoadName(road), zipcode);

    if (!_.isEmpty(kartverketArray)) {
        // we will loop the addresses and try to get a geonorgeRecord by calling getGeonorgeLocationByPostAddress
        for (let i = 0; i < kartverketArray.length; i++) {
            let kartverketRecord: KartverketeiendomExtended = kartverketArray[i];
            geonorgeRecord = await getGeonorgeLocationByPostAddress(kartverketRecord.roadNameAndNumber!, kartverketRecord.zipcode!);
            if (!_.isEmpty(geonorgeRecord)) {
                break; //if there is a record - then we have found it - so stop looping
            }
        }
    }
    return geonorgeRecord;
}
