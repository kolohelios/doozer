package judgment

#Text: string & !=""
#Source: {
	id:       string & =~"^d[0-9]+$"
	kind:     "document" | "conversation" | "observation"
	saidAt:   #Text
	text:     #Text
	replyTo?: string
	origin?:  #Text
	derivedFrom?: [...string]
}
#Variant: {reference: "pass" | "fail" | "uncertain", reason: #Text, extra: [#Source, ...#Source]}
families: [string]: {candidate: #Text, base: [...#Source], variants: [string]: #Variant}
