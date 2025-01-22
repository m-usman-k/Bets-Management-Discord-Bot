import sqlite3, time

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
    
    def set_poll_inactive(self, pollid: int) -> bool:
        """
        Set a poll as inactive.
        :param pollid: The ID of the poll to set as inactive.
        :return: True if the poll was set as inactive successfully, False otherwise.
        """
        if self.poll_exists(pollid):
            self.cursor.execute('UPDATE polls SET is_active = 0 WHERE pollid = ?', (pollid,))
            self.connection.commit()
            return True
        return False

    def add_poll(self , pollid: int , question: str , first_option: str , second_option: str , expiry_time_hours: float , is_active: int):
        
        if not self.poll_exists(pollid):
            self.cursor.execute('INSERT INTO polls (pollid, question, first_option, first_joinees, second_option, second_joinees, expiry_time, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (pollid, question, first_option, "", second_option, "", expiry_time_hours, is_active))
            self.connection.commit()
            return True
        return False
    
    def get_top_users(self, limit=10):
        """
        Retrieve the top users by points.
        :param limit: Number of top users to retrieve.
        :return: A list of tuples containing user data.
        """
        self.cursor.execute('SELECT username, points FROM users ORDER BY points DESC LIMIT ?', (limit,))
        return self.cursor.fetchall()
    
    def poll_not_expired(self, pollid: int):
        if self.poll_exists(pollid=pollid):
            self.cursor.execute('SELECT expiry_time, is_active FROM polls WHERE pollid = ?', (pollid,))
            expiry_time, is_active = self.cursor.fetchone()
            if expiry_time > time.time() and is_active == 1:
                return True
            
            return False
    
    def add_user_to_poll(self, userid: int, poll_option: str, pollid: str, bet_amount: int) -> int | bool:
        if self.poll_exists(pollid=pollid):
            self.cursor.execute("""
                SELECT first_joinees, second_joinees
                FROM polls
                WHERE pollid = ?""", (pollid, ))
            
            first_joined_users, second_joined_users = self.cursor.fetchone()
            all_joinees = f"{first_joined_users},{second_joined_users}"
            all_joinees_list = all_joinees.split(",")
            all_joinees_cleaned = []
            for joinee in all_joinees_list:
                try:
                    all_joinees_cleaned.append(int(joinee.split(":")[0]) )
                except:
                    continue

            if userid in all_joinees_cleaned:
                return 2
            
            self.cursor.execute("""
                SELECT first_option, second_option, first_joinees, second_joinees
                FROM polls
                WHERE pollid = ?
            """, (pollid, ))
            
            row = self.cursor.fetchone()
            
            if not row:
                print("No matching option found.")
                return
            
            first_option, second_option, first_joinees, second_joinees = row
            
            if poll_option == first_option:
                # Update first_joinees
                new_first_joinees = f"{first_joinees},{userid}:{bet_amount}" if first_joinees else f"{userid}:{bet_amount}"
                self.cursor.execute("""
                    UPDATE polls
                    SET first_joinees = ?
                    WHERE first_option = ?
                """, (new_first_joinees, first_option))
            
            elif poll_option == second_option:
                # Update second_joinees
                new_second_joinees = f"{second_joinees},{userid}:{bet_amount}" if second_joinees else f"{userid}:{bet_amount}"
                self.cursor.execute("""
                    UPDATE polls
                    SET second_joinees = ?
                    WHERE second_option = ?
                """, (new_second_joinees, second_option))
            
            else:
                print("Option does not match either column.")
                return False
            
            self.connection.commit()
            print("User ID added successfully.")
            return True
            
        return False
    
    def get_poll_expiry_time(self, pollid: int):
        self.cursor.execute("SELECT expiry_time FROM polls WHERE id = ?", (pollid,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        
        return None
        
        
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