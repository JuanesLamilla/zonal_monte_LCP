# Monte-Carlo Least Cost Path ArcGIS Tool

## Originally Used for: Determining School Walkability for Elk Island Public Schools

ArcGIS arcpy tool used to determine school walkability by district using the monte-carlo method. 

Using Python (and ArcPy) in ArcGIS Pro, a tool was created that automatically found the safest paths for elementary students to use from their houses to their zoned school. The tool used a Monte-Carlo Simulation method and created least-cost paths in order to calculate a mean walking time for each school district. The tool also created associated maps to help with further analysis of the likely paths each student was to take.

## Why Monte Carlo?

Due to the large dataset of housing available in the school district, the numourous school zones that had to be analyzed, and the computational intensity of a least cost path analysis, attempting to create a LCP for every single home to every single school would be irrational and incredibly time consuming. Furthermore, there are technically an infinite number of starting locations. Therefore, the monte-carlo method was decided in order to maximize efficiency, minimize computation time, and still get accurate results.


## Sharing ArcPy code (without sharing the rest of the tool)

ArcGIS product tools are typically designed to stay internal to ArcGIS users, and so tools such as this one would typically be shared through a zip file in an isolated team. In an effort to share my code and experiences with other users who may need something similar, without risking sharing ESRI-owned files, I have decided to create a public repository of this ArcPy code without the rest of the tool file. That being said, creating the rest of the tool should be relatively simply as all that is needed is to format the tools parameters according to the first few lines of the ArcPy code.

## Visit my portfolio :)

The page on my portfolio for this project can be found [here](https://juaneslamilla.github.io/#portfolio/portfolio_school_walk).