import os

cron_sced = os.getenv("CRON_SCHEDULE", "0 * * * *")

print(f"CRON SCHEDULE: {cron_sced}")
with open("/src/docker/default_cron", 'w') as f:
    f.write(str(cron_sced) + " /src/docker/run.sh")
