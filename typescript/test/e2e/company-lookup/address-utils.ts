/* Address utility functions
 * Shared address parsing and normalization utilities for Norwegian addresses
 * 
 * Author: Terje Christensen (terchris)
 * GitHub: https://github.com/terchris
 */

import _ from 'lodash';

/** fixRoadName
Fix the way road numbers and letters are written.
"ulvenveien 90 A" is not an existing address. 
it must be written as "ulvenveien 90a" to becorrect
 */
export function fixRoadName(road: string): string {
    let newRoad = "";
    let nextChar = "";
    if (road) {
        road = road.trim(); // trim tailing spaces on road string
        road = road.toUpperCase(); // make road string uppercase

        for (let i = 0; i < road.length; i++) {
            let char = road.charAt(i);
            newRoad = newRoad + char;

            if (!isNaN(parseInt(char)) && nextChar != " ") {
                // if char is a number and the next char is not a space
                nextChar = road.charAt(i + 1); // get the next char
                if (nextChar == " ") {
                    // if the next char is a space
                    // add everything after he space to the new road string
                    let restOfString = road.substring(i + 2, road.length);
                    newRoad = newRoad + restOfString;
                    break;
                }
            }
        }
    }

    return newRoad;
}

/** getRoadName
 * takes a road string (eg "Havnegata 19A") and removes the number 
 * and returns the road name "Havnegata"
 */
export function getRoadName(roadString: string): string {

    let foundRoadName = "";
    let spaceIndex = roadString.lastIndexOf(" ");
    if (spaceIndex > 0) {
        foundRoadName = roadString.substring(0, spaceIndex);
    } else {
        foundRoadName = roadString;
    }

    return foundRoadName;
}

/** getRoadNumberAndLetter
 * takes a road string (eg "Havnegata 19A") and removes the name of the road
 * and returns the road number "19A"
 * @param {string} roadString
 * @returns {string} roadNumberAndLetter -if there is no number, it returns an empty string ""
 * 
 * if the roadString is "Havnegata 1-2" we return "1-2"
 * if the roadString is "Havnegata 1-2A" we return "1-2A"
 * if the roadString is "Havnegata 19JUST RUBBISH" we return "19"
 */
export function getRoadNumberAndLetter(roadString: string): string {

    //first we assume that the number of the road is after the last space character in the roadString
    let foundRoadNumber = "";
    let spaceIndex = roadString.lastIndexOf(" ");
    if (spaceIndex > 0) {
        foundRoadNumber = roadString.substring(spaceIndex + 1);
    }

    //now we need to validate if the foundRoadNumber is a number    
    if (foundRoadNumber) {
        let roadNumber = "";
        //first get the characters 0 to 9 and - (accepting 1-3 as a road number)
        for (let i = 0; i < foundRoadNumber.length; i++) { //loop the foundRoadNumber
            let char = foundRoadNumber.charAt(i);
            if (_.isNumber(char) || char == "-") { // if char is a number OR char is a "-" 
                roadNumber = roadNumber + char;
            } else {
                break; // no point in looping further if we have found a non-number character
            }
        }

        //loop the foundRoadNumber string and copy the characters that is a number or "-"

        //then check what comes after the roadNumber
        if (roadNumber.length == foundRoadNumber.length) { // if the roadNumber is the same length as the foundRoadNumber
            // then there is no letter after the foundRoadNumber
            // so we will return the foundRoadNumber
            //return foundRoadNumber;
        } else {
            // there is a character or more  after the foundRoadNumber
            // valid valid roadnumbers have just one letter after the number
            // if there is more than one character, we will remove all of them
            let moreCharacters = foundRoadNumber.substring(roadNumber.length);
            if (moreCharacters.length > 1) {
                // we will remove all characters after the roadNumber if there are more than one eg "19JUST RUBBISH"
                foundRoadNumber = roadNumber;
            } else {
                // we will return the roadNumber
                //return foundRoadNumber;
            }
        }
    }

    return foundRoadNumber;
}

/** removeLetterFromRoadNumber
 * takes a road number (eg "19A") and removes the letter "A"
 * so that "19" is returned.
 * if the road number is "1-2A" we return "1-2"
 */
