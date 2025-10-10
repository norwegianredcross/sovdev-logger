/* Type definitions for Norwegian address lookup and business registry libraries
 * Contains only the types needed for the refactored libraries
 * 
 * Author: Terje Christensen (terchris)
 * GitHub: https://github.com/terchris
 */

// ===== ADDRESS LOOKUP TYPES =====

export interface VisitingAddress {
    street?: string;
    city?: string;
    postcode?: string;
    country?: string;
}

export interface PostalAddress {
    street?: string;
    city?: string;
    postcode?: string;
    country?: string;
}

export interface AdminLocation {
    municipalityId?: string;
    municipalityName?: string;
    countyId?: string;
    countyName?: string;
}

export interface LatLng {
    lat?: number;
    lng?: number;
}

export interface LocationObject {
    visitingAddress?: VisitingAddress;
    postalAddress?: PostalAddress;
    adminLocation?: AdminLocation;
    latLng?: LatLng;
    geoPoint?: any;
}

export interface GeonorgeRepresentasjonspunkt {
    epsg?: string;
    lat?: number;
    lon?: number;
}

export interface Geonorgeadresse {
    urbComment?: string; // for debugging use: Used to indicate how we found the geonorgeRecord etc

    adressenavn?: string;
    adressetekst?: string;
    adressetilleggsnavn?: any;
    adressekode?: number;
    nummer?: number;
    bokstav?: string;
    kommunenummer?: string;
    kommunenavn?: string;
    gardsnummer?: number;
    bruksnummer?: number;
    festenummer?: number;
    undernummer?: any;
    bruksenhetsnummer?: string[];
    objtype?: string;
    poststed?: string;
    postnummer?: string;
    adressetekstutenadressetilleggsnavn?: string;
    stedfestingverifisert?: boolean;
    representasjonspunkt?: GeonorgeRepresentasjonspunkt;
    oppdateringsdato?: string;
}

export interface GeonorgeKommuneinfo {
    avgrensningsboks?: any;
    fylkesnavn?: string;
    fylkesnummer?: string;
    gyldigeNavn?: any;
    kommunenavn?: string;
    kommunenavnNorsk?: string;
    kommunenummer?: string;
    punktIOmrade?: any;
    samiskForvaltningsomrade?: boolean;
}

export interface Kartverketeiendom {
    id?: number;
    kommunenavn?: string;
    kommunenr?: string;
    gaardsnr?: number;
    bruksnr?: number;
    festenr?: number;
    seksjonsnr?: number;
    veiadresse?: string;
}

export interface KartverketeiendomExtended extends Kartverketeiendom {
    roadNameAndNumber?: string;
    roadName?: string;
    roadNumberAndLetter?: string;
    roadNumber?: string;
    zipcode?: string;
}

// ===== BRREG (BUSINESS REGISTRY) TYPES =====

export interface BrregAPIResponse {
    _embedded?: {
        enheter?: BrregAPIEnhet[];
    };
    _links?: {
        self: {
            href: string;
        };
        first: {
            href: string;
        };
        last: {
            href: string;
        };
        prev: {
            href: string;
        };
        next: {
            href: string;
        };
    };
    page?: {
        size: number;
        totalElements: number;
        totalPages: number;
        number: number;
    };
}

export interface BrregAPIEnhet {
    organisasjonsnummer?: string;
    navn?: string;
    organisasjonsform?: {
        kode: string;
        beskrivelse: string;
        _links: {
            self: {
                href: string;
            };
        };
    };
    postadresse?: {
        land?: string;
        landkode?: string;
        postnummer?: string;
        poststed?: string;
        adresse?: string[];
        kommune?: string;
        kommunenummer?: string;
    };
    hjemmeside?: string;
    registreringsdatoEnhetsregisteret?: string;
    registrertIMvaregisteret?: boolean;
    naeringskode1?: {
        beskrivelse: string;
        kode: string;
    };
    naeringskode2?: {
        beskrivelse: string;
        kode: string;
        hjelpeenhetskode?: boolean;
    };
    naeringskode3?: {
        beskrivelse: string;
        kode: string;
    };
    antallAnsatte?: number;
    overordnetEnhet?: string;
    forretningsadresse?: {
        land?: string;
        landkode?: string;
        postnummer?: string;
        poststed?: string;
        adresse?: string[];
        kommune?: string;
        kommunenummer?: string;
    };
    stiftelsesdato?: string;
    institusjonellSektorkode?: {
        kode: string;
        beskrivelse: string;
    };
    registrertIForetaksregisteret?: boolean;
    registrertIStiftelsesregisteret?: boolean;
    registrertIFrivillighetsregisteret?: boolean;
    sisteInnsendteAarsregnskap?: string;
    konkurs?: boolean;
    underAvvikling?: boolean;
    underTvangsavviklingEllerTvangsopplosning?: boolean;
    maalform?: string;
    _links?: {
        self: {
            href: string;
        },
        overordnetEnhet?: {
            href: string;
        },
    };
    slettedato?: string; // if a org is deleted you get this field and just name, organisasjonsnummer and organisasjonsform
    endDate?: string; // if the company is closed then this is the date
}
