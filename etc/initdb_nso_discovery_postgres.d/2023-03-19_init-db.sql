CREATE TABLE acidcvrfs (
    id SERIAL PRIMARY KEY,
    fabric VARCHAR NOT NULL,
    tenant VARCHAR NOT NULL,
    vrf_name VARCHAR NOT NULL,
    vrf_description VARCHAR NOT NULL,
    enforcement VARCHAR NOT NULL
);
