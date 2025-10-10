/**
 * Environment Configuration Helper for Test Programs
 * 
 * This module provides a robust, type-safe way to read various types of test data
 * from environment variables. It supports:
 * - Simple comma-separated lists (_LIST suffix)
 * - JSON objects and arrays (_JSON suffix)
 * - Base64 encoded JSON data (_B64 suffix)
 * - Plain string values
 * 
 * Usage Examples:
 * ```typescript
 * // Simple lists
 * const companies = EnvConfig.getList('TEST_COMPANIES_LIST', ['defaultCompany']);
 * 
 * // JSON data
 * const addresses = EnvConfig.getJSON('TEST_ADDRESSES_JSON', []);
 * 
 * // Base64 encoded JSON (most reliable for CI/CD)
 * const users = EnvConfig.getJSONBase64('TEST_USERS_B64', []);
 * 
 * // Auto-detection based on suffix
 * const autoData = EnvConfig.get('TEST_DATA_LIST'); // Automatically parsed as list
 * ```
 * 
 * Environment Variable Naming Conventions:
 * - `VARIABLE_NAME_LIST`: Comma-separated values
 * - `VARIABLE_NAME_JSON`: JSON string data
 * - `VARIABLE_NAME_B64`: Base64 encoded JSON data
 * - `VARIABLE_NAME`: Plain string value
 * 
 * @author Generated for sovdev-logger test suite
 * @version 1.0.0
 */

/**
 * Configuration options for environment variable parsing
 */
interface ParseOptions {
  /** Whether to log warnings when parsing fails */
  logWarnings?: boolean;
  /** Whether to log detailed error information in non-production environments */
  logDetails?: boolean;
  /** Custom delimiter for list parsing (default: ',') */
  listDelimiter?: string;
}

/**
 * Result type for environment variable parsing operations
 */
interface ParseResult<T> {
  /** Whether the parsing was successful */
  success: boolean;
  /** The parsed value (or fallback if parsing failed) */
  value: T;
  /** Error message if parsing failed */
  error?: string;
  /** The raw environment variable value that was parsed */
  rawValue?: string;
}

/**
 * Environment configuration helper class for test programs
 * 
 * Provides type-safe, robust methods for reading test data from environment variables
 * with comprehensive error handling and fallback support.
 */
export class EnvConfig {
  private static readonly DEFAULT_OPTIONS: Required<ParseOptions> = {
    logWarnings: true,
    logDetails: process.env.NODE_ENV !== 'production',
    listDelimiter: ','
  };

  /**
   * Get a comma-separated list from an environment variable
   * 
   * @param envKey - Environment variable name (should end with _LIST)
   * @param fallback - Default value if env var is missing or invalid
   * @param options - Parsing options
   * @returns Array of trimmed, non-empty strings
   * 
   * @example
   * ```typescript
   * // Environment: TEST_COMPANIES_LIST=123,456,789
   * const companies = EnvConfig.getList('TEST_COMPANIES_LIST', ['default']);
   * // Returns: ['123', '456', '789']
   * 
   * // With custom delimiter for addresses using semicolons
   * // Environment: TEST_ADDRESSES_LIST=vestengkleiva 3, 1385 asker;karl johans gate 1, 0154 oslo
   * const addresses = EnvConfig.getList('TEST_ADDRESSES_LIST', [], { listDelimiter: ';' });
   * // Returns: ['vestengkleiva 3, 1385 asker', 'karl johans gate 1, 0154 oslo']
   * 
   * // Handling empty values and whitespace
   * // Environment: TEST_IDS_LIST=  123 , , 456 ,  789  
   * const ids = EnvConfig.getList('TEST_IDS_LIST');
   * // Returns: ['123', '456', '789'] (empty values filtered out)
   * ```
   */
  static getList(
    envKey: string, 
    fallback: string[] = [], 
    options: ParseOptions = {}
  ): string[] {
    const opts = { ...this.DEFAULT_OPTIONS, ...options };
    const result = this.parseList(envKey, fallback, opts);
    
    if (!result.success && opts.logWarnings) {
      this.logParseError('LIST', envKey, result.error, result.rawValue, opts.logDetails);
    }
    
    return result.value;
  }

