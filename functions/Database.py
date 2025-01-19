import sqlite3

class Database:
    def __init__(self, db_name):
        """
        Initialize the Database class, connect to the database, and create the users table if it doesn't exist.
        :param db_name: Name of the SQLite database file.
        """
        self.db_name = db_name
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()
        self.create_users_table()
        self.create_polls_table()

    def create_users_table(self):
        """
        Create the 'users' table if it does not exist.
        """
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userid INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            points INTEGER DEFAULT 0
        )
        ''')
        self.connection.commit()
        
    def create_polls_table(self):
        """
        Create the 'polls' table if it does not exist.
        """
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS polls (
            pollid INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            first_option TEXT NOT NULL,
            first_joinees TEXT,
            second_option TEXT NOT NULL,
            second_joinees TEXT,
            expiry_time INTEGER NOT NULL,
            is_active INTEGER NOT NULL
        )
        ''')
        self.connection.commit()
        
    def poll_exists(self, pollid):
        """
        Check if a user exists in the database.
        :param pollid: The ID of the poll to check.
        :return: True if the poll exists, False otherwise.
        """
        self.cursor.execute('SELECT 1 FROM polls WHERE pollid = ?', (pollid,))
        return self.cursor.fetchone() is not None
    
    def add_poll(self , pollid: int , question: str , first_option: str , second_option: str , first_joinees: str , second_joinees: str , expiry_time_hours: float , is_active: int):
        
        if not self.user_exists(pollid):
            self.cursor.execute('INSERT INTO users (userid, username) VALUES (?, ?)', (userid, username))
            self.connection.commit()
            return True
        return False
        
        
    def user_exists(self, userid):
        """
        Check if a user exists in the database.
        :param userid: The ID of the user to check.
        :return: True if the user exists, False otherwise.
        """
        self.cursor.execute('SELECT 1 FROM users WHERE userid = ?', (userid,))
        return self.cursor.fetchone() is not None

    def add_user(self, userid, username):
        """
        Add a new user to the database.
        :param userid: The ID of the new user.
        :param username: The username of the new user.
        :return: True if the user was added successfully, False otherwise.
        """
        if not self.user_exists(userid):
            self.cursor.execute('INSERT INTO users (userid, username) VALUES (?, ?)', (userid, username))
            self.connection.commit()
            return True
        return False

    def add_points(self, userid, points):
        """
        Add points to a user's wallet.
        :param userid: The ID of the user.
        :param points: The number of points to add.
        """
        if self.user_exists(userid):
            self.cursor.execute('UPDATE users SET points = points + ? WHERE userid = ?', (points, userid))
            self.connection.commit()

    def remove_points(self, userid, points):
        """
        Remove points from a user's wallet.
        :param userid: The ID of the user.
        :param points: The number of points to remove.
        :return: True if the points were removed successfully, False if insufficient points.
        """
        if self.user_exists(userid):
            self.cursor.execute('SELECT points FROM users WHERE userid = ?', (userid,))
            current_points = self.cursor.fetchone()[0]
            if current_points >= points:
                self.cursor.execute('UPDATE users SET points = points - ? WHERE userid = ?', (points, userid))
                self.connection.commit()
                return True
        return False

    def get_user_points(self, userid):
        """
        Get the current points of a user.
        :param userid: The ID of the user.
        :return: The number of points the user has, or None if the user does not exist.
        """
        if self.user_exists(userid):
            self.cursor.execute('SELECT points FROM users WHERE userid = ?', (userid,))
            return self.cursor.fetchone()[0]
        return None

    def get_all_users(self):
        """
        Retrieve all users from the database.
        :return: A list of tuples containing user data.
        """
        self.cursor.execute('SELECT * FROM users')
        return self.cursor.fetchall()

    def delete_user(self, userid):
        """
        Delete a user from the database.
        :param userid: The ID of the user to delete.
        """
        if self.user_exists(userid):
            self.cursor.execute('DELETE FROM users WHERE userid = ?', (userid,))
            self.connection.commit()

    def close_connection(self):
        """
        Close the database connection.
        """
        self.connection.close()