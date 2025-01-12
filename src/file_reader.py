import struct
from shapely.geometry import Polygon
from pathlib import Path

class BinaryPolygonFileReader:
    def __init__(self, file_path):
        # Initialize with the file path and open the binary file
        self.ifs = open(file_path, 'rb')

    def __getitem__(self, idx):
        self.ifs.seek(0) 
        for _ in range(idx+1):
          set_id, first_polygon_set, second_polygon_set = self.read_next_set()
        return set_id, first_polygon_set, second_polygon_set
    
    def close(self):
        # Close the file when done
        self.ifs.close()

    def read_polygon_from_binary_file(self):
        # Using the previously defined `read_polygon_from_binary_file` function
        """
        Reads a polygon with holes (Polygon_wh equivalent) from a binary file stream.
        """
        # Read part count (number of outer polygons + holes)
        part_count = struct.unpack('Q', self.ifs.read(8))[0]  # Assuming 'size_t' is 8 bytes

        parts = []  # Store parts of the polygon, first part is outer, others are holes
        for part in range(part_count):
            # Read vertex count for each part
            vertex_count = struct.unpack('Q', self.ifs.read(8))[0]

            # Read vertices (x, y) for this polygon/part
            vertices = []
            for _ in range(vertex_count):
                x = struct.unpack('d', self.ifs.read(8))[0]
                y = struct.unpack('d', self.ifs.read(8))[0]
                vertices.append((x, y))

            # Add the polygon part (outer polygon or hole)
            parts.append(vertices)

        # The first part is the outer polygon, the rest are holes
        if len(parts) > 1:
            outer_polygon = parts[0]
            holes = parts[1:]
            polygon = Polygon(outer_polygon, holes)
        else:
            polygon = Polygon(parts[0])

        return polygon

    def read_next_set(self):
        """
        Reads the next set of polygons from the binary file.
        Returns a tuple (set_id, first_polygon_set, second_polygon_set) if successful,
        or None if end of file is reached or an error occurs.
        """
        # Check if the file is open and not at the end
        if not self.ifs:
            return None  # End of file or error

        # Read the set_id
        set_id_data = self.ifs.read(8)  # size_t is typically 8 bytes
        if not set_id_data:
            return None  # End of file
        set_id = struct.unpack('Q', set_id_data)[0]  # Unpack the size_t (unsigned long long)

        # Read the first set count
        first_set_count_data = self.ifs.read(8)
        if not first_set_count_data:
            return None  # End of file
        first_set_count = struct.unpack('Q', first_set_count_data)[0]

        # Read the first set of polygons
        first_polygon_set = []
        for _ in range(first_set_count):
            first_polygon_set.append(self.read_polygon_from_binary_file())

        # Read the second set count
        second_set_count_data = self.ifs.read(8)
        if not second_set_count_data:
            return None  # End of file
        second_set_count = struct.unpack('Q', second_set_count_data)[0]

        # Read the second set of polygons
        second_polygon_set = []
        for _ in range(second_set_count):
            second_polygon_set.append(self.read_polygon_from_binary_file())

        return set_id, first_polygon_set, second_polygon_set  # Successfully read a set
































def test_load_module():
    print("NEWww")
# #set file path
# file_path = "data/data_zentrum"
# #initialize reader
# reader = BinaryPolygonFileReader(file_path)


# set_id, polys1, polys2 = reader.read_next_set()

# print("set id: ",set_id)

# # Output the results
# print("First Set of Polygons:")
# for poly in polys1:
#     print(poly)

# print("\nSecond Set of Polygons:")
# for poly in polys2:
#     print(poly)