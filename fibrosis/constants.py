tile_size = 4096
tile_width = 2
padding_size = 1200
exclusion_line_width = 5

downscale_level = 1 #10x (0 is 40x, 1 is 10x, and 2 is 2.5x)
zoom_multiplier = 4

annotation_color = 'limegreen'
end_color = "yellow"
axis_color = "red"
annotation_hover_color = "red"
impacted_color = "pink"

fib_types = ["papilla", "dense", "hyalinized", "mineralized"]

fib_colors = { "papilla": "green",
                "dense": "#1f66b4",
                "hyalinized": "orange",
                "mineralized": "magenta"
}

ann_keys = ["pap_area", "den_area", "hy_area", "min_area"]
graph_title_keys = ["Papilla", "Dense", "Hyalinized", "Mineralized"]
graph_colors = list(fib_colors.values())
perc_keys = ["den_area %", "hy_area %", "min_area %"]
ce_keys = [f"ce {i}" for i in perc_keys]

max_pupilla_area = 27000 #(108,000 for 40x)
perc_digits = 2

# completion values
min_finished_tiles = 20
max_annotations = 1500
min_perc = 1
max_ce = 5
passed_tiles_req = 10

# subtract 1200 from coords, 26 - 27 check excess fucks up modulus x coordinate

#set rel x and y to top left of tile
