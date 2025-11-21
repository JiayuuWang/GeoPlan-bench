DOMAINS=["Agriculture & Forestry", "Urban & Regional Planning", "Environmental Monitoring & Climate Change", "Disaster Emergency & Management", "Earth Science & Resource Exploration", "Marine & Water Resources", "Defense & Security"]
COMPLEXITIES=["Simple", "Medium", "Complex"]

# Domain description dictionary
DOMAIN_DESCRIPTIONS = {
    "Agriculture & Forestry": """
    • Crop type identification and area statistics
    • Crop growth monitoring and stress analysis (drought, flood, pests)
    • Yield estimation
    • Forest resource survey (species identification, volume estimation)
    • Forest fire monitoring and damage assessment
    • Deforestation and reforestation monitoring
    """,
    "Urban & Regional Planning": """
    • Urban expansion monitoring
    • Land use/land cover (LULC) classification and change analysis
    • Building extraction and 3D modeling
    • Transportation network planning (road extraction, traffic flow estimation)
    • Urban green space and water body monitoring
    • Urban heat island effect analysis
    """,
    "Environmental Monitoring & Climate Change": """
    • Water quality monitoring (eutrophication, suspended matter)
    • Air quality monitoring (aerosols, pollutants)
    • Soil erosion and desertification monitoring
    • Glacier, snow, and sea ice change monitoring
    • Carbon storage estimation and carbon cycle research
    """,
    "Disaster Emergency & Management": """
    • Flood inundation extent assessment
    • Earthquake-damaged building identification
    • Landslide and debris flow hazard investigation
    • Drought monitoring
    • Typhoon path and impact analysis
    """,
    "Earth Science & Resource Exploration": """
    • Geological structure interpretation
    • Mineral resource exploration (alteration mineral identification)
    • Oil and gas exploration (hydrocarbon seepage, surface micro-geomorphology)
    • Groundwater resource investigation
    """,
    "Marine & Water Resources": """
    • Coastline change monitoring
    • Sea surface temperature, salinity, and chlorophyll concentration retrieval
    • Maritime vessel and oil spill detection
    • Algal bloom and red tide monitoring
    • Watershed water resource assessment
    """,
    "Defense & Security": """
    • Sensitive target identification (airports, ports, missile bases)
    • Border activity monitoring
    • Battlefield situational awareness
    • Camouflage and counter-camouflage identification
    """
}

