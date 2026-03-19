from ..dao.enums import JobPriority, OutputFormat, UserTier

##
# For Job creation
##

JOB_PRIORITY_LEVEL = {
    UserTier.BASIC: JobPriority.LOW,
    UserTier.PREMIUM: JobPriority.NORMAL,
    UserTier.VIP: JobPriority.HIGH,
}

##
# For JobRunner service
##
SLOT_TIMEOUT_IN_SECOND = {
    UserTier.BASIC: 60,
    UserTier.PREMIUM: 5 * 60,
    UserTier.VIP: 2 * 60 * 60,
}

ENABLED_FORMATS = {
    UserTier.BASIC: set([
        OutputFormat.epub,
    ]),
    UserTier.PREMIUM: set([
        OutputFormat.json,
        OutputFormat.epub,
        OutputFormat.text,
        OutputFormat.mobi,
        OutputFormat.docx,
        OutputFormat.fb2,
        OutputFormat.azw3,
        OutputFormat.lit,
        OutputFormat.pdb,
        OutputFormat.tcr,
    ]),
    UserTier.VIP: set(OutputFormat),
}
