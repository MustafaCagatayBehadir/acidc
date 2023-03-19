CREATE TABLE acidcvrfs (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    enforcement VARCHAR NOT NULL,
    vrf_type VARCHAR NOT NULL
);
