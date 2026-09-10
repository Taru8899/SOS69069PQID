"""All PQID user-visible strings and style tokens."""
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

FONT_TITLE = dp(20)
FONT_SECTION = dp(16)
FONT_BODY = dp(14)
FONT_SMALL = dp(12)
FONT_NAV = dp(11)

TEXT = get_color_from_hex("#f1f5f9")
TEXT_SEC = get_color_from_hex("#cbd5e1")
TEXT_MUTED = get_color_from_hex("#94a3b8")
GREEN = get_color_from_hex("#22c55e")
GREEN_BR = get_color_from_hex("#4ade80")
BLUE = get_color_from_hex("#3b82f6")
BLUE_SOFT = get_color_from_hex("#38bdf8")
YELLOW = get_color_from_hex("#eab308")
ORANGE = get_color_from_hex("#f97316")
DANGER = get_color_from_hex("#ef4444")
INPUT_BG = get_color_from_hex("#1e293b")

LOADING_LINE1 = "Loading ..."
LOADING_LINE2 = "SOS 69069 PQID"
LOADING_LINE3 = "Activity and Signatures"
HOME_TITLE = "HUMAN IDENTITY"
HOME_SUB = "Human to human records section."
BTN_MY_IDENTITY = "MY IDENTITY"
BTN_MY_RECORDS = "MY RECORDS"
BTN_VERIFY = "VERIFY PERSON"
BTN_ATTEST = "ATTESTATIONS"
BTN_CHAIN = "CHAIN SUBMIT"
IDENTITY_TITLE = "SOS HUMAN IDENTITY"
IDENTITY_CREATE = "CREATE IDENTITY"
IDENTITY_EXISTS = "Identity already on this device.\nClear human data on PQID to reset."
IDENTITY_HINT = "Private key never leaves this device.\nShare only fingerprint / public card."
VERIFY_TITLE = "VERIFY PERSON (face-to-face)"
VERIFY_HINT = "Paste their public identity JSON.\nCompare fingerprint in person, then Accept."
VERIFY_PARSE = "PARSE"
VERIFY_ACCEPT = "ACCEPT (HUMAN CHECK DONE)"
RECORDS_TITLE = "MY RECORDS (bearer objects)"
RECORDS_CREATE = "CREATE PRESENCE RECORD"
RECORDS_EMPTY = "No local records yet."
ATTEST_TITLE = "ATTESTATIONS"
ATTEST_HINT = "Mutual attestation (v0): store acceptances locally."
CHAIN_TITLE = "CHAIN COMMITMENT"
CHAIN_HINT = "Submit record hash with gas payer when available."
PQID_CLEAR = "CLEAR HUMAN DATA"
PQID_LOGOUT = "LOGOUT HUMAN SESSION"
