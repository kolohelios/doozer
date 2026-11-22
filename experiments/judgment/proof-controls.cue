package judgment

// Post-hoc constructive countermodels, not extracted facts or world evidence.
// These separate world variables from local knowledge and source-version acts.
proofControls: {
	status: "manually typed logical controls; not a natural-language extraction result"
	dateCountermodel: {
		world: exception: effectiveDate: "2027-05-16"
	} & {
		world: exception: effectiveDate:                    !="2027-05-14"
		epistemic: exception: effectiveDateEstablishedHere: false
	}
	withdrawalCountermodel: {
		world: "meadow-april-10": normalCatalogAvailable: true
	} & {
		sourceActs: "meadow-april-10": priorAssuranceWithdrawn:    true
		epistemic: "meadow-april-10": availabilityEstablishedHere: false
	}
	otherScopeAllowsP: {
		world: "production-west": readsQuietMail: true
	} & {
		world: "production-east": readsQuietMail: true
	}
	otherScopeAllowsNotP: {
		world: "production-west": readsQuietMail: false
	} & {
		world: "production-east": readsQuietMail: true
	}
	// Keep assertions separate. Their pair is incompatible, not an accepted KB.
	accessTarget: world: "meadow-april-10": normalCatalogAvailable:     true
	accessOpposition: world: "meadow-april-10": normalCatalogAvailable: false
	dateTarget: world: exception: effectiveDate:                        "2027-05-16"
	dateAlternative: world: exception: effectiveDate:                   "2027-05-17"
}
