import arcpy
from arcpy import env
from arcpy.sa import *
import random

# Create working space and setup ArcGIS tool environment
arcpy.env.workspace = "ENTER_WORKSPACE_PATH_HERE"
arcpy.env.overwriteOutput = True

# Get parameters from ArcPy tool
boundary = arcpy.GetParameter(0) # SHP used to represent the boundaries of the school districts
roadReclassify = arcpy.GetParameter(1) # SHP of the roads (with associated speeds/costs)
schoolPoint = arcpy.GetParameter(2) # SHP of the school locations (points)
residentialPoint = arcpy.GetParameter(3) # SHP of the residential locations (points)
samplePercent = float(arcpy.GetParameter(4)) # INT of the sampling percentage desired

def main():

    # Separate the various school zones from the original shp and add the respectives paths to a list
    boundaryList = []
    rows = arcpy.GetCount_management(boundary)
    arcpy.AddMessage(str(rows[0]) + " boundaries")

    for i in range(int(rows[0])):
        polyOut ="boundary_" + str(i + 1) + ".shp"
        print("Working on " + polyOut)
        fid = "FID = " + str(i)
        arcpy.Select_analysis(boundary, polyOut, fid)
        boundaryList.append(polyOut)

    arcpy.AddMessage("initialized boundarylist")
    zoneNumber = 1  # Used to representive individual zones and create their unique LCP paths

    # Iterate through and complete the LCP analysis for each school zone
    for zone in boundaryList:
        arcpy.AddMessage("boundary: " + zone) # Inform user of current zone being processed.

        # Select the elements (residential, schools) that are completely within the zone
        schoolPoint = arcpy.management.SelectLayerByLocation(schoolPoint,
                                                            "COMPLETELY_WITHIN",
                                                            zone,
                                                            None,
                                                            "NEW_SELECTION",
                                                            "NOT_INVERT")
        residentialPoint = arcpy.management.SelectLayerByLocation(residentialPoint,
                                                                "COMPLETELY_WITHIN",
                                                                zone,
                                                                None,
                                                                "NEW_SELECTION",
                                                                "NOT_INVERT")

        # Randomly select residential locations from the shp in order to efficiently process 
        # extremely large datasets, which could theoretically be infinite (monte-carlo).
        SelectSampleByPercent(residentialPoint, samplePercent)

        # Inform user of monte-carlo selections.
        arcpy.AddMessage("Selected " + arcpy.GetCount_management(schoolPoint)[
            0] + " SchoolPoint")
        arcpy.AddMessage("Selected " + arcpy.GetCount_management(residentialPoint)[
            0] + " residentialPoints")

        # Run least cost path analysis based on monte-carlo selection for the current zone.
        arcpy.management.CopyRaster(roadReclassify, "reclass.tif")
        arcpy.intelligence.LeastCostPath("reclass.tif", residentialPoint,
                                        schoolPoint,
                                        "LCP.gdb/boundary" + str(zoneNumber) +
                                        "_best_path")
        
        zoneNumber += 1 # Move on to next zone and continue

    # Delete boundaries files that are no longer needed
    for boundary in boundaryList:
        arcpy.management.Delete(boundary)

def ConvertRoadsShpToCostRaster(roadSHP):
    """Coverts road lines shp to cost surface raster according to pretermined safety scores 
    (primarily based on vehicle speeds) for later LCP analysis.

    Ultimately this function was unused in the final school walkability analysis as the data 
    was manually cleaned and converted using pre-made tools in ArcGIS Pro, but I've left it here
    in case it's functionality is useful for another project in the future.

    Parameters:
    roadSHP (shapefile): Shapefile of the roads and paths of the community (vector lines).

    Returns:
    raster: Cost surface raster of the roads and paths.
    """
    roadRaster = arcpy.conversion.PolylineToRaster(roadSHP, "SPEED",
                                                arcpy.env.workspace + "roadRaster.tif",
                                                "MAXIMUM_LENGTH", "NONE", 5,
                                                "BUILD")

    # Get speed list from roadRaster
    speedList = []
    cursor = arcpy.SearchCursor(roadRaster)
    for row in cursor:
        speed = str(row.getValue("SPEED"))
        if speed not in speedList:
            speedList.append(speed)

    speedList = sorted(speedList)

    # Set values for reclassification
    reclass = []
    value = 2
    for speed in speedList:
        if int(speed) < 40:
            reclass.append([int(speed), value])
        elif int(speed) < 90:
            reclass.append([int(speed), value])
            value += 1

    roadReclassifyRaster = arcpy.ddd.Reclassify(arcpy.env.workspace + "roadRaster.tif","SPEED", RemapValue(reclass), 
                                          arcpy.env.workspace + "toolbox.gdb/Reclass_road1", "NODATA")
    return roadReclassifyRaster

def SelectSampleByPercent(layer, percent) -> None:
    """Select residential points by percentage at random for quicker process,

    Parameters:
    layer (int): Description of arg1
    percent (int): Percentage of points to be randomly selected

    Returns:
    None
    """
    featureCount = float(arcpy.GetCount_management(layer).getOutput(0))
    count = int(featureCount * float(percent) / float(100))

    if count == 0:
        count = 1

    oids = [oid for oid, in arcpy.da.SearchCursor(layer, "OID@")]
    oidFldName = arcpy.Describe(layer).OIDFieldName

    path = arcpy.Describe(layer).path
    delimOidFld = arcpy.AddFieldDelimiters(path, oidFldName)
    randOids = random.sample(oids, count)
    oidsStr = ", ".join(map(str, randOids))

    sql = "{0} IN ({1})".format(delimOidFld, oidsStr)
    arcpy.SelectLayerByAttribute_management(layer, "", sql)

if __name__ == '__main__':
    main()