class Config:
    TESTING = False
    DEBUG = False
    CONFIG_FILE = "config.json"
    DATABASE_FILE = "data.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_FILE}"

class TestConfig:
    TESTING = True
    DEBUG = True
    CONFIG_FILE = "config.json"
    DATABASE_FILE = "nonexistent.db"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