  /**
   * Get JSON data from an environment variable
   * 
   * @param envKey - Environment variable name (should end with _JSON)
   * @param fallback - Default value if env var is missing or invalid
   * @param options - Parsing options
   * @returns Parsed JSON data
   * 
   * @example
   * ```typescript
   * // Simple JSON array
   * // Environment: TEST_USERS_JSON=[{"id":1,"name":"John"},{"id":2,"name":"Jane"}]
   * const users = EnvConfig.getJSON('TEST_USERS_JSON', []);
   * // Returns: [{ id: 1, name: "John" }, { id: 2, name: "Jane" }]
   * 
   * // JSON object
   * // Environment: TEST_CONFIG_JSON={"timeout":5000,"retries":3,"debug":true}
   * const config = EnvConfig.getJSON('TEST_CONFIG_JSON', {});
   * // Returns: { timeout: 5000, retries: 3, debug: true }
   * 
   * // Complex nested data
   * // Environment: TEST_ADDRESSES_JSON=[{"street":"vestengkleiva 3","city":"asker","postal":"1385","country":"norway"}]
   * interface Address { street: string; city: string; postal: string; country: string; }
   * const addresses = EnvConfig.getJSON<Address[]>('TEST_ADDRESSES_JSON', []);
   * ```
   */
  static getJSON<T = any>(
    envKey: string, 
    fallback: T, 
    options: ParseOptions = {}
  ): T {
    const opts = { ...this.DEFAULT_OPTIONS, ...options };
    const result = this.parseJSON<T>(envKey, fallback, opts);
    
    if (!result.success && opts.logWarnings) {
      this.logParseError('JSON', envKey, result.error, result.rawValue, opts.logDetails);
    }
    
    return result.value;
  }

  /**
   * Get Base64 encoded JSON data from an environment variable
   * 
   * This is the most reliable method for complex data in CI/CD environments
   * as it avoids shell escaping issues.
   * 
   * @param envKey - Environment variable name (should end with _B64)
   * @param fallback - Default value if env var is missing or invalid
   * @param options - Parsing options
   * @returns Parsed JSON data from Base64 string
   * 
   * @example
   * ```typescript
   * // First, encode your data to Base64:
   * // Original: [{"street":"vestengkleiva 3","city":"asker","notes":"Special chars: $ & !"}]
   * // Base64: W3sic3RyZWV0IjoidmVzdGVuZ2tsZWl2YSAzIiwiY2l0eSI6ImFza2VyIiwibm90ZXMiOiJTcGVjaWFsIGNoYXJzOiAkICYgISJ9XQ==
   * 
   * // Environment: TEST_ADDRESSES_B64=W3sic3RyZWV0IjoidmVzdGVuZ2tsZWl2YSAzIiwiY2l0eSI6ImFza2VyIn1d
   * const addresses = EnvConfig.getJSONBase64('TEST_ADDRESSES_B64', []);
   * // Returns: [{ street: "vestengkleiva 3", city: "asker" }]
   * 
   * // Generate Base64 from JavaScript:
   * const data = [{ id: 1, name: "Test User", special: "chars: $&!" }];
   * const base64 = Buffer.from(JSON.stringify(data)).toString('base64');
   * console.log(base64); // Use this value in your .env file
   * ```
   */
  static getJSONBase64<T = any>(
    envKey: string, 
    fallback: T, 
    options: ParseOptions = {}
  ): T {
    const opts = { ...this.DEFAULT_OPTIONS, ...options };
    const result = this.parseJSONBase64<T>(envKey, fallback, opts);
    
    if (!result.success && opts.logWarnings) {
      this.logParseError('BASE64_JSON', envKey, result.error, result.rawValue, opts.logDetails);
    }
    
    return result.value;
  }

  /**
   * Get a plain string value from an environment variable
   * 
   * @param envKey - Environment variable name
   * @param fallback - Default value if env var is missing
   * @returns String value or fallback
   * 
   * @example
   * ```typescript
   * // Environment: API_KEY=secret123
   * const apiKey = EnvConfig.getString('API_KEY', 'default-key');
   * // Returns: 'secret123'
   * 
   * // Missing environment variable
   * const missing = EnvConfig.getString('MISSING_VAR', 'fallback');
   * // Returns: 'fallback'
   * ```
   */
  static getString(envKey: string, fallback: string = ''): string {
    return process.env[envKey] || fallback;
  }

