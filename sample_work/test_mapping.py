test_to_kind = {
	"document-link/category[@code='B04'] exists?": "org-document",
	"document-link/category[@code='B01'] exists?": "org-document",
	"document-link/category[@code='B06'] exists?": "org-document",
	"document-link/category[@code='A05'] exists (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01))?": "document",
	"document-link/category[@code='A06'] or document-link/category[@code='A11'] exists (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01))?": "document",
	"document-link/category[@code='A07'] exists (if activity-status/@code is at least 3)?": "document",
	"document-link/category[@code='A09'] exists (if activity-status/@code is at least 2)?": "document",
	"document-link/category[@code='A02'] or description[@type='2'] exists (if activity-status/@code is at least 2)?": "document",
	"document-link/category[@code='B05'] exists?": "org-document",
	"document-link/category[@code='B02'] exists?": "org-document",
	"document-link/category[@code='A10'] exists (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01))?": "document",
	"document-link/category[@code='A04'] exists (if activity-status/@code is at least 2)?": "document",
	"document-link/category[@code='A08'] exists (if activity-status/@code is at least 2)?": "document",
	"conditions exists (if activity-status/@code is at least 2)?": "conditions",
	"result exists (if activity-status/@code is at least 2)?": "results",
	"location exists (if activity-status/@code is at least 2 and recipient-region/@code is not 998)?": "location",
	"location/coordinates exists (if activity-status/@code is at least 2 and recipient-region/@code is not 998)?": "location"
}
