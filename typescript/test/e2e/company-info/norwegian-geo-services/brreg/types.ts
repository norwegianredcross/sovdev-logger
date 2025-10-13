/**
 * 🏢 BRREG API - Type Definitions
 * 
 * BRREG (Norwegian Business Registry) specific types and interfaces
 */

export interface BusinessAddress {
  adresse?: string[];
  postnummer?: string;
  poststed?: string;
  kommune?: string;
  kommunenummer?: string;
  land?: string;
  landkode?: string;
}

export interface CompanyBasicInfo {
  organisasjonsnummer: string;
  navn: string;
  organisasjonsform?: {
    kode: string;
    beskrivelse: string;
  };
  registreringsdatoEnhetsregisteret?: string;
  forretningsadresse?: BusinessAddress;
  postadresse?: BusinessAddress;
}

export interface CompanyDetailedInfo extends CompanyBasicInfo {
  hjemmeside?: string;
  telefon?: string;
  epost?: string;
  naeringskode1?: {
    beskrivelse: string;
    kode: string;
  };
  antallAnsatte?: number;
  sisteInnsendteAarsregnskap?: string;
  konkurs?: boolean;
  underAvvikling?: boolean;
  underTvangsavviklingEllerTvangsopplosning?: boolean;
  maalform?: string;
}

export interface CompanySearchParams {
  navn?: string;
  organisasjonsnummer?: string;
  postnummer?: string;
  kommune?: string;
  naeringskode?: string;
  size?: number;
  page?: number;
}

export interface CompanySearchResult {
  enheter: CompanyBasicInfo[];
  side: {
    nummer: number;
    størrelse: number;
    totalAntall: number;
    totalSider: number;
  };
}

/**
 * 🔔 BRREG Updates (Oppdateringer) types
 * Endpoint: /oppdateringer/enheter?dato=YYYY-MM-DDTHH:mm:ss
 */
export type BrregUpdateChangeType = 'Ny' | 'Endring' | 'Sletting' | 'Fjernet' | 'Ukjent' | string;

export interface BrregUpdate {
  oppdateringsid: number;
  dato: string; // ISO date string
  organisasjonsnummer: string;
  endringstype: BrregUpdateChangeType;
}

export interface BrregUpdatesResponsePage {
  size: number;
  totalElements: number;
  totalPages: number;
  number: number;
}

export interface BrregUpdatesResponse {
  _embedded: {
    oppdaterteEnheter: BrregUpdate[];
  };
  page: BrregUpdatesResponsePage;
}

