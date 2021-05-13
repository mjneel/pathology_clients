import sqlite3
import os
import csv
class Database:
    def __init__(self, parent_dir):
        self.parent_dir = parent_dir
        self.database_path = os.path.join(parent_dir, "database.db")
        try:
            self.conn = sqlite3.connect(self.database_path)
            self.c = self.conn.cursor()
            
        except sqlite3.Error as error:
            print("Error while connecting to sqlite", error)
            self.conn.close()
            self.c.close()

    def close(self):
        self.conn.commit()
        self.c.close()
        self.conn.close()
    
    def initiate(self, array_path):
        create_table_query = '''CREATE TABLE IF NOT EXISTS annotations (IDX INTEGER PRIMARY KEY,
                                                                        BODY_TYPE TEXT NOT NULL,
                                                                        GR INTEGER NOT NULL,
                                                                        MAF INTEGER NOT NULL,
                                                                        MP INTEGER NOT NULL)'''
                                                                        
        self.c.execute(create_table_query)
        
        new_array_path = os.path.join(self.parent_dir, "body_array.npy")
        print(new_array_path)
        os.rename(array_path, new_array_path)
        
        self.close()
        
    def add_change_annotation(self, data_values):
        # data_values = (id, body_type, GR, MAF, MP)
        
        insert_replace_query = '''REPLACE INTO annotations (IDX,
                                  BODY_TYPE,
                                  GR,
                                  MAF,
                                  MP)
                                  values (?, ?, ?, ?, ?)'''
                                  
        self.c.execute(insert_replace_query, data_values)
        self.close()
        
    def get_annotation(self, id):
        select_query = '''SELECT * FROM annotations WHERE IDX = ?'''
        
        self.c.execute(select_query, (id, ))
        annotations = self.c.fetchone()
        self.close()
        return annotations
    
    def get_starting_row(self, array_length):
        get_query = '''SELECT IDX FROM annotations WHERE IDX = (SELECT MAX(IDX) FROM annotations)'''
        self.c.execute(get_query)
        result = self.c.fetchone()
        
        print(result)
        if result == None:
            result = 0
        elif result[0] >= array_length:
            result = array_length - 1
        else:
            result = result[0] + 1 # start at the first uncompleted body
            
        self.close()
        
        return result
        
    def export(self, destination_path):
        all_files_query = '''SELECT * FROM annotations'''
        
        self.c.execute(all_files_query)
        
        data = self.c.fetchall()
        
        with open(destination_path, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([i[0] for i in self.c.description])
            csv_writer.writerows(data)