  /**
   * Get a numeric value from an environment variable
   * 
   * @param envKey - Environment variable name
   * @param fallback - Default value if env var is missing or invalid
   * @returns Numeric value or fallback
   * 
   * @example
   * ```typescript
   * // Environment: API_TIMEOUT=5000
   * const timeout = EnvConfig.getNumber('API_TIMEOUT', 3000);
   * // Returns: 5000
   * 
   * // Invalid number
   * // Environment: INVALID_NUMBER=not-a-number
   * const invalid = EnvConfig.getNumber('INVALID_NUMBER', 100);
   * // Returns: 100 (fallback)
   * 
   * // Decimal numbers
   * // Environment: RATE=0.75
   * const rate = EnvConfig.getNumber('RATE', 1.0);
   * // Returns: 0.75
   * ```
   */
  static getNumber(envKey: string, fallback: number = 0): number {
    const value = process.env[envKey];
    if (!value) return fallback;
    
    const parsed = Number(value);
    return isNaN(parsed) ? fallback : parsed;
  }

  /**
   * Get a boolean value from an environment variable
   * 
   * Accepts: 'true', 'false', '1', '0', 'yes', 'no' (case insensitive)
   * 
   * @param envKey - Environment variable name
   * @param fallback - Default value if env var is missing or invalid
   * @returns Boolean value or fallback
   * 
   * @example
   * ```typescript
   * // Environment: DEBUG=true
   * const debug = EnvConfig.getBoolean('DEBUG', false);
   * // Returns: true
   * 
   * // Different true values
   * // Environment: ENABLE_FEATURE=1
   * const feature1 = EnvConfig.getBoolean('ENABLE_FEATURE', false); // Returns: true
   * 
   * // Environment: VERBOSE=yes
   * const verbose = EnvConfig.getBoolean('VERBOSE', false); // Returns: true
   * 
   * // Invalid boolean
   * // Environment: INVALID_BOOL=maybe
   * const invalid = EnvConfig.getBoolean('INVALID_BOOL', false); // Returns: false (fallback)
   * ```
   */
  static getBoolean(envKey: string, fallback: boolean = false): boolean {
    const value = process.env[envKey];
    if (!value) return fallback;
    
    const normalized = value.toLowerCase().trim();
    
    if (['true', '1', 'yes', 'on'].includes(normalized)) return true;
    if (['false', '0', 'no', 'off'].includes(normalized)) return false;
    
    return fallback;
  }

  /**
   * Auto-detect and parse environment variable based on naming convention
   * 
   * Uses suffix to determine parsing method:
   * - _LIST: Parse as comma-separated list
   * - _JSON: Parse as JSON
   * - _B64: Parse as Base64 encoded JSON
   * - Default: Return as string
   * 
   * @param envKey - Environment variable name
   * @param fallback - Default value if env var is missing or invalid
   * @param options - Parsing options
   * @returns Parsed value based on naming convention
   * 
   * @example
   * ```typescript
   * // Auto-detection based on suffix
   * const companies = EnvConfig.get('TEST_COMPANIES_LIST', []); // Auto-parsed as list
   * const config = EnvConfig.get('TEST_CONFIG_JSON', {}); // Auto-parsed as JSON  
   * const data = EnvConfig.get('TEST_DATA_B64', {}); // Auto-parsed as Base64 JSON
   * const apiKey = EnvConfig.get('API_KEY', 'default'); // Returned as string
   * 
   * // Type safety with generics
   * interface User { id: number; name: string; }
   * const users = EnvConfig.get<User[]>('TEST_USERS_JSON', []);
   * ```
   */
  static get<T = any>(
    envKey: string, 
    fallback: T, 
    options: ParseOptions = {}
  ): T {
    if (envKey.endsWith('_LIST')) {
      return this.getList(envKey, fallback as string[], options) as T;
    }
    
    if (envKey.endsWith('_JSON')) {
      return this.getJSON<T>(envKey, fallback, options);
    }
    
    if (envKey.endsWith('_B64')) {
      return this.getJSONBase64<T>(envKey, fallback, options);
    }
    
    // Default to string
    return (process.env[envKey] || fallback) as T;
  }

