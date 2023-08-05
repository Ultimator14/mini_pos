class Config:
    TESTING = False
    DEBUG = False
    CONFIG_FILE = "config.json"
    DATABASE_FILE = "data.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_FILE}"