export function removeLetterFromRoadNumber(roadNumberAndLetter: string): string {
    let roadNumberWithoutLetter = "";
    if (roadNumberAndLetter) {
        // first get the characters 0 to 9 and - (accepting 1-3 as a road number)
        for (let i = 0; i < roadNumberAndLetter.length; i++) {
            // loop the foundRoadNumber
            let char = roadNumberAndLetter.charAt(i);
            if (!isNaN(Number(char)) || char == "-") {
                // if char is a number OR char is a "-"
                roadNumberWithoutLetter = roadNumberWithoutLetter + char;
            } else {
                break; // no point in looping further if we have found a non-number character
            }
        }
    }
    return roadNumberWithoutLetter;
}

/** getZipcodeFromKartverketAddress
 * takes a kartverket address object and returns the zipcode
 * if the zipcode is not found, it returns ""
 * 
 * the kartverket address string is like this:
 * "Havnegata 19A, 0170 Oslo"
 */
export function getZipcodeFromKartverketAddress(kartverketAddress: string): string {

    let foundZipcode = "";
    // find the first number after , in the address string
    let commaIndex = kartverketAddress.indexOf(",");
    if (commaIndex > 0) {
        let hasZipcode = kartverketAddress.substring(commaIndex + 1).match(/\d+/); //extract the number after the , 
        if (hasZipcode) {
            foundZipcode = hasZipcode[0];
        }
    }

    return foundZipcode;
}

/** getRoadNameAndNumberFromKartverketAddress
 * takes a kartverket address string and returns the roadname and number
 * if the roadname and number is not found, it returns ""
 * 
 * the kartverket address string is like this:
 * "Havnegata 19A, 0170 Oslo"
 * this function will return "Havnegata 19A"
 */
export function getRoadNameAndNumberFromKartverketAddress(kartverketAddress: string): string {
    let roadnameAndNumber = "";

    let commaIndex = kartverketAddress.indexOf(",");
    if (commaIndex > 0) {
        roadnameAndNumber = kartverketAddress.substring(0, commaIndex);
    }
    return roadnameAndNumber;
}

/** correctRoadnameAndLetter
 * takes a fullRoadName containing a full roadname, a number and a letter
 * and returns the correct roadname and letter 
 * the fullRoadName address string is like this:
 * "Havnegata 19A"
 * this function will return "Havnegata 19A"
 * If the fullRoadName is "Havnegata 1-2A" we return "Havnegata 1-2A"
 * If the fullRoadName is "Havnegata 19JUST RUBBISH" we return "Havnegata 19"
 * 
*/
export function correctRoadnameAndLetter(fullRoadName: string): string {

    let correctedRoadnameAndnumber = "";

    if (fullRoadName) {
        let roadName = getRoadName(fullRoadName);
        let roadNumberAndLetter = getRoadNumberAndLetter(fullRoadName);
        if (roadNumberAndLetter) {
            correctedRoadnameAndnumber = roadName + " " + roadNumberAndLetter;
        } else {
            correctedRoadnameAndnumber = roadName; //there are no numbers in the roadname
        }
    }

    return correctedRoadnameAndnumber;
}

/** removeLetterFromRoadname
 * takes a fullRoadName containing a full roadname, a number and a letter
 * and returns the roadname and without the letter
 * the fullRoadName address string is like this:
 * "Havnegata 19A"
 * this function will return "Havnegata 19"
 *  If the fullRoadName is "Havnegata 1-2A" we return "Havnegata 1-2"
 * 
 */
export function removeLetterFromRoadname(fullRoadName: string): string {

    let roadNameAndNumberWithoutLetter = "";

    let roadName = getRoadName(fullRoadName);
    let roadNumberAndLetter = getRoadNumberAndLetter(fullRoadName);
    let roadNumberWithoutLetter = removeLetterFromRoadNumber(roadNumberAndLetter);

    if (roadNumberWithoutLetter) {
        roadNameAndNumberWithoutLetter = roadName + " " + roadNumberWithoutLetter;
    } else {
        if (roadNumberAndLetter) {
            roadNameAndNumberWithoutLetter = roadName + " " + roadNumberAndLetter;
        } else {
            roadNameAndNumberWithoutLetter = roadName; //there are no letters in the number
        }
    }

    return roadNameAndNumberWithoutLetter;
}
