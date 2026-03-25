-- 1 ЗАПРОС ---------------
SELECT 
	c.brand, 
	c.model, 
	c.number, 
	cl.name AS class, 
	COUNT(*), 
	SUM(d.amount) AS profit,
	COALESCE(SUM(vs.total_cost) FILTER (WHERE vs.begin_date >= CURRENT_DATE - INTERVAL '3 months'), 0) AS expenses,
	SUM(d.amount) - COALESCE(SUM(vs.total_cost) FILTER (WHERE vs.begin_date > '2026-01-01'), 0) AS net_profit,
	MAX(b.type) AS popular_pricing,
	last_booking.begin_time AS last_booking_date,
    last_booking.duration AS last_booking_duration
FROM car c
JOIN booking b ON c.car_id = b.car_id
JOIN car_class cl ON c.class_id = cl.car_class_id
LEFT JOIN debiting d ON d.booking_id = b.booking_id
LEFT JOIN visit_sc vs ON vs.car_id = c.car_id
LEFT JOIN (
    SELECT DISTINCT ON (car_id)
        car_id,
        begin_time,
        end_time - begin_time AS duration
    FROM booking
    ORDER BY car_id, begin_time DESC
) last_booking ON last_booking.car_id = c.car_id
WHERE b.begin_time > '2026-01-01'
GROUP BY c.brand, c.model, c.number, cl.name, last_booking.begin_time, last_booking.duration
ORDER BY COUNT(*);
-------------------------------------------------


-- 2 ЗАПРОС ---------------------
WITH fines_count AS (
	SELECT
		renter_id,
		COUNT(*) AS fines_total,
		COUNT(*) - COUNT(payment_time) AS not_paid,
		SUM(amount) AS cost
	FROM fine
	GROUP BY renter_id
),
mad_month AS (
	SELECT
		DATE_TRUNC('month', receiving_time) AS month
	FROM fine
	GROUP BY DATE_TRUNC('month', receiving_time)
	ORDER BY COUNT(*) DESC
	LIMIT 1
),
avg_amount_table AS (
	SELECT
		ROUND(AVG(amount), 2) AS avg_amount
	FROM fine f
	WHERE DATE_TRUNC('month', f.receiving_time) = (SELECT month FROM mad_month)
	AND cause = 'Illegal parking'
)
SELECT 
--r.renter_id,
r.full_name,
r.phone,
fc.fines_total,
fc.cost,
fc.not_paid,
--f.cause, 
--COUNT(*) AS illegal_parking_count,
(SELECT avg_amount FROM avg_amount_table) AS avg_cost_for_illigal_parking_within_mad_month
FROM fine f
JOIN renter r ON r.renter_id = f.renter_id
JOIN fines_count fc ON fc.renter_id = f.renter_id
WHERE receiving_time >= CURRENT_DATE - INTERVAL '1 year'
AND cause = 'Illegal parking'
GROUP BY r.renter_id, fc.fines_total, fc.cost, fc.not_paid
HAVING COUNT(*) >= 13
ORDER BY cost DESC;
---------------------------------


-- 3 ЗАПРОС ------------
CREATE EXTENSION postgis;

WITH calculated AS (
	SELECT DISTINCT ON (r.full_name, c.number)
	    r.full_name,
	    c.number,
	    ST_Distance(
	        ST_MakePoint(g.coords[0], g.coords[1])::geography,
	        ST_MakePoint(p.coords[0], p.coords[1])::geography
	    ) / 1000 AS min_distance_km,
	    g.coords AS gps_coords,
	    p.coords AS parking_coords
	FROM booking b
	JOIN renter r ON b.renter_id = r.renter_id
	JOIN car c ON c.car_id = b.car_id
	JOIN gps g ON g.booking_id = b.booking_id
	CROSS JOIN parking p
	WHERE end_time IS null
	ORDER BY r.full_name, c.number, min_distance_km
)
SELECT 
*
FROM calculated
WHERE min_distance_km = (SELECT MAX(min_distance_km) FROM calculated);
----------------------


-- 4 ЗАПРОС --------------
SELECT
	TO_CHAR(begin_time, 'Dy') AS day,
	COALESCE(SUM(d.amount), 0) AS profit,
	COUNT(DISTINCT b.booking_id) AS order_count,  -- удаляем дубликаты, образовавшиеся из-за join booking с debiting
	COUNT(DISTINCT (DATE_TRUNC('day', b.begin_time))) AS days_count,  -- ok
	ROUND(COUNT(DISTINCT b.booking_id) * 1.0 / COUNT(DISTINCT (DATE_TRUNC('day', b.begin_time))), 2) AS average_count,
	ROUND(COUNT(DISTINCT b.booking_id) * 100.0 / (SELECT COUNT(*) FROM booking), 2) AS percentage
FROM booking b
LEFT JOIN debiting d ON b.booking_id = d.booking_id  -- left, чтобы не пропали поездки без записи об оплате
GROUP BY TO_CHAR(begin_time, 'Dy'), EXTRACT(ISODOW FROM b.begin_time)
ORDER BY EXTRACT(ISODOW FROM b.begin_time);
---------------------



-- 5 ЗАПРОС ----------------------
WITH 
calc1 AS ( -- для парковки получем сколько всего раз на ней парковались и когда в последний раз
	SELECT 
		parking_id,
		COUNT(*) as total_count,
		MAX(end_time) AS last_car_parking
	FROM car_parking
	GROUP BY parking_id
),
calc2 AS ( -- для парковки получаем сколько раз на ней парковалась каждая машина
	SELECT 
		parking_id,
		car_id,
	COUNT(*) AS times
	FROM car_parking
	GROUP BY parking_id, car_id
)
SELECT DISTINCT ON (parking_id) -- для каждой парковки выбираем машину, которая чаще всего на ней парковалась
	calc2.parking_id,
	calc1.total_count AS parking_total_count,
	calc1.last_car_parking,
	--calc2.car_id AS most_frequent_car,
	c.number AS most_frequent_car_number,
	calc2.times
FROM calc2
JOIN car c ON c.car_id = calc2.car_id
JOIN calc1 ON calc1.parking_id = calc2.parking_id
ORDER BY parking_id, calc2.times DESC;
--------




