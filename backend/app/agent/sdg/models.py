import enum


class SdgProgressEnum(str, enum.Enum):
    LOADING_FILE = "Loading File"
    PREPARING_DOCUMENTS = "Preparing Documents"
    BUILDING_KNOWLEDGE_GRAPH = "Building Knowledge Graph"
    GENERATING_TESTSET = "Generating Testset"
    STORING_GOLDENS = "Storing Goldens"
    DONE = "Done"
