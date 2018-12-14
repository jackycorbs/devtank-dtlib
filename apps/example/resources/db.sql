BEGIN TRANSACTION;
CREATE TABLE "file_store_protocols" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	TEXT NOT NULL
);
CREATE TABLE "file_stores" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"protocol_id"	INTEGER NOT NULL,
	"server_name"	VARCHAR(255) NOT NULL,
	"base_folder"	TEXT NOT NULL,
	"is_writable"	INTEGER,
	FOREIGN KEY("protocol_id") REFERENCES "file_store_protocols" ("id")
);
CREATE TABLE "files" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"filename"	VARCHAR(255) NOT NULL,
	"file_store_id"	INTEGER NOT NULL,
	"size"	INTEGER NOT NULL,
	"modified_date"	BIGINT NOT NULL,
	"insert_time"	BIGINT NOT NULL,
	FOREIGN KEY("file_store_id") REFERENCES "file_stores" ("id")
);
CREATE TABLE "values" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	VARCHAR(255) NOT NULL,
	"value_text"	TEXT,
	"value_int"	INTEGER,
	"value_real"	REAL,
	"value_file_id"	INTEGER,
	"parent_id"	INTEGER,
	"valid_from"	BIGINT NOT NULL,
	"valid_to"	BIGINT,
	FOREIGN KEY("value_file_id") REFERENCES "files" ("id")
);
CREATE TABLE "tests" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"file_id"	INTEGER NOT NULL,
	"valid_from"	BIGINT NOT NULL,
	"valid_to"	BIGINT,
	FOREIGN KEY("file_id") REFERENCES "files" ("id")
);
CREATE TABLE "test_groups" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	VARCHAR(255) NOT NULL,
	"description"	TEXT NOT NULL,
	"valid_from"	BIGINT NOT NULL,
	"valid_to"	BIGINT
);
CREATE TABLE "test_group_entries" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	VARCHAR(255),
	"test_group_id"	INTEGER NOT NULL,
	"test_id"	INTEGER NOT NULL,
	"valid_from"	BIGINT NOT NULL,
	"valid_to"	BIGINT,
	"order_position"	INTEGER NOT NULL,
	"duration" INTEGER,
	FOREIGN KEY("test_group_id") REFERENCES "test_groups" ("id"),
	FOREIGN KEY("test_id") REFERENCES "tests" ("id")
);
CREATE TABLE "test_group_entry_properties" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"group_entry_id"	INTEGER NOT NULL,
	"value_id"	INTEGER NOT NULL,
	FOREIGN KEY("group_entry_id") REFERENCES "test_group_entries" ("id"),
	FOREIGN KEY("value_id") REFERENCES "values" ("id")
);
CREATE TABLE "example_devs" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"uid"	VARCHAR(255),
	"serial_number"	VARCHAR(255)
);
CREATE TABLE "test_group_results" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"group_id"	INTEGER NOT NULL,
	"time_of_tests"	BIGINT NOT NULL,
	FOREIGN KEY("group_id") REFERENCES "test_groups" ("id")
);
CREATE TABLE "example_dev_test_results" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"example_dev_id"	INTEGER NOT NULL,
	"group_entry_id"	INTEGER,
	"pass_fail"	INTEGER NOT NULL,
	"output_file_id"	INTEGER,
	"log_file_id"	INTEGER,
	"group_result_id" INTEGER NOT NULL,
	FOREIGN KEY("example_dev_id") REFERENCES "example_devs" ("id"),
	FOREIGN KEY("group_entry_id") REFERENCES "test_group_entries" ("id"),
	FOREIGN KEY("output_file_id") REFERENCES "files" ("id"),
	FOREIGN KEY("log_file_id") REFERENCES "files" ("id"),
	FOREIGN KEY("group_result_id") REFERENCES "test_group_results" ("id")
);


INSERT INTO "values" ("name", "valid_from", "value_int") VALUES('version', 0, 1);
INSERT INTO "values" ("name", "valid_from") VALUES('settings', 0);
INSERT INTO "values" ("name", "parent_id", "valid_from") VALUES('defaults', 2, 0);
INSERT INTO "values" ("name", "valid_from") VALUES('tests_properties', 0);

INSERT INTO "file_store_protocols" ("name") VALUES('SFTP');
INSERT INTO "file_store_protocols" ("name") VALUES('SMB');

COMMIT;
