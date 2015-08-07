import os
import vcr

test_vcr = vcr.VCR(
    cassette_library_dir=os.path.join(os.path.dirname(__file__), "cassettes"),
    record_mode="once"
)

use_vcr = test_vcr.use_cassette
