<!--
SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# mo-arbor
OS2mo integration that syncs organisation units from CSV files, such as
[SOR](https://sundhedsdatastyrelsen.dk/data-og-registre/nationale-sundhedsregistre/sundhedsvaesenets-organisationsregister).


## Usage
```
docker compose up -d --build
```
Configuration is done through environment variables. Integration-specific
options are defined in [mo_arbor/config.py](mo_arbor/config.py). FastRAMQPI's
options (MO URL, authentication, logging, etc.) are nested under `FASTRAMQPI`
and set using `__` as delimiter, e.g. `FASTRAMQPI__MO_URL`. See
[docker-compose.yml](docker-compose.yml) for a working example.

### Code systems
A code system, such as SOR, is a tree of codes, and each code becomes an org
unit in MO. The code systems to ingest are set in `CODE_SYSTEMS` as a JSON
list of names the integration knows, e.g. `["sor", "okosted"]`.

The supplier uploads dumps to MO's `EXPORTS` file store. A dump's file name
ends in the code system's name and the time of the dump, after any prefix,
e.g. `customer_sor_20261016_094303.csv`. A dump uploaded again under the
same name, such as one the supplier fixed, is read again. A dump is a CSV file
as described in the supplier's spec
"Kodesystemfiler til OS2mo"
([#69230](https://redmine.magenta.dk/issues/69230)):
- The rows without a `kode_parent` are roots, which become the top units in
  MO, or go under the code system's root unit (see below).
- Every row must have a `type` and a `niveau`.
- A unit is valid from `gyldig_fra` to `gyldig_til`, cut to its parent's
  validity. A unit that is gone from the dump is terminated.
- A file with other columns is rejected.
- SOR codes must be valid SOR IDs, which catches codes damaged by Excel.

### Ingest
A cron job calls `POST /ingest`. For each code system, it compares the newest
dump with the last ingested one, and sends an `org_unit` event for every unit
that was added, changed or removed. Dumps in between are skipped. Event
priorities make MO hand out parents' events before their children's, and
terminations last, children first.

If the last ingested dump is not known, because there is none, it has been
overwritten since, or the database was lost, the newest dump is compared with
the code system's units in MO instead: a unit only in the dump is added, a
unit in both is sent as changed, and a unit only in MO is terminated.

Ingest skips a code system and logs an error when:
- the newest dump is invalid,
- it would terminate more than `MAX_TERMINATIONS` units, 10 by default
  (override with `?force=true`).

The other code systems are still ingested, but the request fails, so the cron
job fails.

`?dry_run=true` shows what would be sent without sending it, and
`?code_system=<name>` ingests only that code system.

### Event handler
Each `org_unit` event makes the org unit with that code match the code
system's newest dump: it is created, updated, reopened or terminated as
needed. The newest dump is read rather than the one the event came from, so an
old or repeated event never writes outdated data.

Changes take effect from the dump's date, or from the unit's start if that is
later. A unit that is gone from the dump is terminated with the day before
the dump as its last day, or from its start if it has not started, so it is
never active. If it comes back in a later dump, and its `gyldig_fra` is on or
before the day MO ended it, it is active again from that day, so it has no
gap. Otherwise it is active again from the later of the dump's date and its
`gyldig_fra`.

A unit's UUID is derived from its code and the code system's `name`, so the
same code in two code systems is two units. Never rename a code system, as
MO's existing units would become unreachable.

SOR's dump has a single root, which is at the top of MO. Økosted's dumps have
several roots, its legal entities, which go under a root unit the integration
makes before it sends the first events: "Økosted", of type `region` and from
1900-01-01. The `region` class must exist in MO, or Økosted is not ingested.

The type and level are the classes in the `org_unit_type` and
`org_unit_level` facets whose user_key is the row's `type` and `niveau`. If a
class does not exist, the event fails and is retried until someone creates it.


## Sundhedsvæsenets Organisationsregister (SOR)
SOR registers organisation and address data, as well as location numbers, for
the Danish healthcare sector. It is owned and operated by Sundhedsdatastyrelsen.


## Development
The integration is a [FastRAMQPI](https://git.magenta.dk/rammearkitektur/FastRAMQPI)
application using OS2mo's GraphQL event system. FastRAMQPI declares event
listeners against MO; MO's GraphQL fetcher polls events and HTTP-POSTs them to
FastAPI routes on this integration. Listeners are configured in
[mo_arbor/app.py](mo_arbor/app.py) and the handlers live in
[mo_arbor/events.py](mo_arbor/events.py).

The development environment connects to the `os2mo_default` network, so OS2mo
must be running locally.

### Running the tests
Unit tests:
```
poetry run pytest -m "not integration_test"
```
Integration tests run against the local OS2mo, from inside the container. They
reset OS2mo's database before each test, so everything in it is lost:
```
docker compose run --rm mo-arbor pytest -m integration_test
```

### Updating the GraphQL client
The GraphQL client in `mo_arbor/autogenerated_graphql_client` MUST NOT be
edited manually. It is generated from `schema.graphql` and the operations in
`queries/`, using `ariadne-codegen`. Operations used only by the tests are in
`queries/testing.graphql`. To regenerate after changing queries:
```
curl -O http://localhost:5000/graphql/v30/schema.graphql
rm -rf mo_arbor/autogenerated_graphql_client/
poetry run ariadne-codegen client
poetry run pre-commit run --files mo_arbor/autogenerated_graphql_client/*
```


## Versioning
This project uses [Semantic Versioning](https://semver.org/) with the following
strategy:
- MAJOR: Incompatible API changes.
- MINOR: Backwards-compatible updates and functionality.
- PATCH: Backwards-compatible bug fixes.


## Authors
Magenta ApS <https://magenta.dk>


## License
- This project: [MPL-2.0](LICENSES/MPL-2.0.txt)

This project uses [REUSE](https://reuse.software) for licensing. All licenses
can be found in the [LICENSES folder](LICENSES/) of the project.
