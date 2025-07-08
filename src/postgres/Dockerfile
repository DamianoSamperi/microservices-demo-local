FROM ankane/pgvector
COPY ./postgres-init/init.sql /docker-entrypoint-initdb.d/
COPY ./postgres-init/products.sql /docker-entrypoint-initdb.d/

