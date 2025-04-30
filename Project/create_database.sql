CREATE SCHEMA IF NOT EXISTS airport;

CREATE TABLE IF NOT EXISTS airport.employee (
    ssn VARCHAR(9) PRIMARY KEY,
    name TEXT,
    password TEXT,
    address TEXT,
    phone TEXT,
    salary NUMERIC(100,2)
);

CREATE TABLE IF NOT EXISTS airport.faa_test (
    test_number INT PRIMARY KEY,
    name TEXT,
    max_score INT
);

CREATE TABLE IF NOT EXISTS airport.manager (
    ssn VARCHAR(9) PRIMARY KEY,
    FOREIGN KEY (ssn) REFERENCES airport.employee(ssn)
);

CREATE TABLE IF NOT EXISTS airport.technician (
    ssn VARCHAR(9) PRIMARY KEY,
    FOREIGN KEY (ssn) REFERENCES airport.employee(ssn)
);

CREATE TABLE IF NOT EXISTS airport.atc (
    ssn VARCHAR(9) PRIMARY KEY,
    FOREIGN KEY (ssn) REFERENCES airport.employee(ssn)
);

CREATE TABLE IF NOT EXISTS airport.airplane_model (
    model_number TEXT PRIMARY KEY,
    capacity INT,
    weight INT
);

CREATE TABLE IF NOT EXISTS airport.expert (
    ssn VARCHAR(9),
    model_number TEXT,
    PRIMARY KEY (ssn, model_number),
    FOREIGN KEY (ssn) REFERENCES airport.employee(ssn),
    FOREIGN KEY (model_number) REFERENCES airport.airplane_model(model_number)
);

CREATE TABLE IF NOT EXISTS airport.airplane (
    reg_number TEXT PRIMARY KEY,
    model_number TEXT,
    FOREIGN KEY (model_number) REFERENCES airport.airplane_model(model_number)
);

CREATE TABLE IF NOT EXISTS airport.test_event (
    test_number INT,
    ssn VARCHAR(9),
    reg_number TEXT,
    date DATE,
    duration INTERVAL,
    score INT,
    PRIMARY KEY (test_number, ssn, reg_number, date),
    FOREIGN KEY (test_number) REFERENCES airport.faa_test(test_number),
    FOREIGN KEY (ssn) REFERENCES airport.employee(ssn),
    FOREIGN KEY (reg_number) REFERENCES airport.airplane(reg_number)
);

CREATE OR REPLACE FUNCTION airport.check_test_event_score()
RETURNS TRIGGER AS $$
DECLARE
    max_allowed_score INT;
BEGIN
    SELECT max_score INTO max_allowed_score
    FROM airport.faa_test
    WHERE test_number = NEW.test_number;

    IF max_allowed_score IS NULL THEN
        RAISE EXCEPTION 'FAA Test number % does not exist in faa_test.', NEW.test_number;
    END IF;

    IF NEW.score > max_allowed_score THEN
        RAISE EXCEPTION 'Score % exceeds maximum allowed score of % for test %.', NEW.score, max_allowed_score, NEW.test_number;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_test_event_score
BEFORE INSERT ON airport.test_event
FOR EACH ROW
EXECUTE FUNCTION airport.check_test_event_score();

