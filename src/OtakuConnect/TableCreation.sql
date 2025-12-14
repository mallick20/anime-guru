
-- Manga Table
CREATE TABLE manga (
    id             SERIAL PRIMARY KEY,                         
    title          VARCHAR(255) NOT NULL,                     
    main_picture   TEXT,                                      
    authors        TEXT,                            
    mean           DECIMAL(3,2) CHECK (mean >= 0 AND mean <= 10), 
    rank           INT CHECK (rank > 0),                      
    popularity     INT CHECK (popularity >= 0),              
    status         VARCHAR(50) NOT NULL,                     
    genres         TEXT,                            
    num_volumes    INT CHECK (num_volumes >= 0),             
    num_chapters   INT CHECK (num_chapters >= 0),            
    media_type     VARCHAR(50),                     
    start_date     DATE,                                      
    end_date       DATE,                                      
    synopsis       TEXT                                       
);

-- Anime Table
CREATE TABLE anime (
    id            INT PRIMARY KEY,                          
    title         VARCHAR(255) NOT NULL,                    
    main_picture  TEXT,                                      
    mean          DECIMAL(3,2) CHECK (mean >= 0 AND mean <= 10), 
    rank          INT CHECK (rank > 0),                     
    popularity    INT CHECK (popularity > 0),               
    status        VARCHAR(50) NOT NULL,                     
    genres        TEXT,                            
    num_episodes  INT CHECK (num_episodes >= 0),            
    start_date    DATE,                                     
    end_date      DATE,                                     
    synopsis      TEXT                                      
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
    RoleId VARCHAR(50) DEFAULT '1',
    FavoriteGenres TEXT, 
    Avatar_Path TEXT NOT NULL,                           
    AccountCreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastLogin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    AccountStatus VARCHAR(20) DEFAULT 'Active'
    CONSTRAINT users_accountstatus_check
    CHECK (AccountStatus IN ('Active', 'Inactive'))
);


-- Feedback Table
CREATE TABLE Feedback_Table (
    ID SERIAL PRIMARY KEY,  
    Rating INT NOT NULL CHECK (Rating BETWEEN 1 AND 10),  
    UserID INT NOT NULL,
    EntityType VARCHAR(20) NOT NULL CHECK (EntityType IN ('Anime', 'Manga')),
    EntityID INT NOT NULL,
    ReviewDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ModeratedStatus VARCHAR(20) DEFAULT 'Pending'
        CHECK (ModeratedStatus IN ('Approved', 'Pending', 'Rejected')),
    ReviewTitle VARCHAR(255),
    ReviewContent TEXT,
    SpoilerFlag BOOLEAN DEFAULT FALSE,
    HelpfulCount INT DEFAULT 0,
    CONSTRAINT feedback_table_userid_fkey FOREIGN KEY (UserID) REFERENCES users(ID) ON DELETE CASCADE
);

--Activity Table
CREATE TABLE activity (
    id            SERIAL PRIMARY KEY,                         
    name          VARCHAR(255) NOT NULL,   
    description		  VARCHAR(255) NOT NULL
);

# Activity Table Insert data
INSERT INTO activity (name, description) VALUES
('Viewed', 'User viewed an entity'),
('Rated', 'User rated an entity'),
('Commented', 'User left a comment'),
('Recommended', 'User received a recommendation');

--Entity Table
CREATE TABLE entity (
    id            SERIAL PRIMARY KEY,                         
    name          VARCHAR(255) NOT NULL,   
    format		  VARCHAR(255) NOT NULL
);

# Insert data into entity table
INSERT INTO entity (name, format) VALUES
('Anime', 'Anime entity type'),
('Manga', 'Manga entity type');

-- Discussion threads tables
CREATE Table discussion_threads(
    id SERIAL NOT NULL,
    userid INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id),
    CONSTRAINT user_discussion_threads_userid_fkey FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE discussion_replies(
    id SERIAL NOT NULL,
    threadid INTEGER NOT NULL,
    userid INTEGER NOT NULL,
    reply TEXT,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT user_discussion_replies_threadid_fkey FOREIGN KEY (threadid) REFERENCES discussion_threads(id) ON DELETE CASCADE,
    CONSTRAINT user_discussion_replies_userid_fkey FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE
);

-- User Activity History
CREATE TABLE user_activity_history(
    id SERIAL NOT NULL,
    userid integer NOT NULL,
    entityid integer,
    entitytype integer,
    activitytype integer,
    content text,
    activitydate timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id),
    CONSTRAINT user_activity_history_userid_fkey FOREIGN key(userid) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT user_activity_history_entitytype_fkey FOREIGN key(entitytype) REFERENCES entity(id),
    CONSTRAINT user_activity_history_activitytype_fkey FOREIGN key(activitytype) REFERENCES activity(id)
);