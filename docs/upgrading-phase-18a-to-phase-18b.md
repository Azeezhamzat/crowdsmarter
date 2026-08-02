# Upgrade to Phase 18B

Phase 18B adds the `platform_admin` Django app and two migrations. The release installer validates an isolated backend and frontend candidate before changing the live source.

The live upgrade sequence is:

1. verify the release archive;
2. build and test isolated backend and frontend candidates;
3. create a complete source backup and PostgreSQL logical backup;
4. stop application processes while leaving PostgreSQL and Redis volumes intact;
5. atomically replace the source tree while preserving `.env`;
6. build the canonical images and apply migrations;
7. grant `hello@crowdsmarter.com` explicit platform authority when that account exists;
8. verify health, routes, migration state, and tenant-governance invariants.

On a post-migration failure, the installer restores both the previous source tree and the PostgreSQL backup. It never removes Docker volumes.
