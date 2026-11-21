package repopolicy

#RepoPolicy & {
	defaultBranch: "main"
	merge: {
		rebase:              true
		merge:               false
		squash:              false
		deleteBranchOnMerge: true
		autoMerge:           false
	}
	issues: true
	handAuthoredWorkflows: ["validate.yml"]
}
