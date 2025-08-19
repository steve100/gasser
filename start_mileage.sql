insert into fuel_readings (id,total_mileage) values (1,274363);

select * from fuel_readings order by id desc limit 2;

update fuel_readings set mpg = 20.2  where id=2;

ALTER TABLE fuel_readings ADD COLUMN lat  DOUBLE PRECISION  lng  DOUBLE PRECISION