  /**
   * Check if an environment variable exists and has a non-empty value
   * 
   * @param envKey - Environment variable name
   * @returns True if the environment variable exists and is not empty
   * 
   * @example
   * ```typescript
   * // Environment: API_KEY=secret123
   * const hasApiKey = EnvConfig.has('API_KEY'); // Returns: true
   * 
   * // Environment: EMPTY_VAR=
   * const hasEmpty = EnvConfig.has('EMPTY_VAR'); // Returns: false
   * 
   * const hasMissing = EnvConfig.has('MISSING_VAR'); // Returns: false
   * ```
   */
  static has(envKey: string): boolean {
    const value = process.env[envKey];
    return value !== undefined && value !== null && value.trim() !== '';
  }

  /**
   * Get all environment variables with a specific prefix
   * 
   * @param prefix - Prefix to filter by (e.g., 'TEST_')
   * @returns Object with filtered environment variables
   * 
   * @example
   * ```typescript
   * // Environment variables:
   * // TEST_API_KEY=secret
   * // TEST_TIMEOUT=5000
   * // TEST_DEBUG=true
   * // PROD_API_KEY=prod-secret
   * 
   * const testVars = EnvConfig.getByPrefix('TEST_');
   * // Returns: { 
   * //   TEST_API_KEY: 'secret', 
   * //   TEST_TIMEOUT: '5000', 
   * //   TEST_DEBUG: 'true' 
   * // }
   * 
   * // Get all database-related vars
   * const dbVars = EnvConfig.getByPrefix('DB_');
   * ```
   */
  static getByPrefix(prefix: string): Record<string, string> {
    const result: Record<string, string> = {};
    
    Object.keys(process.env).forEach(key => {
      if (key.startsWith(prefix)) {
        const value = process.env[key];
        if (value !== undefined) {
          result[key] = value;
        }
      }
    });
    
    return result;
  }

  // Private helper methods

  private static parseList(
    envKey: string, 
    fallback: string[], 
    options: Required<ParseOptions>
  ): ParseResult<string[]> {
    const value = process.env[envKey];
    
    if (!value) {
      return { success: false, value: fallback, error: 'Environment variable not found' };
    }

    try {
      const parsed = value
        .split(options.listDelimiter)
        .map(item => item.trim())
        .filter(item => item.length > 0);
      
      return { success: true, value: parsed, rawValue: value };
    } catch (error) {
      return { 
        success: false, 
        value: fallback, 
        error: `Failed to parse list: ${error}`,
        rawValue: value 
      };
    }
  }

  private static parseJSON<T>(
    envKey: string, 
    fallback: T, 
    options: Required<ParseOptions>
  ): ParseResult<T> {
    const value = process.env[envKey];
    
    if (!value) {
      return { success: false, value: fallback, error: 'Environment variable not found' };
    }

    try {
      // Handle common shell escaping issues
      let normalizedValue = value.trim();
      
      // Remove surrounding quotes if present
      if ((normalizedValue.startsWith('"') && normalizedValue.endsWith('"')) ||
          (normalizedValue.startsWith("'") && normalizedValue.endsWith("'"))) {
        normalizedValue = normalizedValue.slice(1, -1);
      }
      
      const parsed = JSON.parse(normalizedValue);
      return { success: true, value: parsed, rawValue: value };
    } catch (error) {
      return { 
        success: false, 
        value: fallback, 
        error: `Failed to parse JSON: ${error}`,
        rawValue: value 
      };
    }
  }

  private static parseJSONBase64<T>(
    envKey: string, 
    fallback: T, 
    options: Required<ParseOptions>
  ): ParseResult<T> {
    const value = process.env[envKey];
    
    if (!value) {
      return { success: false, value: fallback, error: 'Environment variable not found' };
    }

    try {
      // Decode Base64
      const decoded = Buffer.from(value.trim(), 'base64').toString('utf8');
      
      // Parse JSON
      const parsed = JSON.parse(decoded);
      return { success: true, value: parsed, rawValue: value };
    } catch (error) {
      return { 
        success: false, 
        value: fallback, 
        error: `Failed to decode/parse Base64 JSON: ${error}`,
        rawValue: value 
      };
    }
  }

