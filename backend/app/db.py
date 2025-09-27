from sqlmodel import SQLModel, create_engine, Session

# database file will be created in backend folder
DATABASE_URL = "sqlite:///./outfitmaker.sqlite"

# engine = the actual database connection
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# function to initialize database tables
def init_db() -> None:
    SQLModel.metadata.create_all(engine)

# function that gives us a session for each request
def get_session():
    with Session(engine) as session:
        yield session
