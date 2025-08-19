echo "Display Important Values from the table fuel_readings"
psql -c "select id, total_mileage, mpg, lat,lng,location from fuel_readings order by id desc limit 10"

