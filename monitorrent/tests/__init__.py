import vcr

test_vcr = vcr.VCR(
    cassette_library_dir="cassettes",
    record_mode="once"
)

use_vcr = test_vcr.use_cassette