EMPTY_DAG_TEMPLATE={"domain": "empty", "nodes": ["empty"], "edges": [["empty", "empty"]], "description": "empty"}
EMPTY_TOOL_FLOW=["empty"]
EMPTY_PARAMETERIZED_TOOL_FLOW=["empty"]
DOMAIN_KEYWORDS= {
        "Agriculture & Forestry": [
            "crop", "agriculture", "forest", "vegetation", "farming", "harvest", "yield", "deforestation", "plant", "soil",
            "agricultural", "forestry", "cultivation", "irrigation", "pesticide", "fertilizer", "biomass", "photosynthesis",
            "canopy", "landsat", "ndvi", "chlorophyll", "phenology", "agroforestry", "silviculture", "timber", "logging",
            "reforestation", "afforestation", "carbon sequestration", "biodiversity", "ecosystem", "habitat", "wildlife",
            "pasture", "grassland", "rangeland", "livestock", "grazing", "drought", "precipitation", "evapotranspiration",
            "leaf area index", "lai", "gpp", "npp", "biomass estimation", "tree height", "dbh", "forest inventory"
        ],
        "Urban & Regional Planning": [
            "urban", "city", "building", "infrastructure", "development", "planning", "construction", "residential",
            "metropolitan", "suburban", "downtown", "commercial", "industrial", "zoning", "land use", "lulc", "impervious",
            "built-up", "settlement", "population", "density", "sprawl", "expansion", "growth", "transportation", "road",
            "highway", "street", "transit", "mobility", "accessibility", "pedestrian", "traffic", "congestion", "parking",
            "housing", "neighborhood", "district", "block", "parcel", "footprint", "elevation", "dem", "dsm", "3d modeling",
            "cadastral", "property", "real estate", "gentrification", "sustainability", "smart city", "green space"
        ],
        "Environmental Monitoring & Climate Change": [
            "environment", "climate", "pollution", "air quality", "water quality", "temperature", "carbon", "emission",
            "environmental", "atmospheric", "greenhouse gas", "co2", "methane", "aerosol", "particulate", "pm2.5", "pm10",
            "ozone", "nitrogen", "sulfur", "acid rain", "smog", "visibility", "turbidity", "eutrophication", "algal bloom",
            "contamination", "toxic", "heavy metal", "pesticide residue", "ph", "dissolved oxygen", "bod", "cod",
            "thermal pollution", "noise pollution", "radiation", "uv", "solar", "albedo", "reflectance", "emissivity",
            "evaporation", "humidity", "precipitation", "wind speed", "atmospheric pressure", "meteorological", "weather",
            "global warming", "climate change", "sea level rise", "ice melting", "permafrost", "desertification"
        ],
        "Disaster Emergency & Management": [
            "disaster", "emergency", "flood", "earthquake", "fire", "damage", "evacuation", "rescue", "hazard",
            "natural disaster", "catastrophe", "calamity", "crisis", "risk assessment", "vulnerability", "resilience",
            "wildfire", "forest fire", "bushfire", "burn scar", "burn severity", "seismic", "tsunami", "landslide",
            "mudslide", "avalanche", "hurricane", "typhoon", "cyclone", "tornado", "storm", "lightning", "hail",
            "drought", "famine", "volcanic", "eruption", "lava", "ash", "pyroclastic", "debris flow", "rockfall",
            "subsidence", "sinkhole", "erosion", "inundation", "surge", "breach", "levee", "dam failure", "structural damage",
            "infrastructure damage", "building collapse", "road closure", "bridge failure", "power outage", "communication"
        ],
        "Earth Science & Resource Exploration": [
            "geological", "mineral", "resource", "exploration", "mining", "oil", "gas", "groundwater", "geology",
            "geophysical", "geochemical", "petrology", "mineralogy", "stratigraphy", "tectonics", "fault", "fracture",
            "lithology", "sedimentary", "igneous", "metamorphic", "ore", "deposit", "vein", "alteration", "hydrothermal",
            "geothermal", "petroleum", "hydrocarbon", "reservoir", "basin", "anticline", "syncline", "unconformity",
            "aquifer", "water table", "hydraulic conductivity", "porosity", "permeability", "well", "borehole", "core",
            "outcrop", "exposure", "topography", "elevation", "slope", "aspect", "drainage", "watershed", "catchment",
            "lineament", "magnetic", "gravity", "electromagnetic", "seismic", "reflection", "refraction", "spectral analysis"
        ],
        "Marine & Water Resources": [
            "marine", "ocean", "water", "coastal", "sea", "maritime", "vessel", "algae", "salinity",
            "oceanographic", "hydrographic", "bathymetry", "seafloor", "seabed", "continental shelf", "abyssal", "benthic",
            "pelagic", "littoral", "estuary", "delta", "lagoon", "bay", "gulf", "strait", "channel", "reef", "coral",
            "mangrove", "wetland", "marsh", "swamp", "tide", "tidal", "current", "wave", "swell", "upwelling",
            "chlorophyll", "phytoplankton", "zooplankton", "biomass", "productivity", "eutrophication", "red tide",
            "oil spill", "pollution", "sediment", "turbidity", "suspended matter", "dissolved organic matter", "nutrients",
            "phosphate", "nitrate", "silicate", "sea surface temperature", "sst", "sea level", "altimetry", "fisheries",
            "aquaculture", "shipping", "navigation", "port", "harbor", "anchorage", "buoy", "lighthouse"
        ],
        "Defense & Security": [
            "defense", "security", "military", "surveillance", "border", "target", "threat", "reconnaissance",
            "intelligence", "strategic", "tactical", "operational", "battlefield", "combat", "warfare", "conflict",
            "base", "facility", "installation", "compound", "perimeter", "checkpoint", "patrol", "monitoring",
            "radar", "sonar", "satellite", "imagery", "aerial", "drone", "uav", "aircraft", "helicopter", "fighter",
            "bomber", "transport", "runway", "airfield", "airport", "hangar", "vehicle", "tank", "armored", "convoy",
            "missile", "rocket", "launcher", "artillery", "ammunition", "depot", "storage", "bunker", "fortification",
            "camouflage", "concealment", "detection", "identification", "tracking", "movement", "deployment", "logistics",
            "supply", "communication", "signal", "electronic", "cyber", "homeland", "counterterrorism", "peacekeeping"
        ]
    }
