/**
 * 📍 Geonorge API - Type Definitions
 * 
 * Geonorge-specific types and interfaces
 */

export interface GeonorgeSearchResponse {
  adresser: {
    adressetekst: string;
    postnummer: string;
    poststed: string;
    kommunenummer: string;
    kommunenavn: string;
    fylkesnummer: string;
    fylkesnavn: string;
    representasjonspunkt?: {
      lat: number;
      lon: number;
      epsg: string;
    };
  }[];
  metadata: {
    side: number;
    treff: number;
    totaltAntallTreff: number;
    viserFra: number;
    viserTil: number;
  };
}

export interface GeonorgeAddress {
  adressetekst: string;
  postnummer: string;
  poststed: string;
  kommunenummer: string;
  kommunenavn: string;
  fylkesnummer: string;
  fylkesnavn: string;
  representasjonspunkt?: {
    lat: number;
    lon: number;
    epsg: string;
  };
}

