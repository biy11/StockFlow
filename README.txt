To back up the database before push to Git:

pg_dump -U bilal -h localhost -F p stockflow_db > stockflow_dump.sql


To pull and restore the database:

psql -U bilal -h localhost stockflow_db < stockflow_dump.sql

I have added a droplet service from DigitalOcean