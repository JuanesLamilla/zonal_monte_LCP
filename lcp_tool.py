import arcpy
from arcpy import env
from arcpy.sa import *
import random

# Create working space
arcpy.env.workspace = "ENTER_WORKSPACE_PATH_HERE"
arcpy.env.overwriteOutput = True

# Get parameters from ArcPy tool
boundary = arcpy.GetParameter(0) # SHP used to represent the boundaries of the school districts
roadReclassify = arcpy.GetParameter(1) # SHP of the roads (with associated speeds/costs)
schoolPoint = arcpy.GetParameter(2) # SHP of the school locations (points)
residentialPoint = arcpy.GetParameter(3) # SHP of the residential locations (points)
samplePercent = float(arcpy.GetParameter(4)) # INT of the sampling percentage desired

def main():
    # combinedShp = str(arcpy.GetParameter(4))

    # Separate the zone from one shapefile to multiple file and add the path to list
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
    c = 1  # represent number of zone
    for zone in boundaryList:
        arcpy.AddMessage("boundary: " + zone)
        # Select the elements that completely within the zone
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

        """Random select residential,change the second varialbe to make different
        percentage
        """
        SelectSampleByPercent(residentialPoint, samplePercent)

        """Send message to let user know how may sample selected

        """
        arcpy.AddMessage("Selected " + arcpy.GetCount_management(schoolPoint)[
            0] + " SchoolPoint")
        arcpy.AddMessage("Selected " + arcpy.GetCount_management(residentialPoint)[
            0] + " residentialPoints")

        # Make a string to reclassify
        arcpy.management.CopyRaster(roadReclassify, "reclass.tif")
        arcpy.intelligence.LeastCostPath("reclass.tif", residentialPoint,
                                        schoolPoint,
                                        "LCP.gdb/boundary" + str(c) +
                                        "_best_path")
        c += 1

    # Delete the boundaries file that are not needed
    for boundary in boundaryList:
        arcpy.management.Delete(boundary)

def ConvertRoadsShapefileToCostRaster(roadSHP):
    """Convert to raster for reclassify if the input is shapefile instead of raster directly.

    Parameters:
    roadSHP (shapefile): Description of arg1

    Returns:
    raster
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

    # Set value for reclassify
    reclass = []
    value = 2
    for speed in speedList:
        if int(speed) < 40:
            reclass.append([int(speed), value])
        elif int(speed) < 90:
            reclass.append([int(speed), value])
            value += 1

    roadReclassify = arcpy.ddd.Reclassify(arcpy.env.workspace + "roadRaster.tif","SPEED", RemapValue(reclass), 
                                          arcpy.env.workspace + "toolbox.gdb/Reclass_road1", "NODATA")
    return roadReclassify

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