  private static logParseError(
    type: string, 
    envKey: string, 
    error?: string, 
    rawValue?: string, 
    logDetails: boolean = false
  ): void {
    console.warn(`⚠️  EnvConfig: Failed to parse ${type} from '${envKey}'. Using fallback value.`);
    
    if (logDetails && error) {
      console.warn(`   Error: ${error}`);
      if (rawValue) {
        console.warn(`   Raw value: ${rawValue.substring(0, 200)}${rawValue.length > 200 ? '...' : ''}`);
      }
    }
  }
}

/**
 * Convenience export for common patterns
 * 
 * @example
 * ```typescript
 * // Easy access to common test data
 * const companies = TestEnv.getCompanies();
 * const addresses = TestEnv.getAddresses();
 * const brregId = TestEnv.getBrregSystemId();
 * 
 * // Check CI environment
 * if (TestEnv.isCI()) {
 *   console.log('Running in CI/CD environment');
 * }
 * 
 * // Get all test variables for debugging
 * console.log('Test vars:', TestEnv.getAllTestVars());
 * ```
 */
export const TestEnv = {
  /**
   * Get test company IDs as a list
   * 
   * @example
   * ```typescript
   * // Environment: TEST_COMPANIES_LIST=971277882,915933149,974652846
   * const companies = TestEnv.getCompanies();
   * // Returns: ['971277882', '915933149', '974652846']
   * 
   * // With fallback
   * const companies = TestEnv.getCompanies(['default-company']);
   * ```
   */
  getCompanies: (fallback: string[] = []) => 
    EnvConfig.getList('TEST_COMPANIES_LIST', fallback),

  /**
   * Get test addresses as JSON (tries both JSON and Base64 formats)
   * 
   * @example
   * ```typescript
   * // Environment: TEST_ADDRESSES_JSON=[{"street":"vestengkleiva 3","city":"asker"}]
   * const addresses = TestEnv.getAddresses();
   * // Returns: [{ street: "vestengkleiva 3", city: "asker" }]
   * ```
   */
  getAddresses: <T = any>(fallback: T[] = []) => 
    EnvConfig.getJSON('TEST_ADDRESSES_JSON', fallback) || 
    EnvConfig.getJSONBase64('TEST_ADDRESSES_B64', fallback),

  /**
   * Get BRREG system ID
   * 
   * @example
   * ```typescript
   * // Environment: BRREG_SYSTEM_ID=SYS1234567
   * const brregId = TestEnv.getBrregSystemId();
   * // Returns: 'SYS1234567'
   * ```
   */
  getBrregSystemId: (fallback: string = 'SYS1234567') => 
    EnvConfig.getString('BRREG_SYSTEM_ID', fallback),

  /**
   * Get API timeout in milliseconds
   * 
   * @example
   * ```typescript
   * // Environment: API_TIMEOUT=5000
   * const timeout = TestEnv.getApiTimeout();
   * // Returns: 5000
   * ```
   */
  getApiTimeout: (fallback: number = 5000) => 
    EnvConfig.getNumber('API_TIMEOUT', fallback),

  /**
   * Check if running in CI/CD environment
   * 
   * @example
   * ```typescript
   * if (TestEnv.isCI()) {
   *   console.log('Running in CI - using production endpoints');
   * } else {
   *   console.log('Running locally - using development endpoints');
   * }
   * ```
   */
  isCI: () => 
    EnvConfig.getBoolean('CI', false) || 
    EnvConfig.has('GITHUB_ACTIONS') || 
    EnvConfig.has('GITLAB_CI') || 
    EnvConfig.has('JENKINS_URL'),

  /**
   * Get all test-related environment variables
   * 
   * @example
   * ```typescript
   * // Debug: see all test configuration
   * const testVars = TestEnv.getAllTestVars();
   * console.log('Test configuration:', testVars);
   * ```
   */
  getAllTestVars: () => 
    EnvConfig.getByPrefix('TEST_')
};

// Export default for convenience
export default EnvConfig;