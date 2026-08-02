# Upgrade Phase 3.0.1 to Phase 3.1 on Linux

This upgrade preserves your existing account, password, organisation, decisions, and database. Use the supplied one-terminal upgrade script rather than combining ZIP files.

## Before starting

Download both files to `~/Downloads`:

- `crowdsmarter-phase3.1.zip`
- `upgrade-crowdsmarter-to-phase3.1.sh`

Your current installation should be at `~/Downloads/crowdsmarter` and contain its existing `.env` file.

## Run

```bash
bash ~/Downloads/upgrade-crowdsmarter-to-phase3.1.sh
```

If Docker reports permission denied:

```bash
newgrp docker
bash ~/Downloads/upgrade-crowdsmarter-to-phase3.1.sh
```

The script stops the application, creates a PostgreSQL backup, preserves the old source folder, extracts Phase 3.1, carries forward `.env`, builds the images, applies the invitation migration, runs Django checks, and starts the application.

Open `http://localhost:5173` and use your existing login.

## Invite a local test person

1. Open the organisation governance screen.
2. Enter a different email address under **Invite a person**.
3. Choose a role and select **Send invitation**.
4. Copy the development link displayed on screen.
5. Open a private/incognito browser window and paste the link.
6. The invited person enters their name and chooses a password.

Console email also appears in backend logs:

```bash
docker compose logs --tail=100 backend
```

## Production configuration

Before inviting people outside your machine, configure SMTP and set:

```text
FRONTEND_BASE_URL=https://your-domain.example
INVITATION_EXPIRY_HOURS=168
```

Never run `docker compose down -v`; `-v` deletes the database volume.
