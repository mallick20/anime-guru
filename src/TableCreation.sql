
-- Manga Table
CREATE TABLE manga (
    id             SERIAL PRIMARY KEY,                         
    title          VARCHAR(255) NOT NULL,                     
    main_picture   TEXT,                                      
    authors        TEXT NOT NULL,                            
    mean           DECIMAL(3,2) CHECK (mean >= 0 AND mean <= 10), 
    rank           INT CHECK (rank > 0),                      
    popularity     INT CHECK (popularity >= 0),              
    status         VARCHAR(50) NOT NULL,                     
    genres         TEXT NOT NULL,                            
    num_volumes    INT CHECK (num_volumes >= 0),             
    num_chapters   INT CHECK (num_chapters >= 0),            
    media_type     VARCHAR(50) NOT NULL,                     
    start_date     DATE,                                      
    end_date       DATE,                                      
    synopsis       TEXT                                       
);

-- Anime Table
CREATE TABLE anime (
    id            SERIAL PRIMARY KEY,                          
    title         VARCHAR(255) NOT NULL,                    
    main_picture  TEXT,                                      
    mean          DECIMAL(3,2) CHECK (mean >= 0 AND mean <= 10), 
    rank          INT CHECK (rank > 0),                     
    popularity    INT CHECK (popularity > 0),               
    status        VARCHAR(50) NOT NULL,                     
    genres        TEXT NOT NULL,                            
    num_episodes  INT CHECK (num_episodes >= 0),            
    start_date    DATE,                                     
    end_date      DATE,                                     
    synopsis      TEXT,
    agerating     VARCHAR(50),
    studios      TEXT                                      
);

-- User Table
CREATE TABLE users (
    ID SERIAL PRIMARY KEY,                          
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    UserName VARCHAR(100) NOT NULL UNIQUE,
    Email VARCHAR(255) NOT NULL,                    
    Dob DATE,
    Password VARCHAR(255),                          
    FavoriteGenres TEXT,                            
    AccountCreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastLogin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    AccountStatus VARCHAR(20) DEFAULT 'Active'
        CHECK (AccountStatus IN ('Active', 'Suspended', 'Deleted'))
);

-- Feedback Table
CREATE TABLE Feedback_Table (
    ID SERIAL PRIMARY KEY,  
    Rating INT NOT NULL CHECK (Rating BETWEEN 1 AND 10),  
    UserID INT NOT NULL REFERENCES users(ID) ON DELETE CASCADE,
    EntityType VARCHAR(20) NOT NULL CHECK (EntityType IN ('Anime', 'Manga')),
    EntityID INT NOT NULL,
    ReviewDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ModeratedStatus VARCHAR(20) DEFAULT 'Pending'
        CHECK (ModeratedStatus IN ('Approved', 'Pending', 'Rejected')),
    ReviewTitle VARCHAR(255),
    ReviewContent TEXT,
    SpoilerFlag BOOLEAN DEFAULT FALSE,
    HelpfulCount INT DEFAULT 0

);

--Activity Table
CREATE TABLE activity (
    id            SERIAL PRIMARY KEY,                         
    name          VARCHAR(255) NOT NULL,   
    description		  VARCHAR(255) NOT NULL
);

--Activity Table
CREATE TABLE entity (
    id            SERIAL PRIMARY KEY,                         
    name          VARCHAR(255) NOT NULL,   
    format		  VARCHAR(255) NOT NULL
);

--User Activity History
CREATE TABLE User_Activity_History (
    ID SERIAL PRIMARY KEY,
    UserID INT NOT NULL,
    EntityID INT,
    EntityType INT,
    ActivityType INT,
    Content TEXT,
    FOREIGN KEY (UserID) REFERENCES users(ID),
    FOREIGN KEY (EntityType) REFERENCES Entity(ID),
    FOREIGN KEY (ActivityType) REFERENCES Activity(ID)
);

ALTER TABLE user_activity_history
ADD COLUMN ActivityDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

