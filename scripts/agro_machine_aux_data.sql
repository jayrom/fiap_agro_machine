INSERT ALL
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (1, '1a', 0, 0)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (2, '1b', 800, 0)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (3, '1c', 1600, 0)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (4, '1d', 2400, 0)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (5, '1e', 3200, 0)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (6, '2a', 0, 1250)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (7, '2b', 800, 1250)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (8, '2c', 1600, 1250)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (9, '2d', 2400, 1250)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (10, '2e', 3200, 1250)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (11, '3a', 0, 2500)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (12, '3b', 800, 2500)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (13, '3c', 1600, 2500)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (14, '3d', 2400, 2500)
    INTO T_FIELDS (field_id, field_name, field_x, field_y) VALUES (15, '3e', 3200, 2500)
SELECT 1 FROM DUAL;


INSERT ALL
    INTO T_CROPS (crop_id, crop_name) VALUES (1, 'amendoim 2')
    INTO T_CROPS (crop_id, crop_name) VALUES (2, 'amendoim 1')
    INTO T_CROPS (crop_id, crop_name) VALUES (3, 'cana 12')
    INTO T_CROPS (crop_id, crop_name) VALUES (4, 'soja 322')
SELECT 1 FROM DUAL;

INSERT ALL
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (1, 3, 4, '1a', 0, 0)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (2, 3, 4, '1b', 50, 0)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (3, 3, 4, '1c', 100, 0)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (4, 3, 4, '1d', 150, 0)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (5, 3, 4, '2a', 0, 250)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (6, 3, 4, '2b', 50, 250)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (7, 3, 4, '2c', 100, 250)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (8, 3, 4, '2d', 150, 250)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (9, 3, 4, '3a', 0, 500)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (10, 3, 4, '3b', 50, 500)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (11, 3, 4, '3c', 100, 500)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (12, 3, 4, '3d', 150, 500)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (13, 3, 4, '4a', 0, 750)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (14, 3, 4, '4b', 50, 750)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (15, 3, 4, '4c', 100, 750)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (16, 3, 4, '4d', 150, 750)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (17, 3, 4, '5a', 0, 1000)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (18, 3, 4, '5b', 50, 1000)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (19, 3, 4, '5c', 100, 1000)
    INTO T_PLOTS (plot_id, field_id, crop_id, plot_name, plot_x, plot_y) VALUES (20, 3, 4, '5d', 150, 1000)
SELECT 1 FROM DUAL;

INSERT ALL
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (1, 1, 3, 'fe-00725-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (2, 1, 3, 'fe-00424-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (3, 1, 3, 'fe-03223-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (4, 1, 3, 'fe-03023-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (5, 1, 3, 'fe-01224-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (6, 1, 3, 'fe-00525-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (7, 1, 3, 'fe-00225-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (8, 1, 3, 'fe-01225-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (9, 1, 3, 'fe-01125-esp32-c-v4')
    INTO T_COMPUTERS (computer_id, plot_id, field_id, computer_name) VALUES (10, 1, 3, 'fe-00125-esp32-c-v4')
SELECT 1 FROM DUAL;

INSERT ALL
    INTO T_SENSORS (sensor_id, computer_id, sensor_name, sensor_type) VALUES (1, 7, 'fe-00122-bgt-ph1', 'bgt-ph1')
    INTO T_SENSORS (sensor_id, computer_id, sensor_name, sensor_type) VALUES (2, 7, 'fe-38124-dht22', 'temp_hum_dht22')
    INTO T_SENSORS (sensor_id, computer_id, sensor_name, sensor_type) VALUES (3, 7, 'fe-00125-rs485', 'npk ph rs485')
    INTO T_SENSORS (sensor_id, computer_id, sensor_name, sensor_type) VALUES (4, 7, 'fe-02222-rs485', 'npk ph rs485')
SELECT 1 FROM DUAL;

commit;

