import psycopg2
import psycopg2.extras

class Database:
    def __init__(self, host, port, user, password, dbname):
        self.connection = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            cursor_factory=psycopg2.extras.DictCursor
        )
        self.cursor = self.connection.cursor()

    def execute_query(self, query, params=None):
        print(f"Ejecutando consulta: {query} con parámetros: {params}")
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetch_all(self):
        return self.cursor.fetchall()

    def get_user_roles(self, username):
        query = """
        SELECT r.rolname
        FROM pg_roles r
        JOIN pg_auth_members m ON r.oid = m.roleid
        JOIN pg_user u ON m.member = u.usesysid
        WHERE u.usename = %s;
        """
        self.cursor.execute(query, (username,))
        roles = self.cursor.fetchall()
        return [role[0] for role in roles]

    def close(self):
        self.cursor.close()
        self.connection.close()
