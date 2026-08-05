import os, struct
# Windows minidump - we can at least get the module list from the header
# But minidumps are complex. Let us instead check the WER (Windows Error Reporting) for the crash reason.
# Alternatively check the Application event log for the crash.
import subprocess
# Use PowerShell to read the most recent Application event log entries for CreationKit
