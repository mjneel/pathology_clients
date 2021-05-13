tile_size = 4096
padding_size = 600

annotation_color = 'limegreen'
end_color = "yellow"
axis_color = "red"
annotation_hover_color = "red"

fib_types = ["pupilla", "fibrosis", "hyalinized", "mineralized"]
fib_colors = { "pupilla": "green",
                "fibrosis": "#1f66b4",
                "hyalinized": "orange",
                "mineralized": "purple"
    
}

ann_keys = ["pup_area", "fib_area", "hy_area", "min_area"]
graph_title_keys = ["Pupilla", "Fibrosis", "Hyalinized", "Mineralized"]
graph_colors = list(fib_colors.values())
perc_keys = ["fib_area %", "hy_area %", "min_area %"]
ce_keys = [f"ce {i}" for i in perc_keys]

# completion values
min_finished_tiles = 20
max_annotations = 3500
min_perc = 2
max_ce = 5
passed_tiles_req = 10