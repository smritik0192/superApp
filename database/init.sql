CREATE TABLE rooms (
    room_id TEXT PRIMARY KEY,
    name TEXT,
    status TEXT,
    capacity INTEGER
);

CREATE TABLE facility_mapping (
    facility_id INTEGER PRIMARY KEY,
    facility_name TEXT
);


CREATE TABLE room_facility_mappings (
    room_id TEXT,
    facility_id INTEGER,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    FOREIGN KEY (facility_id) REFERENCES facility_mapping(facility_id),
    PRIMARY KEY (room_id, facility_id)
);

INSERT INTO rooms (room_id, name, capacity)
VALUES 
    ('room1', 'Vista Room', 8),
    ('room2', 'Garden Suite',  4),
    ('room3', 'Skyline Boardroom',  12),
    ('room4', 'Corner Office', 3);

INSERT INTO facility_mapping (facility_id, facility_name)
VALUES
    (1, 'projector'),
    (2, 'video conferencing'),
    (3, 'whiteboard'),
    (4, 'audio system'),
    (5, 'privacy screen'),
    (6, 'catering service'),
    (7, 'coffee machine');


INSERT INTO room_facility_mappings (room_id, facility_id)
VALUES
    ('room1', 1),
    ('room1', 2),
    ('room1', 3),
    ('room2', 4),
    ('room2', 5),
    ('room3', 1),
    ('room3', 2),
    ('room3', 3),
    ('room3', 6),
    ('room4', 7),
    ('room4', 5)
;

CREATE TABLE bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_date TEXT NOT NULL,
    to_date TEXT NOT NULL,
    room_id TEXT,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE parking_lot (
    parking_id INTEGER PRIMARY KEY,
    parking_number INTEGER,
    status TEXT NOT NULL,
    vehicle_id TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id)
);

CREATE TABLE vehicle (
    vehicle_id TEXT PRIMARY KEY,
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    parking_id INTEGER,
    FOREIGN KEY (parking_id) REFERENCES parking_lot(parking_id)
);


INSERT INTO parking_lot (parking_id, parking_number,status)
VALUES 
    (1,101, 'Unreserved'),
    (2, 102, 'Unreserved'),
    (3, 103, 'Unreserved'),
    (4, 104, 'Unreserved'),
    (5, 105, 'Unreserved'),
    (6, 106, 'Unreserved'),
    (7, 107,'Unreserved'),
    (8, 108,'Unreserved'),
    (9, 109,'Unreserved'),
    (10,110, 'Unreserved');



