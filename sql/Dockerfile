FROM postgres:16-alpine

# Set environment variables
ENV POSTGRES_DB=drone_detection
ENV POSTGRES_USER=droneuser
ENV POSTGRES_PASSWORD=dronepass

# Copy initialization script
COPY init.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432
