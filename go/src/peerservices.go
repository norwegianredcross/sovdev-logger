package sovdevlogger

// PeerServices holds the peer service mappings with type-safe constants
type PeerServices struct {
	// INTERNAL is auto-generated and equals the service name
	INTERNAL string
	// Mappings contains the original peer service definitions plus INTERNAL
	Mappings map[string]string
	// constants holds the defined peer service constant names
	constants map[string]string
}

// Get returns the constant name for a peer service
// This provides type-safe access to peer service identifiers
func (ps *PeerServices) Get(name string) string {
	if name == "INTERNAL" {
		return ps.INTERNAL
	}
	if _, ok := ps.constants[name]; ok {
		return name
	}
	return name // Return as-is if not found
}

// CreatePeerServices creates a PeerServices instance with INTERNAL auto-generated
//
// Example:
//
//	peerServices := CreatePeerServices(map[string]string{
//	    "BRREG": "SYS1234567",  // External system
//	    "ALTINN": "SYS7654321", // External system
//	})
//	// INTERNAL is auto-generated = "INTERNAL"
//	// peerServices.Mappings contains all mappings including INTERNAL
func CreatePeerServices(definitions map[string]string) *PeerServices {
	// Create mappings with INTERNAL pre-populated
	mappings := make(map[string]string)

	// Copy all definitions
	for k, v := range definitions {
		mappings[k] = v
	}

	// Create constants map (stores the constant names, not the IDs)
	constants := make(map[string]string)
	for k := range definitions {
		constants[k] = k  // Store the constant name itself
	}

	return &PeerServices{
		INTERNAL:  "INTERNAL", // Always "INTERNAL" string
		Mappings:  mappings,
		constants: constants,
	}
}
