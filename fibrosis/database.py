import sqlite3
import os
import numpy as np
import pandas as pd
import constants
import helper
from random import shuffle
import openslide
import matplotlib
import matplotlib.pyplot as plt

from PIL import Image
class Database:
    def __init__(self, parent_dir):
        self.parent_dir = parent_dir
        self.database_path = os.path.join(parent_dir, "database.db")
        try:
            self.conn = sqlite3.connect(self.database_path)
            self.c = self.conn.cursor()
            self.c.execute("PRAGMA foreign_keys = ON") # allows cascade deletes
            self.conn.commit()
        except sqlite3.Error as error:
            print("Error while connecting to sqlite", error)
            self.conn.close()
            self.c.close()

    def __del__(self):
        # ends any connections
        self.close()
        
    def close(self):
        self.conn.commit()
        self.c.close()

        
    def initiate(self, wsi_dir, grid_dimensions):
        create_master_query = """CREATE TABLE IF NOT EXISTS master
                                (
                                tag TEXT PRIMARY KEY,
                                tile_id INTEGER,
                                pap_area INTEGER,
                                den_area INTEGER,
                                hy_area INTEGER,
                                min_area INTEGER
                                )"""
        self.c.execute(create_master_query)
        
        create_paths_query = """CREATE TABLE IF NOT EXISTS paths
                                (
                                wsi TEXT
                                )"""
        self.c.execute(create_paths_query)

        self.wsi_dir = wsi_dir
        insert_paths_query = """INSERT INTO paths (wsi) VALUES(?)"""
        self.c.execute(insert_paths_query, (self.wsi_dir,))

        # make sure constants.fib_types is safe to prevent injections
        for fib_type in constants.fib_types:
            create_table_query = f"""CREATE TABLE IF NOT EXISTS {fib_type}
                                    (
                                    rel_x INTEGER,
                                    rel_y INTEGER,
                                    tag TEXT,
                                    CONSTRAINT fk_tag
                                        FOREIGN KEY (tag)
                                        REFERENCEs master(tag)
                                        ON DELETE CASCADE
                                    )"""
            self.c.execute(create_table_query)
        
        create_grid_query = """CREATE TABLE IF NOT EXISTS tiles
                                (
                                rel_tile INTEGER PRIMARY KEY,
                                real_tile INTEGER,
                                completed INTEGER
                                )"""
        self.c.execute(create_grid_query)

        # #counts number of fib types created
        # create_count_query = """CREATE TABLE IF NOT EXISTS count 
        #                             (
        #                             papilla INTEGER,
        #                             fibrosis INTEGER,
        #                             hyalinized INTEGER,
        #                             mineralized INTEGER
        #                             )"""
        # #initializes count table to all 0's
        # initialize_count_query = """INSERT INTO count 
        #                             (papilla, fibrosis, hyalinized, mineralized)
        #                             VALUES (0, 0, 0, 0)"""
        # self.c.execute(create_count_query)
        # self.c.execute(initialize_count_query)                       
        
        
        # save total image size

        create_impacted_query = """CREATE TABLE IF NOT EXISTS impacted
                                    (
                                    tag TEXT
                                    )"""
        self.c.execute(create_impacted_query)

        create_dimension_query = """CREATE TABLE IF NOT EXISTS dimensions 
                                    (
                                    x_tiles INTEGER,
                                    y_tiles INTEGER
                                    )"""
        self.c.execute(create_dimension_query)
        
        insert_dimension_query = """INSERT INTO dimensions (x_tiles, y_tiles) VALUES(?, ?)"""
        self.c.execute(insert_dimension_query, grid_dimensions)
        
        max_tile_size = grid_dimensions[0] * grid_dimensions[1]
        randomized_tiles = [i for i in range(max_tile_size)]
        shuffle(randomized_tiles)
        
        # randomizing the grid and pushing the data in
        grids_data = [(i, randomized_tiles[i], False) for i in range(max_tile_size)]
        
        tile_data_query = """INSERT OR IGNORE INTO tiles(
                                            rel_tile,
                                            real_tile,
                                            completed
                                            ) VALUES(?, ?, ?)"""
                                           
        self.c.executemany(tile_data_query, grids_data)
        
        # paths_data_query = """INSERT OR IGNORE INTO paths(wsi) VALUES(?)"""
        # self.c.executemany(paths_data_query, [self.wsi_dir])

        self.conn.commit()
        
        # move the wsi image to the initiated folder
            # new_wsi_path = os.path.join(self.parent_dir, "wsi.svs")
            # os.rename(wsi_path, new_wsi_path)

    def get_wsi_path(self):
        pull_wsi_query = """SELECT wsi FROM paths"""
        self.c.execute(pull_wsi_query)
        wsi_path = self.c.fetchall()

        return wsi_path[0][0]

    def get_dimensions(self):
        pull_query = """SELECT * FROM dimensions"""
        self.c.execute(pull_query)
        result = self.c.fetchall()
        
        return result[0]
    
    def get_randomized_tiles(self):
        pull_query = """SELECT rel_tile,
                                real_tile
                        FROM tiles"""
        self.c.execute(pull_query)
        
        result = self.c.fetchall()
        
        return [result[i][1] for i in range(0, len(result))]
    
    def get_first_unfinished(self):
        get_unfinished_query = """SELECT rel_tile FROM tiles WHERE completed = 0 LIMIT 1"""
        self.c.execute(get_unfinished_query)
        result = self.c.fetchall()
        
        return result[0][0]
    
    def get_finished_status(self, tile_id):
        get_finished_status_query = """SELECT completed FROM tiles WHERE rel_tile = ?"""
        self.c.execute(get_finished_status_query, (tile_id, ))
        
        result = self.c.fetchall()
        
        return result[0][0]
        
    def get_max_tiles(self):
        get_max_tiles_query = """SELECT MAX(rel_tile) FROM tiles"""
        self.c.execute(get_max_tiles_query)
        result = self.c.fetchall()
        return result[0][0]

    def get_total_annotations(self):
        total_query = """SELECT COUNT(tag) FROM master"""
        self.c.execute(total_query)
        result = self.c.fetchall()
        return result[0][0]

    def add_impacted(self, tag):
        add_query = """INSERT INTO impacted (tag) VALUES(?)"""
        self.c.execute(add_query, (tag,))
        self.conn.commit()
        
    def delete_impacted(self, tag):
        delete_query = """DELETE FROM impacted WHERE tag = ?"""
        self.c.execute(delete_query, (tag,))
        self.conn.commit()
        
    def push_annotation_data(self, ann, tag, tile_id):
        for key in constants.fib_types:
            if key not in ann.keys():
                print("invalid annotation dictionary")
                return
            
        master_data = [tag, tile_id]
        for key in constants.fib_types:
            points = ann[key]
            if points == []:
                master_data.append(0)
            else:
                master_data.append(helper.calc_area(points))
            
        # print(master_data)
        master_query = """INSERT INTO master (
                            tag,
                            tile_id,
                            pap_area,
                            den_area,
                            hy_area,
                            min_area
                            ) VALUES(?, ?, ?, ?, ?, ?)"""
        self.c.execute(master_query, master_data)
        self.conn.commit()
            
        for key, points in ann.items():
            if points == []:
                continue
            
            insert_data = [(tag, points[i][0], points[i][1]) for i in range(0, len(points))]
            points_query = f"""INSERT INTO {key} (tag, rel_x, rel_y) VALUES (?, ?, ?)"""
            # count_query = f"""UPDATE count SET {key} = {key} + 1"""
            # self.c.execute(count_query)
            self.c.executemany(points_query, insert_data)
        
        self.conn.commit()
        
    def delete_annotation(self, tag):
        delete_query = """DELETE FROM master where tag = ?"""
        delete_query_2 = """DELETE FROM impacted where tag = ?"""
        self.c.execute(delete_query, (tag,))
        self.c.execute(delete_query_2, (tag,))
        self.conn.commit()

    def get_counts(self):
        try:
            count_query = """SELECT COUNT(NULLIF(pap_area,0)) as pap_count,
                        COUNT(NULLIF(den_area,0)) as den_count,
                        COUNT(NULLIF(hy_area,0)) as hy_count,
                        COUNT(NULLIF(min_area,0)) as min_count
                    FROM master
                    """
            self.c.execute(count_query)
            count = self.c.fetchall()
            count = count[0]

            impacted_query = """SELECT COUNT(NULLIF(tag,0)) as imp
                            FROM impacted"""
            self.c.execute(impacted_query)
            imp = self.c.fetchall()
            imp = imp[0][0]
            
            count = list(count)
            count.append(imp)
            count = tuple(count)

            return count
        except:
            return (0, 0, 0, 0, 0)

    def pull_impacted_tags(self):
        get_tags_query = """SELECT tag FROM impacted"""
        self.c.execute(get_tags_query)
        t = self.c.fetchall()
        tags = []
        for tup in t:
            tags.append(tup[0])
        return tags

    def pull_tile_annotations(self, tile_id):
        # create the data structure to return the points
        get_tags_query = """SELECT tag from MASTER where tile_id = ?"""
        self.c.execute(get_tags_query, (tile_id, ))
        tags = self.c.fetchall()
        tags = [tags[i][0] for i in range(len(tags))]
        
        annotations = {}
        for tag in tags:
            annotations[tag] = {}
            for fib_type in constants.fib_types:
                annotations[tag][fib_type] = []
        
        """
        { tag : {papilla:[(), (), (), ()], dense:[(), (), ()]}
        }
        """
        
        fib_type = "papilla"
        for fib_type in constants.fib_types:
            get_query = f"""SELECT master.tag,
                                    {fib_type}.rel_x,
                                    {fib_type}.rel_y
                                    FROM {fib_type}
                                    INNER JOIN master on {fib_type}.tag = master.tag
                                    WHERE master.tile_id = ?"""
            self.c.execute(get_query, (tile_id, ))
            points = self.c.fetchall()
            
            for point in points:
                cur_tag = point[0]
                x = point[1]
                y = point[2]
                annotations[cur_tag][fib_type].append((x,y))
        
        # i shouldve paid attention in data structure more pepela
        return annotations

    def update_completion(self, tile_id, completion):
        completion_query = """UPDATE tiles SET completed = ? where rel_tile = ?"""
        
        self.c.execute(completion_query, (completion, tile_id))
        self.conn.commit()
        
    def format_df(self):
        master_query = """SELECT tile_id, 
                                tiles.real_tile,
                                tiles.completed,
                                SUM(pap_area) as pap_area,
                                SUM(den_area) as den_area,
                                sum(hy_area) as hy_area,
                                sum(min_area) as min_area 
                        FROM master
                        INNER JOIN tiles on tiles.rel_tile = tile_id
                        GROUP BY tile_id, tiles.real_tile"""
        
        df = pd.read_sql_query(master_query, con=self.conn)
        
        ann_keys = constants.ann_keys
        
        df[ann_keys] = df[ann_keys].cumsum(axis=0) # get cumulative sum of all columns
        
        perc_keys = constants.perc_keys
        
        # percent of total papilla area
        df[perc_keys] = (df[["den_area", 
                             "hy_area", 
                             "min_area"]].div(df["pap_area"], axis=0).multiply(100)).round(2)
        
        ce_keys = constants.ce_keys
        df[ce_keys] = df[perc_keys].rolling(window=10, axis=0).std()
        
        for i in range(len(ce_keys)):
            df[ce_keys[i]] = df[ce_keys[i]].div(df[perc_keys[i]]) * 100
        
        return df
    
    def create_graphs(self):
        df = self.format_df()
        
        matplotlib.use("Agg") # defines backend as write only
        ann_keys = constants.ann_keys
        graph_title_keys = constants.graph_title_keys
        perc_keys = constants.perc_keys
        ce_keys = constants.ce_keys
        graph_colors = constants.graph_colors
        
        # alot of this code is formatted to make adding new plots easier
        max_plots = 2+len(perc_keys)
        fig, axs = plt.subplots(max_plots)
        fig.set_size_inches(4, 15)
        pap_area = df[ann_keys[0]]
        
        # sunburst pie chart
        try:
            pie_sizes = list(df[ann_keys].iloc[-1, 0:4])
        except:
            pie_sizes = list([0,0,0,0])

        last_pap_area = pie_sizes[0]
        delta_radius = .7
        # super impose pie charts on top of each other to make sunburst
        for i in range(len(perc_keys), -1, -1):
            cur_size = pie_sizes[i]
            axs[0].pie([cur_size, last_pap_area - cur_size], labels=[graph_title_keys[i], ""],
                         radius = .5+(.95**i)*i*delta_radius, colors=[graph_colors[i], "w"],
                        wedgeprops=dict(width=(.95**i)*delta_radius-.04), startangle=90)
        
        
        for i in range(1, 1+len(perc_keys)):
            j = i-1 # to iterate through the smaller perc_keys
            label = f"{graph_title_keys[i]} Percent Area"
            axs[i].plot(pap_area, df[perc_keys[j]], label=label, color=graph_colors[i])
            axs[i].set_title(f"{label} v Total Papilla Area")
            axs[i].set_xlabel("Total Papilla Area")
            axs[i].set_ylabel(label)
        
        last_plot= max_plots-1
        
        for i in range(len(ce_keys)):
            axs[last_plot].plot(pap_area, df[ce_keys[i]], color=graph_colors[i+1]) 
        axs[last_plot].axhline(5, color="grey", alpha=.5, dashes=(1,1))
        axs[last_plot].set_title("Moving CE v Total Papilla Area")
        axs[last_plot].set_ylabel("Moving CE Percentage")
        axs[last_plot].set_xlabel("Total Papilla Area")
        axs[last_plot].set(ylim=(0,25))
        
        lines = []
        for ax in axs:
            line, label = ax.get_legend_handles_labels()
            lines.extend(line)
            
        fig.legend(reversed(lines[:-3]), graph_title_keys, loc="upper center", ncol=4, fontsize = "x-small")
        plt.tight_layout()
        
        # convert to pil object
        # matplotlib integration with tkinter is buggy 
        fig.canvas.draw()
        return Image.frombytes("RGB", fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
    
    def check_completed(self):
        df = self.format_df()
        
        if len(df[df["completed"] == 1]) < constants.min_finished_tiles:
            return False
        
        df = df.iloc[-constants.passed_tiles_req:, :]
        
        bool_query = (df["completed"] == 1)
        
        perc_keys = constants.perc_keys
        ce_keys = constants.ce_keys
        
        valid_tiles = False
        for i in range(len(perc_keys)):
            try:
                perc = df[perc_keys[i]].iloc[-1]
            except:
                perc = 0
            
            if (perc > constants.min_perc):
                valid_tiles = True # boolean check if atleast one type of body has surpassed min perc
                bool_query = (bool_query * (df[ce_keys[i]] < constants.max_ce))

        if valid_tiles:
            num_passed_tiles = len(df[bool_query])
        else:
            num_passed_tiles = 0

        total_annotations = self.get_total_annotations()
        
        if ((total_annotations < constants.max_annotations) and not valid_tiles):
            return True

        if (num_passed_tiles == constants.passed_tiles_req):
            return True
        else:
            return False


    def export_case(self, save_path, case_name, max_tiles=None): 
        main_df = self.format_df()
        main_name = os.path.join(save_path, case_name+"-info.csv")
        main_df.to_csv(main_name)
        
        
        if max_tiles==None:
            max_tiles = self.get_dimensions()
        
        tile_count_query = """SELECT COUNT(NULLIF(pap_area,0)) as pap_count,
                                COUNT(NULLIF(den_area,0)) as den_count,
                                COUNT(NULLIF(hy_area,0)) as hy_count,
                                COUNT(NULLIF(min_area,0)) as min_count
                            FROM master
                            GROUP BY tile_id
                            """               
        impacted_count_query = """SELECT COUNT(a.tag) as imp_count
                                    FROM master AS a, impacted AS b
                                    WHERE a.tag = b.tag
                                    GROUP BY a.tile_id
                                """
                               
        count_df = pd.read_sql_query(tile_count_query, self.conn)
        imp_df = pd.read_sql_query(impacted_count_query, self.conn)
        imp_count = imp_df["imp_count"]
        count_df.insert(4, "imp_count", imp_count)
        count_name = os.path.join(save_path, case_name+"-counts.csv")
        count_df.to_csv(count_name)


        impacted_tag_query = """SELECT tag
                                FROM impacted"""
                                
        impacted_df = pd.read_sql_query(impacted_tag_query, self.conn)
        impacted_name = os.path.join(save_path, case_name+"-impacted-tags.csv")
        impacted_df.to_csv(impacted_name)

        total_count_query = """SELECT COUNT(NULLIF(pap_area,0)) as total_pap,
                                COUNT(NULLIF(den_area,0)) as total_den,
                                COUNT(NULLIF(hy_area,0)) as total_hy,
                                COUNT(NULLIF(min_area,0)) as total_min,
                                COUNT(NULLIF(den_area,0)) * 1.0 / COUNT(NULLIF(pap_area,0)) * 100 AS den_count_perc,
                                COUNT(NULLIF(hy_area,0)) * 1.0 / COUNT(NULLIF(pap_area,0)) * 100 AS hy_count_perc,
                                COUNT(NULLIF(min_area,0)) * 1.0/ COUNT(NULLIF(pap_area,0)) * 100 AS min_count_perc
                            FROM master
                            """

        total_impacted = len(self.pull_impacted_tags())
        total_pap = self.get_counts()[0]
        impacted_perc = round((total_impacted / total_pap) * 100, constants.perc_digits)

        count_df = pd.read_sql_query(total_count_query, self.conn)
        count_df.insert(4, "total_imp", total_impacted)
        count_df.insert(8, "imp_count_perc", impacted_perc)
        count_name = os.path.join(save_path, case_name+"-count-percentages.csv")
        count_df.to_csv(count_name)
        
        for fib_type in constants.fib_types:
            points_query = f"""SELECT {fib_type}.*,
                                master.tile_id,
                                tiles.real_tile
                                FROM {fib_type}
                                INNER JOIN master on master.tag = {fib_type}.tag
                                INNER JOIN tiles on tiles.rel_tile = master.tile_id
                                """
                                
            pt_df = pd.read_sql_query(points_query, self.conn)
            # account of padding of the image in tkinter
            pt_df["real_x"] = (pt_df["rel_x"] * constants.zoom_multiplier) - constants.padding_size
            pt_df["real_y"] = (pt_df["rel_y"] * constants.zoom_multiplier) - constants.padding_size
            
            # convert to overall coordinates
            pt_df["real_x"] = pt_df["real_x"] + ((pt_df["real_tile"] % max_tiles[0])*constants.tile_size)
            pt_df["real_y"] = pt_df["real_y"] + ((pt_df["real_tile"] // max_tiles[0])*constants.tile_size)

            pt_df["rel_x"] = pt_df["rel_x"] - (constants.padding_size // constants.zoom_multiplier) #set rel coords 0,0 to top left of tile
            pt_df["rel_y"] = pt_df["rel_y"] - (constants.padding_size // constants.zoom_multiplier)
            
            points_name = os.path.join(save_path, case_name+f"-{fib_type}-pts.csv")
            pt_df.to_csv(points_name)

if __name__ == "__main__":
    test = Database("test_fibrosis/database.db")
    test.initiate(r"C:\Users\shahr\Desktop\MonukiCode\monuki-fibrosis\test-fibrosis\wsi.svs", (31,31))
    # print(test.get_randomized_tiles())
    # print(test.format_df())
    # print(test.pull_tile_annotations(83))
    # test.export_case((31,31))
    test.create_graphs()
    test.close()