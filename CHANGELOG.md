# v0.4.1
- Upgrade `taxonomic-profile-translator` to v0.4.1, which replaces `taxonkit` with a bundled SQLite database
- Drop the `TAXONKIT_DB` and `TAXONKIT_PATH` environment variables; only `TPT_DB_PATH` is read
- Unclassified rows of generic profiles (`-1`, `unassigned`, `unclassified`) are now kept, so the `unclassified` rows of the community summary reflect them

# v0.4.0
- Look up reference data through a byte-offset index instead of scanning the whole file
- Add `sumtraits-index` for building the reference data indexes
- Document the `TPT_DB_PATH`, `TAXONKIT_DB` and `TAXONKIT_PATH` environment variables

# v0.3.0
- Change the community output format

# v0.2.3
- Performance improvements
- remove retries on clowm

# v0.2.2
- Added end to end testing

# v0.2.1
- Initial release
