package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	sovdevlogger "github.com/redcross-public/sovdev-logger/go/src"
)

// CompanyData represents the response from BRREG API
type CompanyData struct {
	Organisasjonsnummer string `json:"organisasjonsnummer"`
	Navn                string `json:"navn"`
	Organisasjonsform   *struct {
		Kode        string `json:"kode"`
		Beskrivelse string `json:"beskrivelse"`
	} `json:"organisasjonsform"`
}

// PEER_SERVICES defines external system mappings
var PEER_SERVICES *sovdevlogger.PeerServices

func init() {
	PEER_SERVICES = sovdevlogger.CreatePeerServices(map[string]string{
		"BRREG": "SYS1234567", // Norwegian company registry
	})
}

// fetchCompanyData fetches company information from BRREG API
func fetchCompanyData(orgNumber string) (*CompanyData, error) {
	url := fmt.Sprintf("https://data.brreg.no/enhetsregisteret/api/enheter/%s", orgNumber)

	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	var data CompanyData
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}

	return &data, nil
}

// lookupCompany performs a single company lookup with transaction correlation
func lookupCompany(orgNumber string) error {
	const FUNCTIONNAME = "lookupCompany"

	// Prepare input
	input := map[string]interface{}{
		"organisasjonsnummer": orgNumber,
	}

	// Generate trace ID for correlation
	traceID := sovdevlogger.SovdevGenerateTraceID()

	// LOG #1: Transaction Start
	sovdevlogger.SovdevLog(
		sovdevlogger.SOVDEV_LOGLEVELS.INFO,
		FUNCTIONNAME,
		fmt.Sprintf("Looking up company %s", orgNumber),
		PEER_SERVICES.Mappings["BRREG"],
		input,
		nil,
		nil,
		traceID,
	)

	// Fetch company data
	companyData, err := fetchCompanyData(orgNumber)
	if err != nil {
		// LOG #2: Transaction Error
		sovdevlogger.SovdevLog(
			sovdevlogger.SOVDEV_LOGLEVELS.ERROR,
			FUNCTIONNAME,
			fmt.Sprintf("Failed to lookup company %s", orgNumber),
			PEER_SERVICES.Mappings["BRREG"],
			input,
			nil,
			err,
			traceID,
		)
		return err
	}

	// Prepare response
	response := map[string]interface{}{
		"navn": companyData.Navn,
	}
	if companyData.Organisasjonsform != nil {
		response["organisasjonsform"] = companyData.Organisasjonsform.Beskrivelse
	}

	// LOG #3: Transaction Success
	sovdevlogger.SovdevLog(
		sovdevlogger.SOVDEV_LOGLEVELS.INFO,
		FUNCTIONNAME,
		fmt.Sprintf("Company found: %s", companyData.Navn),
		PEER_SERVICES.Mappings["BRREG"],
		input,
		response,
		nil,
		traceID,
	)

	return nil
}

// batchLookup processes multiple companies with job tracking
func batchLookup(orgNumbers []string) {
	const FUNCTIONNAME = "batchLookup"
	const JOBNAME = "CompanyLookupBatch"

	// LOG #1: Job Started
	sovdevlogger.SovdevLogJobStatus(
		sovdevlogger.SOVDEV_LOGLEVELS.INFO,
		FUNCTIONNAME,
		JOBNAME,
		"Started",
		PEER_SERVICES.INTERNAL,
		map[string]interface{}{
			"totalCompanies": len(orgNumbers),
		},
		"",
	)

	successful := 0
	failed := 0

	// Process each company
	for i, orgNumber := range orgNumbers {
		// LOG #2-5: Progress Tracking
		sovdevlogger.SovdevLogJobProgress(
			sovdevlogger.SOVDEV_LOGLEVELS.INFO,
			FUNCTIONNAME,
			orgNumber,
			i+1,
			len(orgNumbers),
			PEER_SERVICES.Mappings["BRREG"],
			map[string]interface{}{
				"organisasjonsnummer": orgNumber,
			},
			"",
		)

		// Lookup company
		if err := lookupCompany(orgNumber); err != nil {
			failed++

			// LOG: Batch Item Error
			sovdevlogger.SovdevLog(
				sovdevlogger.SOVDEV_LOGLEVELS.ERROR,
				FUNCTIONNAME,
				fmt.Sprintf("Batch item %d failed", i+1),
				PEER_SERVICES.Mappings["BRREG"],
				map[string]interface{}{
					"organisasjonsnummer": orgNumber,
					"itemNumber":          i + 1,
				},
				nil,
				err,
				"",
			)
		} else {
			successful++
		}

		// Small delay to avoid rate limits
		time.Sleep(100 * time.Millisecond)
	}

	// LOG #6: Job Completed
	sovdevlogger.SovdevLogJobStatus(
		sovdevlogger.SOVDEV_LOGLEVELS.INFO,
		FUNCTIONNAME,
		JOBNAME,
		"Completed",
		PEER_SERVICES.INTERNAL,
		map[string]interface{}{
			"totalCompanies": len(orgNumbers),
			"successful":     successful,
			"failed":         failed,
			"successRate":    fmt.Sprintf("%d%%", (successful*100)/len(orgNumbers)),
		},
		"",
	)
}

func main() {
	const FUNCTIONNAME = "main"

	// Initialize logger
	serviceName := os.Getenv("OTEL_SERVICE_NAME")
	if serviceName == "" {
		serviceName = "company-lookup-service"
	}

	if err := sovdevlogger.SovdevInitialize(
		serviceName,
		"1.0.0",
		PEER_SERVICES.Mappings,
	); err != nil {
		fmt.Printf("Failed to initialize logger: %v\n", err)
		os.Exit(1)
	}

	// LOG #1: Application Started
	sovdevlogger.SovdevLog(
		sovdevlogger.SOVDEV_LOGLEVELS.INFO,
		FUNCTIONNAME,
		"Company Lookup Service started",
		PEER_SERVICES.INTERNAL,
		nil,
		nil,
		nil,
		"",
	)

	// Test data - MUST match specification
	companies := []string{
		"971277882", // Company 1: Valid
		"915933149", // Company 2: Valid
		"974652846", // Company 3: INVALID (intentional)
		"916201478", // Company 4: Valid
	}

	// Process batch
	batchLookup(companies)

	// LOG #2: Application Finished
	sovdevlogger.SovdevLog(
		sovdevlogger.SOVDEV_LOGLEVELS.INFO,
		FUNCTIONNAME,
		"Company Lookup Service finished",
		PEER_SERVICES.INTERNAL,
		nil,
		nil,
		nil,
		"",
	)

	// CRITICAL: Flush telemetry before exit
	if err := sovdevlogger.SovdevFlush(); err != nil {
		fmt.Printf("⚠️  Flush warning: %v\n", err)
	}
}
