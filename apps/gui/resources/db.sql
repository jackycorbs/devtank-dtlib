BEGIN TRANSACTION;

CREATE TABLE "example_devs" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"uid"	VARCHAR(255),
	"serial_number"	VARCHAR(255)
);

CREATE TABLE "example_dev_test_results" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"example_dev_id"	INTEGER NOT NULL,
	"group_entry_id"	INTEGER,
	"pass_fail"	INTEGER NOT NULL,
	"output_file_id"	INTEGER,
	"log_file_id"	INTEGER,
	"group_result_id" INTEGER NOT NULL,
	"duration" INTEGER,
	FOREIGN KEY("example_dev_id") REFERENCES "example_devs" ("id"),
	FOREIGN KEY("group_entry_id") REFERENCES "test_group_entries" ("id"),
	FOREIGN KEY("output_file_id") REFERENCES "files" ("id"),
	FOREIGN KEY("log_file_id") REFERENCES "files" ("id"),
	FOREIGN KEY("group_result_id") REFERENCES "test_group_results" ("id")
);

CREATE TABLE "example_dev_test_results_values" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"test_result_id"	INTEGER NOT NULL,
	"value_id"	INTEGER NOT NULL,
	FOREIGN KEY("test_result_id") REFERENCES "example_dev_test_results" ("id"),
	FOREIGN KEY("value_id") REFERENCES "values" ("id")
);

INSERT INTO "values" ("name", "parent_id", "valid_from", "value_text") VALUES('dev_table',                2, 0, "example_devs");
INSERT INTO "values" ("name", "parent_id", "valid_from", "value_text") VALUES('dev_results_table',        2, 0, "example_dev_test_results");
INSERT INTO "values" ("name", "parent_id", "valid_from", "value_text") VALUES('dev_results_table_key',    2, 0, "example_dev_id");
INSERT INTO "values" ("name", "parent_id", "valid_from", "value_text") VALUES('dev_results_values_table', 2, 0, "example_dev_test_results_values");

COMMIT;
