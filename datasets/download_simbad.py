from astroquery.simbad import Simbad

print("Downloading Simbad star catalog...")

# New TAP query syntax (replaces deprecated query_criteria)
query = """
SELECT TOP 3000
    basic.main_id,
    basic.ra,
    basic.dec,
    basic.sp_type,
    plx.plx AS parallax,
    allfluxes.V,
    allfluxes.B
FROM basic
JOIN plx ON basic.oid = plx.oidref
JOIN allfluxes ON basic.oid = allfluxes.oidref
WHERE plx.plx > 10
AND basic.sp_type IS NOT NULL
AND allfluxes.V IS NOT NULL
"""

try:
    result = Simbad.query_tap(query)
    if result and len(result) > 0:
        result.write('datasets/nearby_stars.csv', format='csv', overwrite=True)
        print(f"Downloaded {len(result)} stars successfully!")
        print("First few rows:")
        print(result[:3])
    else:
        print("No results returned")
except Exception as e:
    print(f"Error: {e}")
    print("Trying simpler fallback query...")

    simple_query = """
    SELECT TOP 3000
        main_id, ra, dec, sp_type
    FROM basic
    WHERE sp_type IS NOT NULL
    AND sp_type LIKE 'M%'
    """
    try:
        result = Simbad.query_tap(simple_query)
        result.write('datasets/nearby_stars.csv', format='csv', overwrite=True)
        print(f"Downloaded {len(result)} stars with fallback query!")
    except Exception as e2:
        print(f"Fallback also failed: {e2}")
